# Fixed 01010101 range test with two responders and BLE reporting

This separate experiment holds the initiator's transmit power at
**0x01010101 continuously**. It does not sweep or increase power after errors.
It builds on the checked combined DS-TWR implementation, preserving timestamp
handling, frame checks, bounded waits and responder-side Final RSSI.

Applications: [BLE initiator](../twr_checked_fixed01_init/README.md) and
[UWB responder](../twr_checked_fixed01_resp/README.md). Neither application
compiles the original combined core; they use this independent source copy.
BLE transport is reused from [twr_checked_ble_common](../twr_checked_ble_common/README.md).

## Radio behavior

| Frame | Transmitter | TX_POWER |
|---|---|---|
| Poll | Initiator | 0x01010101 |
| Response | Addressed responder | 0x01010101 |
| Final | Initiator | 0x01010101 |
| Result | Addressed responder | 0x01010101 |

The responder measures Final's RSSI, then returns raw C/N/D and the legacy
estimate in Result. The initiator applies the same DGC correction as the checked
sweep and reports over BLE. **Both link directions now use 01**, as requested
on 2026-11-14. A failed exchange may involve any of the four weak frames.
The earlier forward-only setup with FE replies is preserved in its
[2026-11-13 experiment record](../../experiments/fixed01_range_test_20261113.md).

The PHY remains channel 9, code 9, 128-symbol Ipatov preamble, 6.8 Mbps,
DW-8 SFD, STS off. PGdly is 0x34 and PGcount is 0.

On-air protocol version is **5**, so protocol-4 sweep responders do not join
this experiment. Packet structure and timestamp math remain unchanged.
The logger retains the COMBINED prefix so the existing BLE collector can
save all records. The ready banner explicitly includes:

```text
targets=2 levels=1 attempts_per_peer=20 dwell_attempts=40 mode=fixed tx_power=0x01010101 reply_tx_power=0x01010101
```

`combined_plan.h` returns octet 01 for every level argument and level 0 for
every attempt. Two peers alternate after every attempt, including failures.
Every 40 attempts produces a reporting window: 20 attempts per peer. `cycle`
increments between windows, but TX power never changes. Attempts continue
until paused over BLE or the initiator loses its host connection.

## Board mapping for the current two connected responders

| Role | J-Link serial | Former sweep role |
|---|---|---|
| BLE initiator | 760201778 | Initiator |
| Fixed01 responder 0 | 760204734 | Sweep responder 1 |
| Fixed01 responder 1 | 760204645 | Sweep responder 2 |

The separately powered 760201915 is not programmed for this experiment. Its
protocol-4 firmware is incompatible with these version-5 frames.

## Build and flash

Run from the repository root:

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 760201778 760204734 760204645
```

The builder creates independent `build/checked_fixed01_init`,
`build/checked_fixed01_resp0` and `build/checked_fixed01_resp1` directories.
It verifies actual compiler role/ID/count settings and saves image hashes in
`build/checked_variants_fixed01_manifest.json`. The flash helper checks live
probe IDs and hashes, programs the two responders, then the initiator.

## Move responders away and record over Bluetooth

1. Flash the three selected boards while connected over USB.
2. Keep the initiator near the laptop, powered and within BLE range.
3. Power the responders from external USB supplies. Their compiled IDs survive
   power cycling; they need no laptop data connection.
4. Start the collector in a normal host Python environment with Bleak installed:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py \
  --seconds 3600 --address CB:56:11:3C:AB:ED \
  --out experiments/data/fixed01_walk_NEW_RUN
```

The initiator still advertises UWB-COEX-INIT. The collector sends START,
receives both peers over BLE, writes complete readings immediately, and pauses
at the timed end. Choose a new output directory per run. A one-hour duration
is an example; select a shorter window as needed.

Files: `measurements.csv` (individual timestamps, ranges, RSSI, errors and raw
C/N/D), `init.log`, `capture.json` (BLE integrity), and `summary.json`.
The analyzer recognizes levels=1 only with an explicit fixed-power banner and
checks that the observed TX octet remains 01. Do not use the three-responder
wrapper, which intentionally requires three targets.

For walking tests, individual time-stamped readings describe changing positions;
reporting-window averages can span several positions. For a fixed-distance
measurement, stop and keep the geometry unchanged throughout the sample window.

RSSI is the responder-side corrected estimate in dB, not calibrated dBm;
distance is millimetres. Invalid RSSI stays unavailable. Failed exchanges remain
errors rather than fabricated distances or zero RSSI. A failed TWR transaction
does not prove that no UWB energy or individual frame reached the responder.
The inherited distance guard rejects results outside -2 to 100 m.

## Verification

```bash
cc -std=c99 -Wall -Wextra -Werror -Isamples/twr_checked_fixed01_common \
  tools/test_checked_fixed01.c -o /tmp/checked_fixed01
/tmp/checked_fixed01
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_analyze_fixed01.py
```

Host tests exercise fixed power across 10000 attempts, peer rotation, reporting
windows, 01 replies, DGC handling, missing peers and fixed-power log checks.
Hardware programming and BLE measurements are recorded separately in the
[experiment report](../../experiments/fixed01_both_directions_20261114.md).
