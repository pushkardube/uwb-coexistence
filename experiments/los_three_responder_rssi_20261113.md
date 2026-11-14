# BLE-only RSSI capture: three LOS responders at approximately 1 m spacing

Date: 2026-11-13. This is a new acquisition after the initial
[three-responder validation](three_responder_rssi_20261113.md).
The user reports all boards in a line, approximately 1 m apart, with LOS.
Two responders use the laptop's USB power and the last uses a separate supply.
Exact tape distances and the physical ordering of peer IDs were not supplied.

## Acquisition method

All measurement data comes from the initiator's BLE Nordic UART Service.
The capture opens no serial ports and does not reset or reprogram any board.
Responders send their Final receive diagnostics to the initiator over UWB;
the initiator relays them over BLE, including the separately powered responder.

| Role | J-Link serial | USB present at acquisition start |
|---|---|---|
| Initiator | 760201778 | Yes |
| Peer 0 | 760201915 | No |
| Peer 1 | 760204734 | Yes |
| Peer 2 | 760204645 | Yes |

Peer 0's USB absence is consistent with the user-described external supply.
USB presence was checked through sysfs for identification only; no UART data
was read. All three peer IDs appeared in BLE measurement records.

Command run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --seconds 720 --address CB:56:11:3C:AB:ED \
  --out experiments/data/2026-11-13/los_three_responders_run1
```

The firmware uses protocol 4, channel 9, three peers and 20 attempts per peer
at each of 65 TX settings. A full cycle therefore comprises 3900 attempts.
The initial 01010101 probe is followed by FEFEFEFE down through the 64 fine
codes at coarse gain 2, ending at 02020202. Responder reply power remains FE.
Peers are addressed in quick succession at each common TX setting.

## Files

All readings for this run are stored inside the repository:

- [Raw decoded BLE records](data/2026-11-13/los_three_responders_run1/init.log)
- [Individual readings CSV](data/2026-11-13/los_three_responders_run1/measurements.csv)
- [Board/layout metadata](data/2026-11-13/los_three_responders_run1/layout.json)
- `capture.json`: BLE commands, connection history and transport integrity.
- `summary.json`: per-peer/per-level statistics and schedule checks.
- `rssi_by_tx_setting.csv` / `.json`: three-peer comparisons, separated by cycle and setting.

The last four outputs are finalized after the timed acquisition. Intermediate
comparison files may be regenerated from the log during acquisition without
opening any radio or serial connection. The console log is stored alongside
the run directory as `los_three_responders_run1_console.log`.

## Interpretation

Reported distance comes from UWB ranging and is not tape ground truth.
Corrected RSSI is an uncalibrated dB estimate. Exact board positions and
antenna orientations are not inferred from peer numbers. Analyze the same TX
setting across peers; do not regress pooled TX-power sweep readings against
distance. Failed exchanges and missing RSSI remain explicit.

## Completed result

The timed run saved **4072 consecutive attempts**, sequences 1–4072, with
**4069 completed exchanges**. It includes one full 65-setting cycle followed
by part of cycle 1. Do not pool the extra cycle-1 records into first-cycle
20-sample groups.

The complete first cycle contains **3900 attempts and 3898 completed exchanges**.
All 65 settings have exactly 20 attempts per responder. Every completed
exchange returned valid RSSI.

| Peer | Board serial | Cycle-0 completed / attempts | USB connected |
|---|---|---:|---|
| 0 | 760201915 | 1300/1300 | No; consistent with external power |
| 1 | 760204734 | 1300/1300 | Yes; power only for this acquisition |
| 2 | 760204645 | 1298/1300 | Yes; power only for this acquisition |

The two cycle-0 errors are radio error code 2 for peer 2 at sequences 2823
and 2949, levels 47 and 49. One additional peer-1 radio error occurred in the
partial next cycle, sequence 3956 at the initial 01 setting. These are retained
as failed exchanges; no RSSI was invented for them.

BLE used one connection with no connection errors. Capture metadata reports
zero sequence gaps, duplicates, out-of-order records, framing errors, discarded
partial bytes, queue drops and transport replays. Final STATUS reported
running=0 and queue=0. All 4072 individual CSV records matched the corresponding
parsed BLE log fields, and every valid corrected RSSI matched
`final_rssi_mdB + 6000*D`. No serial stream was used for this verification.

### Same-TX-setting readings

Per-setting medians from cycle 0, sorted by reported distance within each setting:

| TX register | Peer | Median reported range (m) | Median corrected RSSI (dB) | Completed |
|---|---:|---:|---:|---:|
| 0x01010101 | 2 | 0.7680 | -85.3920 | 20/20 |
| 0x01010101 | 1 | 1.7725 | -92.0410 | 20/20 |
| 0x01010101 | 0 | 2.8615 | -88.5200 | 20/20 |
| 0xFEFEFEFE | 2 | 0.7470 | -63.1705 | 20/20 |
| 0xFEFEFEFE | 1 | 1.7515 | -69.0165 | 20/20 |
| 0xFEFEFEFE | 0 | 2.8120 | -68.1520 | 20/20 |
| 0x02020202 | 2 | 0.7690 | -84.1470 | 20/20 |
| 0x02020202 | 1 | 1.7625 | -90.5790 | 20/20 |
| 0x02020202 | 0 | 2.8465 | -87.1470 | 20/20 |

The reported near-to-far ordering is peer 2, peer 1, then peer 0. These are
UWB-derived positions, not independently measured distances. Peer 0 is slightly
stronger than the middle peer at the listed settings; LOS and approximate
collinearity do not by themselves establish a distance-only RSSI law.
This dataset should not be presented as a calibrated dB-per-metre fit.

### Convenient complete-cycle file

[cycle0_rssi_by_tx_setting.csv](data/2026-11-13/los_three_responders_run1/cycle0_rssi_by_tx_setting.csv)
contains exactly the 65 first-cycle rows with all three peer columns.
It is a direct filter of `rssi_by_tx_setting.csv` for cycle=0, with values and
acquisition ordering unchanged. The unfiltered CSV/JSON retain the additional
partial-cycle data.

`layout.json` records the user-supplied geometry and the USB identity snapshot;
`provenance.json` records source/image hashes and the built configuration;
`validation.json` records counts, full-cycle budget checks, raw/CSV agreement,
gain-correction checks and data hashes. A short README is also saved in the
run directory. The selected raw evidence and this report are versioned together.
