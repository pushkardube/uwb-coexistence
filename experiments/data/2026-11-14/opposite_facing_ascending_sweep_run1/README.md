# Opposite-facing ascending sweep — 2026-11-14

A complete acquisition in increasing nominal gain order: **01010101,
02020202, 06060606, ... FEFEFEFE**. The original descending-order sweep
source and saved images remain intact.

## Read the values

The [power-threshold analysis](../../../opposite_facing_power_threshold_analysis_20261114.md)
explains where each responder's exchanges start failing as TX power decreases.

- [All 65 settings as a Markdown table](cycle0_distance_rssi.md).
- [All 65 settings as CSV](cycle0_rssi_by_tx_setting.csv).
- [Every individual reading/error](measurements.csv).
- [Raw BLE records](init.log).
- [All observed groups](rssi_by_tx_setting.csv) and [JSON](rssi_by_tx_setting.json).
- [Layout](layout.json), [source/image provenance](provenance.json),
  [validation](validation.json), and [transport metadata](capture.json).

The full first cycle completed **3769/3900** exchanges:
65 settings, three peers, 20 attempts each. The complete timed capture contains
4031 attempts and 3818 completions, including
part of the next cycle. All attempts remain in the files.

| Role | Serial |
|---|---|
| Initiator | 760201915 |
| Peer 0 | 760201778 |
| Peer 1 | 760204734 |
| Peer 2 | 760204645 |

All readings came through BLE F1:FB:C0:BC:DB:75. Responders reply at FEFEFEFE;
only initiator Poll/Final power sweeps. No serial measurement capture was used.
The user reports opposite-facing anchors; exact angles and tape distances were
not supplied. The initiator differs from the earlier LOS experiment.

Distances in measurements.csv are millimetres; comparison tables use metres.
RSSI is an uncalibrated corrected dB estimate. Statistics include valid successful
frames only; failed attempts have no invented RSSI/distance. NA is missing data,
not zero power. No smoothing or RSSI-based sorting was applied.

See the [experiment report](../../../opposite_facing_ascending_sweep_20261114.md)
and [source guide](../../../../samples/twr_checked_ascending_common/README.md).
