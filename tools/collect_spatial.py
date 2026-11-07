#!/usr/bin/env python3
"""
collect_spatial.py — laptop-side data collector for the UWB spatial-resolution
experiment (samples/spatial_resolution_rx).

Each receiver board runs a Nordic UART Service (NUS) and, at the end of every
TX burst, notifies one CSV line:

    <epoch>,<pos>,<recv>,<N>,<prr_hundredths>,<rssi_millidb>\\n

This script scans for every advertising receiver (default name "DWM3001-RX"),
connects to all of them at once, subscribes to their notifications, and writes
one merged CSV with a wall-clock timestamp and the board's BLE address so rows
from different receivers stay distinguishable.

Install:
    pip install bleak

Run:
    python collect_spatial.py --csv run1.csv                 # all boards, until Ctrl-C
    python collect_spatial.py --csv run1.csv --duration 120  # stop after 120 s
    python collect_spatial.py --name DWM3001-RX --scan 8
    python collect_spatial.py --addr AA:BB:.. --addr CC:DD:..  # explicit boards, skip scan
"""

import argparse
import asyncio
import csv
import sys
import threading
from datetime import datetime

from bleak import BleakClient, BleakScanner

NUS_TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
DEFAULT_NAME = "DWM3001-RX"

CSV_HEADER = [
    "wall_time", "device", "epoch", "pos",
    "received", "N", "prr_pct", "rssi_db",
]


class Collector:
    def __init__(self, csv_path):
        self._lock = threading.Lock()
        self._rows = 0
        self._csv_file = None
        self._csv_writer = None
        if csv_path:
            self._csv_file = open(csv_path, "w", newline="")
            self._csv_writer = csv.writer(self._csv_file)
            self._csv_writer.writerow(CSV_HEADER)
            self._csv_file.flush()
        self.csv_path = csv_path

    def handle(self, device_addr, data: bytearray):
        # One notification may carry one or more newline-separated lines.
        text = data.decode("utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            self._handle_line(device_addr, line)

    def _handle_line(self, device_addr, line):
        parts = line.split(",")
        if len(parts) != 6:
            print(f"[WARN] {device_addr}: unexpected format: {line!r}")
            return
        try:
            epoch, pos, recv, n = (int(parts[0]), int(parts[1]),
                                   int(parts[2]), int(parts[3]))
            prr_pct = int(parts[4]) / 100.0
            rssi_db = int(parts[5]) / 1000.0
        except ValueError:
            print(f"[WARN] {device_addr}: non-numeric field: {line!r}")
            return

        wall = datetime.now().isoformat(timespec="milliseconds")
        print(f"[{wall}] {device_addr}  epoch={epoch:>3} pos={pos:<3} "
              f"recv={recv}/{n}  PRR={prr_pct:6.2f}%  RSSI={rssi_db:7.2f} dB")

        with self._lock:
            self._rows += 1
            if self._csv_writer:
                self._csv_writer.writerow(
                    [wall, device_addr, epoch, pos, recv, n,
                     f"{prr_pct:.2f}", f"{rssi_db:.3f}"])
                self._csv_file.flush()

    def close(self):
        print(f"\nCollected {self._rows} rows.")
        if self._csv_file:
            self._csv_file.close()
            print(f"Saved to {self.csv_path}")


async def discover(name, timeout):
    print(f"Scanning {timeout:.0f}s for '{name}' boards ...")
    devices = await BleakScanner.discover(timeout=timeout)
    matches = [d for d in devices if d.name and d.name.startswith(name)]
    if not matches:
        print(f"ERROR: no '{name}' boards found. Are they advertising?")
        sys.exit(1)
    for d in matches:
        print(f"  found {d.name}  [{d.address}]")
    return [d.address for d in matches]


async def run_board(addr, collector, stop_event):
    """Connect to one board, subscribe, hold until stop_event is set."""
    def cb(_char, data):
        collector.handle(addr, data)

    try:
        async with BleakClient(addr) as client:
            print(f"Connected {addr}")
            await client.start_notify(NUS_TX_UUID, cb)
            await stop_event.wait()
            try:
                await client.stop_notify(NUS_TX_UUID)
            except Exception:
                pass
        print(f"Disconnected {addr}")
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")


async def main(name, addrs, csv_path, scan_timeout, duration):
    if not addrs:
        addrs = await discover(name, scan_timeout)

    collector = Collector(csv_path)
    stop_event = asyncio.Event()

    tasks = [asyncio.create_task(run_board(a, collector, stop_event)) for a in addrs]

    print(f"\nCollecting from {len(addrs)} board(s). "
          f"{'Stopping after %ds.' % duration if duration else 'Ctrl-C to stop.'}\n")
    try:
        if duration:
            await asyncio.sleep(duration)
        else:
            while not stop_event.is_set():
                await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        collector.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="UWB spatial-resolution BLE collector")
    ap.add_argument("--name", default=DEFAULT_NAME,
                    help=f"BLE name prefix to scan for (default: {DEFAULT_NAME})")
    ap.add_argument("--addr", action="append", default=[],
                    help="explicit BLE address (repeatable); skips scanning")
    ap.add_argument("--csv", default=None, metavar="FILE",
                    help="CSV file to write (default: print only)")
    ap.add_argument("--scan", type=float, default=8.0, metavar="SEC",
                    help="scan duration in seconds (default: 8)")
    ap.add_argument("--duration", type=float, default=None, metavar="SEC",
                    help="stop after this many seconds (default: run until Ctrl-C)")
    args = ap.parse_args()

    try:
        asyncio.run(main(args.name, args.addr, args.csv, args.scan, args.duration))
    except KeyboardInterrupt:
        pass
