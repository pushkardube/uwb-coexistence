# Four-board RSSI capture: one initiator and three responders

Date: 2026-11-13. Firmware is the existing checked BLE initiator plus plain
checked combined responders. Only build-time peer count and attempt budget
changed; no ranging or RSSI calculation was modified for this experiment.
The new Python wrapper and analysis are documented in
[THREE_RESPONDER_RSSI.md](../tools/THREE_RESPONDER_RSSI.md).

## Board mapping and programming

| Role | J-Link serial | Image |
|---|---|---|
| BLE initiator | 760201778 | build/checked_ble_init/merged.hex |
| Responder 0 | 760201915 | build/checked_ble_resp0/merged.hex |
| Responder 1 | 760204734 | build/checked_ble_resp1/merged.hex |
| Responder 2 | 760204645 | build/checked_ble_resp2/merged.hex |

The initiator was programmed alone first, as requested. The other three boards
were connected subsequently and programmed individually with explicit probe
serials using `west flash --skip-rebuild -r nrfutil --dev-id SERIAL`.
All programming commands reported verification and successful flashing.
Opening each UART before a selected reset confirmed all three responder IDs
and the initiator configuration at boot.

Configuration: protocol 4, channel 9, 65 TX settings, three target peers,
20 attempts per peer per setting. Each power setting lasts 60 addressed
attempts; a full cycle is 3900 attempts. All responder replies stay at FEFEFEFE.
The initiator advertises UWB-COEX-INIT at CB:56:11:3C:AB:ED.

The 360-second run below is a partial-sweep validation of the three-responder
setup. The collector now defaults to 720 seconds for an approximate full-cycle
window; actual completion must still be checked against all 3900 attempts.

Build command:

```bash
bash tools/build_checked_ble.sh 3 20
```

Build, programming and boot logs:

```text
build/checked_ble_3responders_build.log
build/checked_ble_3responders_init_flash.log
build/checked_ble_3responders_resp{0,1,2}_flash.log
build/checked_ble_3responders_init_boot.log
build/checked_ble_3responders_resp{0,1,2}_boot.log
build/checked_variants_ble_manifest.json
build/three_responder_rssi_20261113_validation.json
```

The manifest verifies actual compiler role, responder-ID and peer-count
definitions and SHA-256 image hashes. The validation JSON retains role mapping
and source hashes. Build binaries remain local. A selected byte-for-byte copy of this run's raw
capture and validation metadata is published with this report.

## Acquisition

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --seconds 360 --address CB:56:11:3C:AB:ED \
  --out build/three_responder_rssi_20261113_run1
```

This starts a fresh sweep, including the initial 01010101 probe, and saves
readings received over BLE. The three UWB exchanges occur in succession at
the same TX setting, not as simultaneous over-the-air replies. Keep the
geometry fixed throughout a capture. The user was asked for physical tape
distances; no tape measurements were supplied at acquisition start.

The user subsequently said the initiator directly faces the middle responder,
then clarified that all boards are in a line, approximately 1 m apart, with
LOS. The earlier facing-middle statement alone did not establish unequal
antenna angles. A separate BLE-only LOS capture was started after this
clarification; it is recorded in
[the LOS run report](los_three_responder_rssi_20261113.md). These captures must
not be pooled as if their positions were unchanged.

The original acquisition paths were:

```text
build/three_responder_rssi_20261113_run1/init.log
build/three_responder_rssi_20261113_run1/measurements.csv
build/three_responder_rssi_20261113_run1/capture.json
build/three_responder_rssi_20261113_run1/summary.json
build/three_responder_rssi_20261113_run1/rssi_by_tx_setting.csv
build/three_responder_rssi_20261113_run1/rssi_by_tx_setting.json
build/three_responder_rssi_20261113_run1_console.log
```

The individual CSV retains host timestamps, peer/sequence/cycle/level,
TX register, distance, RSSI and raw C/N/D. The comparison CSV separates cycles
and settings and reports each peer's attempts, completions, valid samples,
median range, median/min/max corrected RSSI and errors. Partial budgets and
missing RSSI are explicit. Invalid or absent readings are never converted to zero.

## Host verification

The existing combined scheduling test passed with CHECKED_N_RESPONDERS=3 and
SWEEP_ATTEMPTS=20. Four new Python tests passed for same-setting grouping,
failed/missing peers, invalid diagnostics, incomplete budgets, latest-startup
selection and rejection of a different target count.

The wrapper reuses the already-tested BLE ACK/replay and fragmentation collector.
Hardware acquisition is required to establish that all three peers actually
respond; passing the host tests alone does not establish radio behavior.

## Interpretation

Use the corrected `rssi_dgc_mdB` field divided by 1000. It is an uncalibrated
received-power estimate in dB. Distances are UWB-reported, not tape-measured.
Completion ratios describe the four-message ranging exchange, not one-way PRR.
Different boards and orientations can produce different RSSI offsets; this
capture is not by itself a calibrated dB-per-metre propagation model.

## Observed result: partial sweep validation

The requested 360-second window completed with **2037 consecutive attempts**,
sequences 1–2037, and **2031 completed exchanges**. All completed exchanges had
valid RSSI. Each peer received exactly 679 attempts. There were 33 full-budget
settings (levels 0–32) and 57/60 attempts at level 33, all in cycle 0.
This is not a complete 65-setting sweep. A full cycle needs 3900 attempts;
the documented default capture duration is now 720 seconds.

| Peer | Completed / attempts | Radio errors (code 2) |
|---|---:|---:|
| 0 | 679 / 679 | 0 |
| 1 | 678 / 679 | 1 |
| 2 | 674 / 679 | 5 |

Peer 2's five errors occurred at the initial 01010101 setting. The extra
peer-1 error remains in the saved data. No fatal reports, dropped UART-log
reports or sequence discontinuities were detected in the received stream.

BLE used one connection with no connection errors. Transport metadata reports
zero sequence gaps, duplicates, out-of-order records, framing errors,
discarded partial bytes, queue drops and transport replays. The collector sent
START, then PAUSE and STATUS at the timed end. These are collector observations;
no independent UART-versus-BLE exact-match capture was made for this run.

Every measurement CSV row was checked against the corresponding parsed raw
record for sequence, peer, cycle, level, TX octet, range, RSSI, raw C/N/D,
diagnostic validity and errors. All valid corrected RSSI values matched
`final_rssi_mdB + 6000*D` exactly.

### Same-setting comparison

The following are per-setting medians, not pooled statistics across different
transmit powers. Each group had 20 attempts per responder.

| TX register | Peer | Median reported range (m) | Median corrected RSSI (dB) | Completed |
|---|---:|---:|---:|---:|
| 01010101 | 0 | 1.7640 | -84.5700 | 20/20 |
| 01010101 | 1 | 1.0675 | -91.9585 | 20/20 |
| 01010101 | 2 | 1.8770 | -93.9690 | 15/20 |
| FEFEFEFE | 0 | 1.7045 | -62.7995 | 20/20 |
| FEFEFEFE | 1 | 1.0420 | -67.4695 | 20/20 |
| FEFEFEFE | 2 | 1.8640 | -69.6245 | 20/20 |

The larger reported distance for peer 0 than peer 1 accompanies stronger RSSI
at both listed settings. Antenna patterns, board calibration and multipath are
possible contributors, but this run does not isolate their effects. The user's
later LOS/line clarification should not be treated as proof of a particular
cause for the earlier RSSI ordering. A distance-only path-loss fit still needs
recorded board positions and controlled antenna orientation.

Raw sample example at FEFEFEFE (all fields come from actual captured records):

```text
COMBINED seq=61 peer=0 dist_mm=1735 final_rssi_mdB=-83949 diag=1 C=35 N=111 D=4 ok=56/61 peer_ok=21/21 cycle=0 level=1 octet=0xfe rssi_dgc_mdB=-59949 level_ok=1/1
COMBINED seq=62 peer=1 dist_mm=1035 final_rssi_mdB=-81504 diag=1 C=55 N=105 D=2 ok=57/62 peer_ok=21/21 cycle=0 level=1 octet=0xfe rssi_dgc_mdB=-69504 level_ok=1/1
COMBINED seq=63 peer=2 dist_mm=1888 final_rssi_mdB=-81388 diag=1 C=62 N=110 D=2 ok=58/63 peer_ok=16/21 cycle=0 level=1 octet=0xfe rssi_dgc_mdB=-69388 level_ok=1/1
```

The selected raw and derived files are published in
[data/2026-11-13/three_responder_initial_validation/](data/2026-11-13/three_responder_initial_validation/README.md).
They were copied byte for byte; publication.json retains original locations and
hashes. The build paths above describe acquisition history, not clone requirements.
