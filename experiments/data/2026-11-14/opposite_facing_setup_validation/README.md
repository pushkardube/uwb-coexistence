# Opposite-facing sweep setup validation — 2026-11-14

Initiator 760201915, BLE F1:FB:C0:BC:DB:75. Responders:
0=760201778, 1=760204734, 2=760204645. Protocol 4, 65 settings,
20 attempts per peer per setting; fixed FE responder replies.

30-second BLE-only setup check: 168 attempts, 148 completed. At initial
01010101, peers 0 and 2 completed 20/20 each, peer 1 completed 0/20.
At FEFEFEFE all three completed 20/20. The remaining records are a partial
FA setting. No reported BLE sequence gaps, duplicates or queue drops.
This is a setup check, not a complete orientation-comparison experiment.

[Readings](measurements.csv), [raw BLE log](init.log),
[comparison](rssi_by_tx_setting.csv), [capture metrics](capture.json),
[validation](validation.json).
