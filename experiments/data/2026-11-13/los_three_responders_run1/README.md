# LOS three-responder Bluetooth capture — 2026-11-13

All measurements were received through BLE NUS from initiator 760201778.
No serial ports were opened. Responders send their diagnostics over UWB.

User-reported layout: all boards in a line, LOS, approximately 1 m apart.
Exact tape distances were not supplied. UWB-reported near-to-far order is
peer 2 (760204645), peer 1 (760204734), peer 0 (760201915).
Peer 0 was absent from this laptop's USB inventory and returned data through
the initiator, consistent with its separate power supply.

- [All individual readings](measurements.csv): 4072 attempt records.
- [Complete first-cycle comparison](cycle0_rssi_by_tx_setting.csv): exactly 65 rows,
  20 attempts per peer at every setting; 3898/3900 exchanges completed.
- [All observed comparison groups](rssi_by_tx_setting.csv): includes the partial next cycle.
- [Raw decoded BLE log](init.log).
- [Acquisition and BLE transport metrics](capture.json).
- [Per-peer analysis](summary.json).
- [Layout](layout.json), [source/image provenance](provenance.json),
  and [validation checks](validation.json).

The run used three responders, 65 TX settings and 20 attempts per peer/setting.
All RSSI values are uncalibrated DGC-corrected estimates in dB. Distances in the
individual CSV are millimetres; comparison distances are metres. Blank
comparison cells mean missing data. Error records remain failed attempts.
A complete cycle has 3900 attempts; the extra records start the next cycle.

Reproduce from the repository root, choosing a new output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --seconds 720 --address CB:56:11:3C:AB:ED --out experiments/data/NEW_RUN
```

The complete-cycle CSV is the existing comparison table filtered to cycle=0;
no smoothing, power reordering or measurement changes were applied.
