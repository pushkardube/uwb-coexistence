# Bluetooth telemetry for checked UWB ranging and power sweeps

This module adds BLE to the **initiator only**. The matching responder keeps
the checked UWB protocol and does not need a Bluetooth connection to the laptop.
The new standalone application is [../twr_checked_ble_init](../twr_checked_ble_init/README.md).

```text
Far responder(s) -- UWB Result: timestamp + Final RSSI --> Initiator
                                                        |
                                                        +-- BLE NUS --> Laptop
```

Both boards still require power. Use a USB power bank or suitable USB power
supply instead of a laptop USB data connection. The laptop needs BLE range to
the initiator; the farther responder needs UWB range to the initiator. This
does not extend the underlying UWB or Bluetooth radio range.

## What stays in the radio exchange

The shared implementation is [../twr_checked_combined_common/checked.c](../twr_checked_combined_common/checked.c).
The 65-setting schedule, responder-side Final RSSI, DGC correction, sequence/peer
validation and timestamp math are retained. Replies use FEFEFEFE; the initiator
starts at 01010101 and sweeps the normal ladder. Current default BLE build:
one responder, 20 attempts per setting, matching the latest two-board map.

CHECKED_BLE=1 redirects post-exchange reporting to telemetry_line. Without that
definition, REPORT remains printk and the plain combined roles do not initialize
Bluetooth. The responder's build remains BLE-free. Protocol version stays 4:
Bluetooth changes host transport/control rather than the UWB packet layout.

telemetry.c never accesses the DW3000. The main thread formats bounded records
after exchanges and puts them in a 32-record queue; a lower-priority thread
sends BLE notifications. BLE controller interrupts still share the MCU, so
on-hardware ranging validation with Bluetooth active is required, rather than
assuming that queueing removes every possible timing effect.

## Build and flash

```bash
# Repository root. Defaults: one responder, 20 attempts per power setting.
bash tools/build_checked_ble.sh 1 20
bash tools/flash_checked_variant.sh ble 760201778 760201915
```

Build directories are checked_ble_init and checked_ble_resp0. More responders
can be built with the first argument, each receiving its own image/ID. Supply
their explicit serials to the flash helper. The builder verifies compiler
settings, BLE selection and image hashes in checked_variants_ble_manifest.json.
The flash helper uses west/nrfutil, responders first, initiator last, no rebuild.

The initiator advertises as **UWB-COEX-INIT**. The Nordic UART Service UUID is
`6e400001-b5a3-f393-e0a9-e50e24dcca9e`; TX notifications end in 0003 and RX
writes in 0002. It supports one laptop connection. The current lab firmware
does not require pairing; it is not a deployment access-control design.

## Laptop capture, with no serial port

Use system Python with Bleak installed and the laptop's Bluetooth adapter on:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py --seconds 300
```

The collector scans for exactly one matching name, subscribes, and sends START.
Use --address BLE_ADDRESS if more than one matching initiator is nearby.
It saves init.log, measurements.csv, capture.json and summary.json under a
new build/ble_capture_<timestamp> directory. Use --out NEW_DIRECTORY to choose
another location. There is **no serial-port read or USB reset** in this path.

The console shows the same COMBINED distance/RSSI records. Existing analyzers
and the complete-cycle power-map exporter accept the resulting init.log:

```bash
python3 tools/analyze_checked_variants.py build/<ble_capture>/init.log
python3 tools/export_power_rssi_map.py build/<ble_capture>/init.log \
  --out-prefix experiments/ble_power_map_NEW_RUN
```

A full default sweep requires 1300 attempts, plus transport/control time.
The 300-second example is an initial capture window; confirm all settings and
complete counts before claiming a full table. A BLE interruption pauses progress
and can increase the wall-clock time required.

## Move the boards away from the laptop

1. Flash the selected boards while their USB/J-Link connections are available.
2. Power each board from a USB power bank or USB power supply. A USB data
   connection to the laptop is no longer needed.
3. Keep the laptop within Bluetooth range of the initiator. The responder can
   be farther away, within the UWB link's working range to the initiator.
4. At a fixed geometry, run the collector command above. It starts a fresh
   sweep and saves the distance/RSSI records from all configured peers.
5. At the timed end, or when the Bluetooth connection closes, the initiator
   pauses. Move the receiver, then start another capture with a new output
   directory to measure the next position.

A continuously moving receiver can be monitored live, but do not label such
an entire sweep as a fixed-distance register/RSSI calibration.

## Commands, acknowledgements and disconnections

RX commands are newline-terminated ASCII:

| Command | Effect at a safe exchange boundary |
|---|---|
| START | Reset sweep sequence/counters to the initial 01 setting and run |
| PAUSE | Stop starting new exchanges; retain sweep position |
| RESUME | Continue from the retained position |
| STATUS | Return connection/run/queue/drop/retry counters |

The initiator waits after boot until notifications are enabled and START/RESUME
is received. When the BLE link disappears or the queue approaches capacity,
it stops starting new exchanges. An already active exchange can finish first.
There is no durable on-board offline measurement archive.

BLE notifications can split a text line into multiple packets. Each queued
record has a `BLE_RECORD boot=<nonce> id=<number>` envelope followed by the
original text line. The collector reassembles the full line, writes it, and
sends `ACK <nonce> <number>`. Unacknowledged records are replayed after reconnect;
the collector acknowledges replays without duplicating the saved measurement.
A boot nonce distinguishes a board reboot from an ordinary link reconnect.
STATUS transport counters are cumulative since boot; START resets the UWB
sweep counters but does not clear transport retry/drop history.

The supplied collector implements this protocol. A generic NUS terminal can
show a record but will not provide a continuous stream unless it implements
the record acknowledgements. Do not use the older collect_spatial.py: it expects
a different six-field PRR payload despite using NUS as well.

The collector automatically reconnects and sends RESUME. --resume also continues
an existing sweep on the first connection; otherwise it starts a fresh run.
At a normal timed stop it sends PAUSE and requests STATUS. Interrupting/closing
the link also pauses subsequent exchanges. Queue drops and host sequence gaps
are explicit metrics, not silently classified as UWB packet loss.

## Implementation and verification files

- telemetry.h: small interface called by the BLE application's main/radio loop.
- telemetry.c: NUS advertising, command parser, bounded queue, fragmentation,
  acknowledgements, retry/reconnect handling and flow control.
- [collect_checked_ble.py](../../tools/collect_checked_ble.py): laptop BLE client,
  reassembly, replay deduplication, command/ACK handling and logging.
- [test_collect_checked_ble.py](../../tools/test_collect_checked_ble.py): byte-wise
  fragmentation, coalescing, disconnect tails, gaps, bounded buffers and replay tests.
- [BLE bench record](../../experiments/checked_ble_bench.md): actual tests and limits.

The initial notification-only prototype lost three records during a connection
timeout despite successful local notification completion. That is why this
version uses application acknowledgements rather than treating a BLE send
callback as proof that the laptop saved the entire record.

This is telemetry for the current ranging/sweep experiment, not yet the spatial
plan's independent broadcast PRR counter. A responder whose UWB Result cannot
reach the initiator does not gain an independent host reporting path from this
aggregator design. That later instrument remains separate planned work.
