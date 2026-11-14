# Fixed 01010101 in both link directions

Date: 2026-11-14. The user requested 01010101 on the responders as well as the
initiator. This supersedes the active fixed01 setup's strong-reply setting;
the [2026-11-13 FE-reply result](fixed01_range_test_20261113.md) remains historical.

## Configuration

| Role | Serial | Transmitted frames | TX_POWER |
|---|---|---|---|
| BLE initiator | 760201778 | Poll and Final | 0x01010101 |
| Responder 0 | 760204734 | Response and Result | 0x01010101 |
| Responder 1 | 760204645 | Response and Result | 0x01010101 |

Protocol remains version 5. The frame format, radio PHY, timing and RSSI
calculation are unchanged. The responder power macro now aliases the fixed
initiator octet, preventing the two settings from drifting apart. The ready
banner formats both power words from those macros instead of hardcoding them.
The separately powered protocol-4 responder 760201915 is not programmed.

The same initiator board is retained and its TX power remains 01. Its image is
refreshed so its startup banner also reports the new responder reply setting.
Two responders still alternate, with 20 attempts per peer per reporting window.

## Build, flash and checks

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 760201778 760204734 760204645
```

The fixed-power host test passed across 10000 attempts, including an assertion
that the responder power word is 01010101. Three fixed-mode analyzer tests and
the build-script syntax check passed. Build log:
`build/checked_fixed01_both01_build_20261114.log`.

The builder records actual compiler role/ID selections and image hashes in
`build/checked_variants_fixed01_manifest.json`. Flash and BLE validation results
are appended after programming and measurement complete.

## Capture over BLE

```bash
python3 tools/collect_checked_ble.py --seconds 3600 \
  --address CB:56:11:3C:AB:ED \
  --out experiments/data/fixed01_both_directions_NEW_RUN
```

All four ranging messages now use low power. Full exchange completion can
therefore be limited by either direction. RSSI still measures Final at the
responder; adding an initiator-side diagnostic read was not part of this change.
Keep failed attempts as errors, not zero RSSI. Distances are UWB-reported and
RSSI is an uncalibrated DGC-corrected estimate in dB.

## Programming and BLE result

Both responders and the same initiator were successfully programmed and verified
with west/nrfutil. Flash log: `build/checked_fixed01_both01_flash_20261114.log`;
per-board logs: `build/fixed01_flash.cEuyTDj3/`.

A 30-second BLE-only capture confirmed both runtime power words as 01010101,
level 0 on every record, two active peers and the intended fixed schedule.
There were **172 consecutive attempts, 137 completed exchanges**, and valid
RSSI on all completed exchanges.

| Peer | Serial | Completed / attempts | Median reported range (m) | Median corrected RSSI (dB) |
|---|---|---:|---:|---:|
| 0 | 760204734 | 51/86 | 1.7580 | -92.322 |
| 1 | 760204645 | 86/86 | 0.7895 | -85.373 |

All 35 failures were peer-0 radio error code 2. There were no fatal reports.
BLE reported zero sequence gaps, duplicates, out-of-order records, framing
errors, discarded partial bytes, queue drops and replays. The individual CSV
matched the raw BLE log fields. Final STATUS showed running=0 and queue=0;
a new collector START begins the next test.

The short completion ratios describe the observed full ranging transactions;
they are not one-way PRR or a measured maximum range. The prior FE-reply trial
had a different capture window and is retained separately.

- [Individual readings](data/2026-11-14/fixed01_both_directions_validation/measurements.csv)
- [Raw BLE records](data/2026-11-14/fixed01_both_directions_validation/init.log)
- [Transport metadata](data/2026-11-14/fixed01_both_directions_validation/capture.json)
- [Summary](data/2026-11-14/fixed01_both_directions_validation/summary.json)
- [Image hashes and validation](data/2026-11-14/fixed01_both_directions_validation/validation.json)

## Original full sweep preserved

The user asked whether the tested full-sweep firmware remained intact. Its
combined core/header/plan and BLE telemetry source hashes were compared against
`experiments/data/2026-11-13/los_three_responders_run1/provenance.json` and
matched exactly. All four saved `build/checked_ble_*/merged.hex` images also
matched their original recorded hashes. Re-analyzing the saved LOS sweep
produced an identical summary.

The fixed experiment lives in `samples/twr_checked_fixed01_*` and
`build/checked_fixed01_*`; the sweep stays in `samples/twr_checked_combined_*`,
`samples/twr_checked_ble_*` and `build/checked_ble_*`. Host analysis has an added
fixed-mode branch, with unchanged results for the saved full sweep. The selected
physical boards now run the fixed variant; preserved sweep sources and images
can be used to restore the sweep later.
