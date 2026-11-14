# Ascending 01010101-to-FEFEFEFE sweep with three responders

Date: 2026-11-14. The user requested a complete increasing-power sweep with
distance and RSSI stored for all three responders, following the opposite-facing
setup. Exact board angles and tape-measured antenna separations were not supplied.

## Acquisition order and firmware

The original sweep acquires 01, FE, FA, …, 02. This run instead acquires
**01, 02, 06, 0A, …, FA, FE**, using the same 65 register settings.
This is an actual change in acquisition order, not a post-hoc sort by power or RSSI.

Independent source directories:

```text
samples/twr_checked_ascending_common/
samples/twr_checked_ascending_init/
```

The copied common core changes only the level-to-octet plan and the ready
banner's `order=ascending` label. Ranging timestamps, diagnostics, PHY and
on-air protocol 4 remain unchanged. The original combined/BLE source and its
saved images were preserved; the old LOS summary remained identical when
order-aware analysis support was added.

| Role | Serial | Firmware / power |
|---|---|---|
| BLE initiator | 760201915 | Ascending Poll/Final power |
| Responder 0 | 760201778 | Compatible protocol-4 responder; replies FEFEFEFE |
| Responder 1 | 760204734 | Compatible protocol-4 responder; replies FEFEFEFE |
| Responder 2 | 760204645 | Compatible protocol-4 responder; replies FEFEFEFE |

All three responder images produced by the ascending builder matched the
already-installed responder images byte for byte. Only the initiator was
reprogrammed. BLE identity remains F1:FB:C0:BC:DB:75, name UWB-COEX-INIT.

Build and flash:

```bash
bash tools/build_checked_ascending.sh
source tools/ncs_env.sh
export NRFUTIL_HOME="$PWD/build/.nrfutil"
west flash --skip-rebuild -d build/checked_ascending_init -r nrfutil --dev-id 760201915
```

Logs: `build/checked_ascending_build_20261114.log` and
`build/checked_ascending_init_flash_20261114.log`. The role/ID/compiler checks
and image hashes are in `build/checked_variants_ascending_manifest.json`.

Host checks passed for the full ascending plan, equal budgets over two cycles,
order-aware analysis, and ascending comparison-file metadata. Existing combined,
fixed01 and three-responder tests also passed during implementation.

## Bluetooth-only capture

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --seconds 720 --address F1:FB:C0:BC:DB:75 \
  --out experiments/data/2026-11-14/opposite_facing_ascending_sweep_run1
```

There are 20 addressed attempts per responder per setting, 60 attempts per
setting and **3900 attempts per complete cycle**. Errors consume their attempt
budget and do not stall power progression. The three peers are addressed in
succession at each common TX setting. No serial ports are opened for measurement.

Files are stored in the run directory above:

- `measurements.csv`: individual timestamps, peer/cycle/level, TX register,
  range, corrected/legacy RSSI, validity, C/N/D and errors.
- `init.log`: raw decoded BLE records.
- `rssi_by_tx_setting.csv` / `.json`: side-by-side statistics for all three peers.
- `capture.json`: BLE commands, connections and transport integrity.
- `summary.json`: per-peer/per-level analysis with ascending-order validation.
- `layout.json`: board mapping, user-reported orientation and comparison limits.
- `provenance.json`: source/image hashes and build settings.

The raw records are stored as they arrive. Comparison files may be regenerated
during acquisition without touching any radio or serial port.

## Interpretation

RSSI is an uncalibrated DGC-corrected estimate in dB. Reported distances are UWB
ranges, not tape ground truth. A missing distance/RSSI for a failed setting stays
unavailable; an independently reported distance at FE must not be substituted
as if it were measured during a failed low-power exchange.

The prior LOS experiment used a different physical initiator, so comparing runs
does not isolate antenna orientation alone. Keep this dataset separate from the
earlier LOS and fixed-power runs. Full TWR completion is not one-way PRR.

## Completed acquisition

See [the power-threshold analysis](opposite_facing_power_threshold_analysis_20261114.md)
for the distance-dependent completion transition and the observed selective
0A0A0A0A setting.

The timed BLE run saved **4031 consecutive attempts**, with
**3818 completed exchanges**, including the complete first
cycle and a partial second cycle.

The complete first cycle has **3900 attempts and 3769
completed exchanges**. It contains exactly 65 settings in actual ascending order,
from 01010101 through FEFEFEFE, and exactly 20 attempts per peer at each setting.
The full-cycle CSV/table filter cycle=0; the individual records retain the extra
partial-cycle attempts.

| Peer | Serial | Completed / attempts in cycle 0 | Median reported distance at FE (m) | Median RSSI at FE (dB) |
|---|---|---:|---:|---:|
| 0 | 760201778 | 1296/1300 | 0.863 | -64.03 |
| 1 | 760204734 | 1209/1300 | 2.154 | -75.42 |
| 2 | 760204645 | 1264/1300 | 1.894 | -70.87 |

At 01010101, completion was 20/20 for peer 0, 0/20 for peer 1, and 1/20
for peer 2. At FEFEFEFE all three completed 20/20. A missing low-power distance
or RSSI stays NA; the FE reference distance above is explicitly a different
setting's measurement. All failed attempts remain in the individual and grouped
files. These are full TWR outcomes, not proof of one-way zero reception.

The first cycle has 131 radio-error records (code 2): 4 for peer 0, 91 for
peer 1, and 36 for peer 2. There were no fatal reports. Valid C/N/D-based RSSI
corrections matched `final_rssi_mdB + 6000*D` exactly.

BLE used one connection with no reported connection errors, sequence gaps,
duplicates, out-of-order records, framing errors, discarded partial bytes,
queue drops or transport replays. Every individual CSV record matched the
corresponding parsed raw BLE fields. Final STATUS reported running=0 and queue=0.

### Full values

- [65-setting Markdown distance/RSSI table](data/2026-11-14/opposite_facing_ascending_sweep_run1/cycle0_distance_rssi.md)
- [65-setting CSV with all three peers](data/2026-11-14/opposite_facing_ascending_sweep_run1/cycle0_rssi_by_tx_setting.csv)
- [All individual readings and errors](data/2026-11-14/opposite_facing_ascending_sweep_run1/measurements.csv)
- [Validation and hashes](data/2026-11-14/opposite_facing_ascending_sweep_run1/validation.json)

The original sweep firmware sources and all four saved images were checked
again and remain unchanged. The separate ascending application remains flashed
on 760201915 and waits for the next BLE START. The source, selected raw evidence and this report are versioned together.
