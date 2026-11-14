# Independent checked-ranging experiments: bench record

Date: 2026-11-11. Board: DWM3001CDK / nRF52833 / DW3000.
Toolchain: Zephyr through nRF Connect SDK 3.2.4 and west; nrfutil flash runner.

These are independent forks of the checked two-board baseline:

- [Power sweep](../samples/twr_checked_power_common/README.md).
- [Addressed multiple responders](../samples/twr_checked_multi_common/README.md).

Neither fork edits the baseline implementation or incorporates the other fork.
All baseline source hashes were checked against `build/checked_pair_manifest.json`.

## Build and host validation

`bash tools/build_checked_variants.sh all` built five images successfully:
power initiator, power responder, multi initiator, multi responder 0, and multi
responder 1. The final build log `build/checked_variants_final_build.log` contained
no `warning:` or `error:` diagnostics. Image hashes and actual compiler commands
are in `build/checked_variants_all_manifest.json`.

An initial sysbuild override did not reach the responder compiler. The build
helper caught both images being ID 0 before flashing. Application CMake now
uses `zephyr_get()` for the settings, and the final compile commands explicitly
verify ID 0 versus ID 1 and initiator versus responder. Different build folders
alone do not guarantee different IDs.

Host checks passed for the attempt-based level schedule, valid coarse/fine
gain ladder, DGC correction and invalid sentinel, and peer rotation. Analyzer
checks cover reset boundaries, failed peer attempts, and refusing to claim an
endpoint power trend from an incomplete ladder. Shell syntax checks passed.

```bash
cc -std=c99 -Wall -Wextra \
  -Isamples/twr_checked_power_common -Isamples/twr_checked_multi_common \
  tools/test_checked_variants.c -o /tmp/test_checked_variants
/tmp/test_checked_variants
```

## Power sweep: visible in received RSSI

Programmed and verified only these selected probes:

| Role | Probe |
|---|---|
| Initiator | 760201778 |
| Fixed-power responder 0 | 760201915 |
| Third connected board, unchanged | 760204734 |

Flash logs: `build/power_flash.YDWevMak/`. Raw UART and machine-readable
summary: `build/power_capture_20261111_145153/`. Capture duration: 85 seconds
after resetting with both serial ports already open. The analyzer excludes
buffered records before the latest application startup.

There were **490 consecutive attempt records**, sequences 1–490, and **488
complete exchanges (99.59%)**. Both incomplete exchanges returned radio error
code 2, at levels FE and BE in cycle 1. No interval/range errors, fatal/guard
reports, or dropped-log reports appeared in the analyzed run. Every completed
exchange returned valid diagnostics. Two full sweeps and part of a third were
captured (24 completed level summaries).

| TX octet, repeated four times | Attempts | Completed | Median DGC-corrected RSSI (dB) | Median reported range (mm) |
|---|---:|---:|---:|---:|
| FE | 60 | 59 | -64.525 | 390 |
| DE | 60 | 60 | -64.735 | 382.5 |
| BE | 60 | 59 | -65.370 | 376 |
| 9E | 60 | 60 | -66.574 | 382.5 |
| 7E | 60 | 60 | -68.132 | 385 |
| 5E | 60 | 60 | -69.757 | 388.5 |
| 3E | 50 | 50 | -72.361 | 379.5 |
| 1E | 40 | 40 | -79.874 | 367 |
| 02 | 40 | 40 | -85.269 | 400.5 |

Median corrected RSSI decreased monotonically across the nine tested levels;
the endpoint difference was **20.744 dB**. All successful reported distances
were 314–432 mm. Absolute physical separation and antenna calibration were
not supplied, so the evidence establishes a relative received-strength trend
with stable reported ranging at the current geometry.

The low-power level still completed 40/40 exchanges. This geometry did **not**
reach a reception cliff. A later spatial test needs several receiver positions
and numbered one-way frames to measure their PRR. The two radio errors occurred
away from the lowest setting and are not evidence of a low-power cutoff.

The corrected estimate includes the vendor-model `+6*D` term. Both the original
estimate and raw C/N/D remain in the log. Individual corrected samples still
show gain-state outliers; use distributions and repeated sweeps rather than
claiming precise calibrated dBm from a single observation.

## Multi-responder: two-board partial validation

The two-board restriction is retained. Concurrent testing with two responders
requires a third programmed board and is not established by these results.

With responder 0 present and responder 1 absent, the 35-second capture
`build/multi_capture_20261111_145422/` contains 184 consecutive attempts.
Targets alternate correctly between 0 and 1. Peer 0 completed **92/92** exchanges,
all with valid RSSI; absent peer 1 completed **0/92**, returning radio timeout/error
code 2. Every absent-peer attempt was followed by successful service of peer 0.
Reported peer-0 range: median 366.5 mm, minimum 250 mm, maximum 407 mm.
No fatal errors or log drops were detected. Flash logs:
`build/multi_flash.s5KES1H7/`.

The same second physical board was then programmed as responder ID 1, leaving
the third board unchanged. Capture `build/multi_capture_20261111_145629/` also
contains 184 consecutive attempts over 35 seconds. Present peer 1 completed
**92/92** with all diagnostics valid; absent peer 0 completed **0/92** with
the expected code 2. Peer-1 reported range: median 375 mm, minimum 274 mm,
maximum 432 mm. Targets alternated throughout, without fatal errors or dropped
logs. Its flash verification log is `build/multi_peer1_flash.log`.

These runs validate both responder-ID builds, strict address selection,
separate counters, and recovery after missing peers. They do **not** validate
two responders operating concurrently or a powered responder being unplugged
mid-run. Those remain the next hardware checks when a third board is available
for programming.

## Final hardware state and next merge gate

After these tests, the two selected boards were returned to the tested
power-sweep images. Initiator probe 760201778 sweeps; responder probe 760201915
stays fixed-power, ID 0. Probe 760204734 was never programmed by this work.

Before merging, test multi-responder with both peers present, then remove and
restore one peer and check that the other continues receiving service. Retain
raw C/N/D when adding corrected RSSI to that version. Only then combine the
attempt-based sweep with per-peer measurements; use separate numbered one-way
bursts to evaluate the intended receiver's PRR versus the next receiver's PRR.
