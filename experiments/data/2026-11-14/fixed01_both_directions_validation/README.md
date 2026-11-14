# Fixed 01010101 in both directions — 2026-11-14

Initiator: 760201778. Responders 0/1: 760204734 / 760204645.
All four DS-TWR frames use 01010101. Protocol 5; two peers; BLE-only data capture.

30-second validation: 172 attempts, 137 completed. Peer 0 completed 51/86,
peer 1 completed 86/86. All 35 failures were peer-0 radio error code 2.
The runtime banner reported tx_power=0x01010101 and reply_tx_power=0x01010101.
No reported BLE sequence gaps, duplicates or queue drops. The collector paused
normally at the timed end.

Files: [measurements.csv](measurements.csv), [init.log](init.log),
[capture.json](capture.json), [summary.json](summary.json),
[validation.json](validation.json).

The earlier FE-reply validation is in the 2026-11-13 data directory. The full
65-setting sweep firmware sources and all four built images retain their
original recorded hashes.
