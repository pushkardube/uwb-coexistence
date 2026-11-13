#!/usr/bin/env python3
"""Collect checked UWB distance/RSSI over BLE NUS, with no serial port needed."""
import argparse
import asyncio
import csv
import datetime
import json
from pathlib import Path
import re
import time

NUS_TX = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
NUS_RX = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
FIELDS = ['host_time_utc','device','connection','seq','peer','cycle','level','octet',
          'tx_power_hex','dist_mm','final_rssi_mdB','rssi_dgc_mdB','diag','C','N','D',
          'error','status','ok','peer_ok','level_ok']


class LineSink:
    """Notifications are arbitrary byte fragments, not complete UART records."""
    def __init__(self, directory, quiet=False):
        self.log = (directory / 'init.log').open('w')
        self.file = (directory / 'measurements.csv').open('w', newline='')
        self.csv = csv.DictWriter(self.file, fieldnames=FIELDS)
        self.csv.writeheader()
        self.buffer = bytearray()
        self.discarding = False
        self.quiet = quiet
        self.last_seq = None
        self.metrics = dict(notifications=0, bytes=0, lines=0, measurements=0,
                            sequence_gaps=0, duplicates=0, out_of_order=0,
                            framing_errors=0, discarded_partial_bytes=0,
                            maximum_reported_queue_drops=0, transport_replays=0)
        self.pending_record = None
        self.last_record = None

    def reset_stream(self):
        self.metrics['discarded_partial_bytes'] += len(self.buffer)
        self.buffer.clear()
        self.discarding = False
        self.pending_record = None

    def feed(self, data, device='', connection=0):
        acknowledgements = []
        self.metrics['notifications'] += 1
        self.metrics['bytes'] += len(data)
        self.buffer.extend(data)
        while b'\n' in self.buffer:
            raw, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            if self.discarding:
                self.discarding = False
                continue
            if len(raw) > 1024:
                self.metrics['framing_errors'] += 1
                continue
            try:
                line = raw.rstrip(b'\r').decode('utf-8')
            except UnicodeDecodeError:
                self.metrics['framing_errors'] += 1
                continue
            envelope = re.fullmatch(r'BLE_RECORD boot=([0-9a-fA-F]{8}) id=(\d+)', line)
            if envelope:
                self.pending_record = (envelope[1].lower(), int(envelope[2]))
                continue
            if self.pending_record is not None:
                token = self.pending_record
                self.pending_record = None
                acknowledgements.append(token)
                if token == self.last_record:
                    self.metrics['transport_replays'] += 1
                    continue
                self.last_record = token
            self.line(line, device, connection)
        if len(self.buffer) > 1024:
            self.metrics['framing_errors'] += 1
            self.buffer.clear()
            self.discarding = True
        return acknowledgements

    def line(self, line, device, connection):
        self.metrics['lines'] += 1
        self.log.write(line + '\n')
        self.log.flush()
        if not self.quiet:
            print(line, flush=True)
        if line.startswith('COMBINED ready:'):
            self.last_seq = None
        tokens = dict(re.findall(r'(\w+)=([^\s]+)', line))
        if line.startswith('BLE_STATUS '):
            self.metrics['maximum_reported_queue_drops'] = max(
                self.metrics['maximum_reported_queue_drops'], int(tokens.get('dropped', 0)))
        if not line.startswith('COMBINED seq='):
            return
        row = {key: tokens[key] for key in FIELDS if key in tokens}
        row.update(host_time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   device=device, connection=connection)
        if 'octet' in tokens:
            row['tx_power_hex'] = f"0x{int(tokens['octet'],16)*0x01010101:08X}"
        seq = int(tokens['seq'])
        if self.last_seq is not None:
            difference = (seq - self.last_seq) & 0xffffffff
            if difference == 0:
                self.metrics['duplicates'] += 1
            elif 1 < difference < 0x80000000:
                self.metrics['sequence_gaps'] += difference - 1
            elif difference >= 0x80000000:
                self.metrics['out_of_order'] += 1
        self.last_seq = seq
        self.metrics['measurements'] += 1
        self.csv.writerow(row)
        self.file.flush()

    def close(self):
        self.reset_stream()
        self.log.close()
        self.file.close()


async def collect(args, sink, record):
    from bleak import BleakClient, BleakScanner
    if args.address:
        device = await BleakScanner.find_device_by_address(args.address, timeout=args.scan_seconds)
        if device is None:
            raise RuntimeError(f'BLE device {args.address} not found; check power and advertising.')
    else:
        found = await BleakScanner.discover(timeout=args.scan_seconds)
        matches = [d for d in found if d.name and d.name.startswith(args.name)]
        if len(matches) != 1:
            raise RuntimeError(f'Found {len(matches)} matching BLE devices; use --address to select one. '
                               f'Matches: {[(d.name,d.address) for d in matches]}')
        device = matches[0]
    record.update(device_name=device.name, device_address=device.address)
    print(f'BLE_DEVICE={device.name} {device.address}', flush=True)
    started = None
    last_progress = time.monotonic()
    connection_number = 0
    while started is None or time.monotonic() - started < args.seconds:
        connection_number += 1
        record['connections'] = connection_number
        disconnected = asyncio.Event()
        sink.reset_stream()
        ack_task = None
        try:
            async with BleakClient(device, disconnected_callback=lambda _: disconnected.set(), timeout=20) as client:
                acknowledgements = asyncio.Queue()
                def notification(_, data):
                    for token in sink.feed(data, device.address, connection_number):
                        acknowledgements.put_nowait(token)
                async def send_acknowledgements():
                    while True:
                        boot, identifier = await acknowledgements.get()
                        await client.write_gatt_char(NUS_RX, f'ACK {boot} {identifier}\n'.encode(), response=False)
                await client.start_notify(NUS_TX, notification)
                ack_task = asyncio.create_task(send_acknowledgements())
                ack_task.add_done_callback(lambda task: disconnected.set() if not task.cancelled() else None)
                await asyncio.sleep(.2)
                command = 'RESUME' if started is not None or args.resume else 'START'
                await client.write_gatt_char(NUS_RX, (command + '\n').encode(), response=True)
                record['commands'].append(command)
                if started is None:
                    started = time.monotonic()
                print(f'BLE_COMMAND={command} connection={connection_number}', flush=True)
                while not disconnected.is_set() and time.monotonic() - started < args.seconds:
                    await asyncio.sleep(.2)
                    if time.monotonic() - last_progress >= 25:
                        print(f'CAPTURE_SECONDS={time.monotonic()-started:.1f} measurements={sink.metrics["measurements"]}', flush=True)
                        last_progress = time.monotonic()
                if client.is_connected:
                    await client.write_gatt_char(NUS_RX, b'PAUSE\n', response=True)
                    record['commands'].append('PAUSE')
                    await asyncio.sleep(.6)
                    await client.write_gatt_char(NUS_RX, b'STATUS\n', response=True)
                    record['commands'].append('STATUS')
                    await asyncio.sleep(.5)
                    await client.stop_notify(NUS_TX)
        except Exception as error:
            record['connection_errors'].append(str(error))
            print(f'BLE_CONNECTION_ERROR={error}', flush=True)
            if started is None:
                raise
        finally:
            if ack_task is not None:
                ack_task.cancel()
                try:
                    await ack_task
                except asyncio.CancelledError:
                    pass
                except Exception as error:
                    record['connection_errors'].append('ACK transport: ' + str(error))
        if started is not None and time.monotonic() - started >= args.seconds:
            break
        print('BLE reconnecting; sweep pauses until RESUME', flush=True)
        await asyncio.sleep(2)
    record['seconds'] = time.monotonic() - started


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address', help='explicit BLE address; otherwise require one matching name')
    parser.add_argument('--name', default='UWB-COEX-INIT')
    parser.add_argument('--scan-seconds', type=float, default=8)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--resume', action='store_true', help='continue current sweep instead of START from 01')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.seconds <= 0 or args.scan_seconds <= 0:
        parser.error('durations must be positive')
    directory = args.out or Path('build') / ('ble_capture_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    directory.mkdir(parents=True, exist_ok=False)
    sink = LineSink(directory, args.quiet)
    record = dict(transport='BLE NUS', commands=[], connections=0, connection_errors=[])
    print('CAPTURE_DIR=' + str(directory), flush=True)
    error = None
    try:
        asyncio.run(collect(args, sink, record))
    except (Exception, KeyboardInterrupt) as exception:
        error = exception
        record['error'] = str(exception)
    finally:
        sink.close()
        record['transport_metrics'] = sink.metrics
        (directory / 'capture.json').write_text(json.dumps(record, indent=2) + '\n')
    if sink.metrics['measurements']:
        from analyze_checked_variants import analyze
        summary, _ = analyze(directory / 'init.log')
        (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(record, indent=2), flush=True)
    if error:
        raise SystemExit(str(error))


if __name__ == '__main__':
    main()
