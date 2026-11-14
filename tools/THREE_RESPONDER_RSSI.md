# Save RSSI and range from three responders

Use [collect_three_responder_rssi.py](collect_three_responder_rssi.py) with a
BLE initiator compiled for three responders. It saves individual readings
and a comparison table with all three peers at the same TX register setting.
The radio addresses the peers in succession; this is not simultaneous RF reception.

The script reuses [collect_checked_ble.py](collect_checked_ble.py) for Bluetooth
notifications, record acknowledgements, reconnect/replay handling, and safe
START/PAUSE control. It does not open serial ports or program any board.

It also accepts the separate [ascending sweep](../samples/twr_checked_ascending_common/README.md).
Its `order=ascending` banner is validated and retained in comparison metadata.
See [the opposite-facing ascending run](../experiments/opposite_facing_ascending_sweep_20261114.md)
for that run's newer initiator/peer mapping; the table below records the earlier
2026-11-13 setup.

## Current board assignments

The four-board setup programmed on 2026-11-13 uses:

| Role | J-Link serial | Firmware build |
|---|---|---|
| BLE initiator | 760201778 | build/checked_ble_init |
| Responder ID 0 | 760201915 | build/checked_ble_resp0 |
| Responder ID 1 | 760204734 | build/checked_ble_resp1 |
| Responder ID 2 | 760204645 | build/checked_ble_resp2 |

The initiator advertises `UWB-COEX-INIT`, address `CB:56:11:3C:AB:ED` on this
board. Other boards may have different addresses. All responders return Final
diagnostics over UWB; only the initiator connects to the laptop over Bluetooth.
The existing responder-1 board retains its previous ID; the newly added board
is responder 2. Peer IDs do not imply an ordering by physical distance.

## Build and flash

Run from the repository root. For this lab mapping:

```bash
bash tools/build_checked_ble.sh 3 20
bash tools/flash_checked_variant.sh ble 760201778 760201915 760204734 760204645
```

Those commands program the whole setup. When programming boards individually,
select their matching `build/checked_ble_respN` directory and explicit serial
with `west flash --skip-rebuild -r nrfutil --dev-id SERIAL`.

There are 65 settings: the `01010101` probe, then `FEFEFEFE` through
`02020202` in fine-gain steps at coarse 2. Each peer gets 20 attempts at each
setting. Thus a complete cycle contains 3900 attempts, whether successful or not.
Responder replies stay at `FEFEFEFE`.

## Collect

Use normal host Python with `bleak` installed and Bluetooth powered on:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py --seconds 720
```

Default output: a new `build/three_responder_rssi_<timestamp>/` directory.
For a specific initiator and output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --seconds 720 --address CB:56:11:3C:AB:ED --out build/three_peers_NEW_RUN
```

The output directory must not already exist. The collector starts a fresh
sweep and sends PAUSE/STATUS at the timed end. Twelve minutes is an initial
full-cycle budget, not a guarantee: BLE pauses or retries can extend a cycle.
Check the resulting counts instead of assuming all levels were completed.

Keep the boards fixed throughout one capture. They can use external USB power;
only the initiator must remain within BLE range. Record tape-measured antenna
separations, orientation and board-to-position mapping separately.

## Saved files

| File | Contents |
|---|---|
| measurements.csv | Every complete measurement/error record with host time, peer, sequence, cycle, TX setting, reported range, corrected/legacy RSSI and raw C/N/D |
| init.log | Decoded firmware records without the BLE record envelope |
| capture.json | BLE address, connection history, errors and transport integrity counters |
| summary.json | Per-peer/per-level analysis and schedule checks |
| rssi_by_tx_setting.csv | One row per observed cycle/setting, with distance/RSSI statistics for peers 0, 1 and 2 side by side |
| rssi_by_tx_setting.json | The comparison rows, configuration and summary flags |

Comparison CSV fields have `peer0_`, `peer1_`, or `peer2_` prefixes:
attempts, completed, valid_rssi, distance_m_median, rssi_db_median,
rssi_db_min, rssi_db_max and errors. `first_seq` and `last_seq` identify the
setting's measurement window. Different cycles are kept separate.

`full_attempt_budget` means all three peers received the configured number of
attempts at that setting; it does not mean every attempt succeeded.
`all_peers_have_valid_rssi` means each peer supplied at least one valid sample.
Failed attempts remain in the counts; absent or invalid measurements have
blank CSV cells / JSON null, never fabricated zero RSSI. RSSI statistics are
conditional on successful frames with valid diagnostics.

Distances are UWB-reported metres. RSSI is the DGC-corrected relative estimate
in dB, not calibrated dBm. The script does not fit a path-loss exponent: different
board calibration, orientation and propagation conditions can confound a
distance-versus-RSSI fit. Compare the same TX setting, not pooled sweep values.

## Re-analyze without Bluetooth

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --summarize-only build/three_peers_NEW_RUN
```

This regenerates the comparison and summary files from the latest startup
in the existing `init.log`; it does not overwrite raw readings or use a radio.
It rejects a different target count or an inconsistent schedule.

## Host test

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_collect_three_responder_rssi.py
```

Tests cover three-peer grouping and units, failed/missing peers, incomplete
budgets, invalid diagnostics, latest-startup selection and wrong target counts.
