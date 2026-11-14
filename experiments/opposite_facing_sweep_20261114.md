# Repeat sweep with the opposite-facing orientation

Date: 2026-11-14. The user requested repeating the previous power sweep with
all anchors facing exactly in opposite directions, and programming the sole
connected board as the initiator before connecting the other three responders.
The precise antenna-angle reference and new physical distances remain to be
recorded with the actual capture.

## Initiator programmed

- Serial: **760201915**, the only USB probe present at programming time.
- Image: `build/checked_ble_init/merged.hex`, original protocol-4 BLE sweep.
- Three targets, 65 TX settings, 20 attempts per peer per setting.
- Initiator sequence: 01010101, then FEFEFEFE through 02020202 at coarse 2.
- Matching sweep responder reply power: FEFEFEFE.
- BLE name: UWB-COEX-INIT; address: **F1:FB:C0:BC:DB:75**.

The sweep core and BLE telemetry source hashes matched the previous LOS run.
The initiator image also matched that run's saved image hash. No sweep source
or radio/timing configuration was changed for the new orientation.

Only 760201915 was programmed, using:

```bash
source tools/ncs_env.sh
export NRFUTIL_HOME="$PWD/build/.nrfutil"
west flash --skip-rebuild -d build/checked_ble_init -r nrfutil --dev-id 760201915
```

west/nrfutil reported successful programming and verification. A selected reset
with a boot-only UART check confirmed role INIT, protocol 4, targets=3,
levels=65 and attempts_per_peer=20. No ranging data was collected and no BLE
START was issued at this stage. The initiator advertises and waits for START.

Logs and setup record:

```text
build/opposite_facing_sweep_init_flash_20261114.log
build/opposite_facing_sweep_init_boot_20261114.log
build/opposite_facing_sweep_setup_20261114.json
```

## Responders programmed

The three newly connected boards were identified and successfully programmed
and verified with explicit serials:

| Role | Serial | Image |
|---|---|---|
| Responder 0 | 760201778 | build/checked_ble_resp0/merged.hex |
| Responder 1 | 760204734 | build/checked_ble_resp1/merged.hex |
| Responder 2 | 760204645 | build/checked_ble_resp2/merged.hex |

Only those three responders were flashed in this stage. The already-programmed
760201915 initiator was left running. Image hashes, protocol-4 compatibility
and compiler ID/count definitions were verified before programming.
Logs are `build/opposite_facing_sweep_resp{0,1,2}_flash_20261114.log`.

A short BLE-only setup check uses a separate directory:

```bash
python3 tools/collect_three_responder_rssi.py --seconds 30 \
  --address F1:FB:C0:BC:DB:75 \
  --out experiments/data/2026-11-14/opposite_facing_setup_validation
```

This short check is not a full sweep or a completed orientation comparison.
The full recorded experiment can use:

```bash
python3 tools/collect_three_responder_rssi.py --seconds 720 \
  --address F1:FB:C0:BC:DB:75 --out experiments/data/opposite_facing_NEW_RUN
```

A full cycle is 3900 attempts; verify actual completeness after acquisition.

The previous LOS initiator was 760201778. Changing the initiating physical
board as well as the antenna orientation means a comparison is not a pure
orientation-only controlled experiment. Keep this run's board mapping and raw
readings separate from the previous LOS and fixed01 captures.

## Setup-check result

All three responders returned valid distance/RSSI data over BLE during the
30-second check. The capture contains 168 consecutive attempts, 148 completed
exchanges, two complete settings and part of the next. All 20 radio errors
were peer 1 at the initial 01010101 setting. There were no fatal reports or
reported BLE sequence gaps, duplicates, framing errors or queue drops.

| Initiator TX_POWER | Peer | Completed / attempts |
|---|---:|---:|
| 0x01010101 | 0 | 20/20 |
| 0x01010101 | 1 | 0/20 |
| 0x01010101 | 2 | 20/20 |
| 0xFEFEFEFE | 0 | 20/20 |
| 0xFEFEFEFE | 1 | 20/20 |
| 0xFEFEFEFE | 2 | 20/20 |

The peer-1 response at FE confirms that it is programmed and reachable despite
its 0/20 full-exchange completion at 01 in this short sample. These counts do
not establish long-term one-way PRR or zero physical signal reception.
Final BLE STATUS reported running=0 and queue=0, ready for a fresh START.

[Individual readings](data/2026-11-14/opposite_facing_setup_validation/measurements.csv),
[three-peer comparison](data/2026-11-14/opposite_facing_setup_validation/rssi_by_tx_setting.csv),
and [validation metadata](data/2026-11-14/opposite_facing_setup_validation/validation.json)
are saved separately from the previous orientation runs.
