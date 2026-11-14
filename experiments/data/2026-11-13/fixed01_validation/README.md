# Fixed 01010101 firmware validation — 2026-11-13

BLE-only capture, 60 seconds, two responders. Initiator 760201778 always sends
Poll and Final at 01010101. Responders reply at FEFEFEFE.

| Fixed01 peer | Serial | Completed / attempts |
|---|---|---:|
| 0 | 760204734 | 150/169 |
| 1 | 760204645 | 168/168 |

All 337 consecutive attempt records use octet 01 and level 0 across nine
reporting windows. There were 19 radio errors for peer 0 and no reported BLE
sequence gaps, duplicates or queue drops. The program was paused normally
at the end. This is a short setup validation, not a maximum-distance test.

Files: [measurements.csv](measurements.csv), [init.log](init.log),
[capture.json](capture.json), [summary.json](summary.json),
[validation.json](validation.json).

See the [experiment report](../../../fixed01_range_test_20261113.md) for the
firmware, build/flash commands, units and external-power test procedure.

## Reproduce the earlier FE-reply configuration

The current fixed01 firmware sends 01 in both directions. In a separate clean
checkout of this snapshot, apply [restore_FE_replies.patch](restore_FE_replies.patch)
before building. The patch restores the earlier responder setting, banner,
build-manifest setting and corresponding host assertion. Do not apply it to
an active both-directions experiment.

```bash
git apply --check experiments/data/2026-11-13/fixed01_validation/restore_FE_replies.patch
git apply experiments/data/2026-11-13/fixed01_validation/restore_FE_replies.patch
bash tools/build_checked_fixed01.sh
```

The restored firmware-source contents match every source hash recorded in
validation.json. This verifies the source snapshot; identical rebuilt binary
hashes also depend on the captured toolchain and build environment. The original
raw measurements and their validation metadata were not modified.
