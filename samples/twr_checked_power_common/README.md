# Checked DS-TWR: independent transmit-power sweep

This experiment forks the working `twr_checked_common` two-board baseline.
It is separate from both that baseline and the multi-responder experiment.
The applications are `../twr_checked_power_init` and `../twr_checked_power_resp`.
See [the baseline notes](../twr_checked_common/README.md) for timestamp handling,
frame lengths, error codes, GPIO overlay fixes, and diagnostic ordering.

## What it measures

The initiator changes its own TX power before sending each Poll. That setting
also applies to its Final. The responder measures the received Final, after
saving the ranging timestamp, and returns RSSI and raw diagnostics in Result.
The responder's TX power stays fixed at `0xFEFEFEFE`; its Response and Result
therefore do not sweep. This tests the direction needed for the later experiment:
power at board 1 versus received strength at a downstream board.

The level order is `FE DE BE 9E 7E 5E 3E 1E 02`. Each octet is repeated across
the four TX_POWER bytes. Coarse gain stays at 2 while fine gain decreases from
63 to 0. These are register settings, not calibrated dB or dBm steps.
`PGdly=0x34`, `PGcount=0`, channel 9, preamble 128, code 9, 6.8 Mb/s, STS off.

Each level lasts **20 attempted exchanges**, then advances even if every
exchange failed. Nine levels form a cycle; cycles repeat indefinitely. There
is a 150 ms pause after each exchange. The compile-time `SWEEP_ATTEMPTS` setting
accepts 1–10000; build with a separate directory when changing it.

## RSSI fields

- `final_rssi_mdB`: unchanged baseline estimate,
  `1000 * (10*log10(C*2^21/N^2)-121.7)`.
- `rssi_dgc_mdB`: that estimate plus `6000*D`, where D is the receiver's
  dynamic-gain-control decision. Use this for the primary sweep comparison.
- `C`, `N`, `D`: raw CIR power, accumulation count, and DGC decision. Keep them
  so surprising changes can be investigated rather than hidden by averaging.
- `diag=1`: valid diagnostics. Invalid RSSI is `-2147483648`.

The DGC term follows the local vendor reference
`COSIC/SDK/Firmware/DW3_QM33_SDK_1.1.1/Libs/dwt_uwb_driver/deca_rsl.c`,
`rsl_calculate`: `10*log10(C*2^Q/N^2)+6*D-A`; DW3000 uses Q=21.
The old estimate lacks the gain correction, so raw RSSI can move in a
surprising direction when receiver gain changes. Both fields remain approximate
and uncalibrated. A visible trend does not establish absolute emitted power.

## Build, flash, capture

Run from the repository root:

```bash
bash tools/build_checked_variants.sh all
bash tools/flash_checked_variant.sh power 760201778 760201915
python3 tools/capture_checked_variants.py --variant power \
  --init 760201778 --responder 760201915 --seconds 85 --reset
```

The build helper uses west, NCS 3.2.4, and separate directories
`build/checked_power_init` and `build/checked_power_resp`. It checks compiled
roles and writes image hashes to `build/checked_variants_all_manifest.json`.
The flash helper checks those hashes and the selected live probe IDs, then
uses `west flash --skip-rebuild -r nrfutil`, responder first, initiator last.
Only the two explicitly selected boards are programmed.

For a manual custom build after sourcing `tools/ncs_env.sh`:

```bash
west build -b decawave_dwm3001cdk samples/twr_checked_power_init \
  -d build/checked_power_init_custom -- -DSWEEP_ATTEMPTS=40
```

Application CMake uses `zephyr_get()` to propagate settings through sysbuild.
Checking only the parent CMake cache is insufficient: inspect the actual
`checked.c` compile command when building a custom configuration.

UART is 115200 with DTR asserted. Measurement records start with `POWER seq=`.
Every record includes `cycle`, `level`, and `octet`, including errors.
`POWER_LEVEL` records summarize a completed 20-attempt level. A capture can
end halfway through a level; its host summary includes that partial group.

```bash
python3 tools/analyze_checked_variants.py build/<capture>/init.log \
  --json build/<capture>/analysis.json --csv build/<capture>/measurements.csv
```

The analyzer reports completion counts, per-level RSSI medians and means,
distance spread, sequence gaps, fatal errors, and dropped logs. Compare repeated
cycles at a fixed geometry; individual samples can fluctuate with gain state
and multipath. Read the [bench record](../../experiments/checked_variants_bench.md)
for actual results and limitations.

## Protocol and scope

The header uses protocol **version 2** (`C7 51 02 ...`). Layout and DS-TWR
ordering otherwise match the checked baseline. Version 1 baseline and version 3
multi firmware are intentionally rejected, so flash a matching pair.

Exchange completion is **four-frame DS-TWR completion**, not one-way packet
reception ratio. An error cannot identify which direction or frame was lost.
The experiment does not choose a cutoff board or automatically converge on a
power. Those features require the later combined experiment and numbered
one-way bursts observed at every receiver.

## C implementation walkthrough

See [the checked protocol/source guide](../CHECKED_PROTOCOL.md) for the
function map, timestamp ownership, frame layout, diagnostic ordering, guards,
and differences among these independent implementations. The
[sample index](../README.md) links every role and its validation record.
