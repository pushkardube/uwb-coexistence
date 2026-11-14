# Build, flash, capture and analysis tools

Run commands from the repository root. These helpers support distinct firmware
families; their manifests and build-directory names are not interchangeable.
See [the firmware index](../samples/README.md) and [FLASHING.md](../FLASHING.md).

## Environment: ncs_env.sh

`source tools/ncs_env.sh` selects NCS 3.2.4 and toolchain bundle 2ac5840438
under `~/ncs`. It changes PATH, library paths, Python environment, Zephyr SDK
paths and NRFUTIL_HOME. It is meant to be **sourced**, not run as a child process.
Build/flash helpers source it internally. Host capture tools use system Python;
a fresh shell avoids leaking the SDK's PYTHONHOME/PYTHONPATH into those tools.
The paths describe this machine and need updating on another installation.

## Bluetooth telemetry without USB data connections

```bash
bash tools/build_checked_ble.sh 1 20
bash tools/flash_checked_variant.sh ble 760201778 760201915
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py --seconds 300
```

The BLE builder creates a dedicated BLE initiator and plain checked UWB
responders in checked_ble_* directories and verifies their roles/configuration
and hashes in checked_variants_ble_manifest.json. Default is one responder,
20 attempts per setting. It does not alter the plain combined build directories.
The flash helper accepts ble as a variant and uses explicitly listed probes.

collect_checked_ble.py requires Bleak, a powered Bluetooth adapter and the
UWB-COEX-INIT peripheral. It does not open any serial ports. It subscribes to
NUS TX, sends START, reassembles arbitrary fragments, writes complete records,
and acknowledges boot/record IDs over NUS RX. Replayed records are acknowledged
again without duplicating measurements. Unexpected disconnects trigger RESUME
on reconnect; the sweep pauses when the link is absent or its queue backs up.

Options include --address, --name, --scan-seconds, --seconds, --resume, --quiet
and --out NEW_DIRECTORY. A normal timed stop sends PAUSE and STATUS. Outputs:
init.log, measurements.csv, capture.json and summary.json. Capture metadata
contains connection/command history, sequence gaps, duplicates, framing errors,
transport replays and maximum reported queue drops. Existing analysis and
complete-cycle map tools accept its init.log.

Only the initiator needs Bluetooth range to the laptop. The responder sends
diagnostics over UWB and can use external USB power. Read
[the complete guide](../samples/twr_checked_ble_common/README.md) and
[the bench record](../experiments/checked_ble_bench.md). The old
collect_spatial.py expects a different data schema and does not implement the
acknowledged checked-telemetry protocol.

test_collect_checked_ble.py exercises byte fragmentation/coalescing, reconnect
tails, bounded framing, gaps/duplicates, and transport replay deduplication.

## Current combined firmware

For the separate **continuous 01010101** range experiment, build with
`bash tools/build_checked_fixed01.sh` and flash with
`bash tools/flash_checked_variant.sh fixed01 INIT_SERIAL RESP0_SERIAL RESP1_SERIAL`.
The initiator and both version-5 responders always transmit at 01010101.
Use `collect_checked_ble.py` for file capture; the analyzer validates
the fixed-power banner and single-level schedule. See
[the fixed01 guide](../samples/twr_checked_fixed01_common/README.md).

For one BLE initiator and three responders, use
[collect_three_responder_rssi.py](collect_three_responder_rssi.py). It retains
the individual reading CSV and exports a side-by-side distance/RSSI table for
all three peers at each TX setting and cycle. See
[the three-responder capture guide](THREE_RESPONDER_RSSI.md) for the board
mapping, commands, output fields and missing-data semantics.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py --seconds 720
```

The initiator must already be built for three targets. This collector does not
flash hardware or change the configured peer count. Run
`python3 tools/test_collect_three_responder_rssi.py` for its host checks.

```bash
# Two responders, 10 attempts per peer per setting:
bash tools/build_checked_combined.sh
# Example: four responders, 20 attempts per peer per setting:
bash tools/build_checked_combined.sh 4 20
```

The builder accepts 1–16 responders and 1–10000 attempts per peer per setting.
It builds `checked_combined_init` plus `checked_combined_resp0..N-1`, verifies
actual compiler role/ID/count/dwell definitions, hashes merged.hex images, and
writes `build/checked_variants_combined_manifest.json`. The level count is read
from combined_plan.h: currently **65**, starting with 01010101 then FE..02.
Responders keep fixed FEFEFEFE reply power. It does not flash hardware.

```bash
bash tools/flash_checked_variant.sh combined 760201778 760201915 760204734
```

The first serial is initiator; following serials map to responder IDs 0, 1,
and onward. The helper requires distinct live SEGGER probes and matching hashed
artifacts before programming. It uses west/nrfutil, responders first and
initiator last, with `--skip-rebuild`. It programs only explicitly listed probes.
Fewer serials do not change the initiator's compiled target count, and do not
stop an omitted board from responding if it already has compatible firmware.

Flash logs and target assignments are saved in a unique `build/<variant>_flash.*`
directory. Successful programming verifies bytes, not RF behavior.

## Independent checked variants

```bash
bash tools/build_checked_variants.sh all
bash tools/build_checked_variants.sh power
bash tools/build_checked_variants.sh multi
```

`all` here means the **five standalone power/multi images**, not the combined
65-setting application. Power builds checked_power_init/resp; multi builds
checked_multi_init/resp0/resp1. Each selected family gets a manifest; the `all`
manifest contains all five images. The flash helper chooses the latest applicable
manifest and verifies the needed image hashes.

```bash
bash tools/flash_checked_variant.sh power INIT_SERIAL RESP_SERIAL
bash tools/flash_checked_variant.sh multi INIT_SERIAL RESP0_SERIAL RESP1_SERIAL
```

Power accepts one responder. Multi accepts one or two listed responders, while
its supplied initiator build still targets two. Protocol versions differ between
these variants, so switching firmware requires a matching set.

## Capture: capture_checked_variants.py

Requires system Python with PySerial. Example for the current three boards:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/capture_checked_variants.py \
  --variant combined --init 760201778 --responder 760201915 \
  --responder 760204734 --seconds 60 --reset
```

Options: variant power/multi/combined; one initiator; repeatable --responder;
positive --seconds; optional --out for a new directory; optional --reset.
It opens the selected `/dev/serial/by-id/usb-SEGGER_J-Link_<12-digit-ID>-if00`
ports exclusively at 115200, asserts DTR and records bytes. `--reset` resets
only selected responders and then initiator through nrfutil, with UART already
open. The timed interval starts after those commands. Existing serial consumers
must release the ports. The selected variant labels the capture directory; it
does not inspect, build or change the firmware to match that label.

Outputs are init.log, resp0.log, resp1.log etc., capture.json and summary.json.
The responder log suffix is the **argument position**, not a discovered peer ID.
The script prints progress every 25 seconds and closes ports on completion.
Use a longer window for an entire sweep; the 01 probe lasts only its initial
20 attempted exchanges under the default two-peer configuration.

## Analyze: analyze_checked_variants.py

```bash
python3 tools/analyze_checked_variants.py build/<capture>/init.log \
  --json build/<capture>/analysis.json --csv build/<capture>/measurements.csv
```

This tool uses only the standard library. It strips ANSI control sequences,
selects the latest captured application-ready marker, and parses POWER/MULTI/
COMBINED records. Unterminated trailing UART fragments are ignored rather than counted as attempts
or radio failures. Errors remain attempts. It reports sequence continuity,
completion counts, error-code counts, RSSI/range summaries, fatal-text detection
and dropped-log markers from the **input log**. The capture helper supplies the
initiator log; responder logs must be reviewed separately for their own errors.

Combined output groups by peer and level; cycles_seen records which cycles
contributed, but the statistics pool repeated visits to a level. The 65-setting
configuration reports probe_01010101 separately and compares FE..02 endpoints
only after the 64-entry coarse-2 ladder has appeared. It supports the earlier
64-setting captures as well. Schedule verification depends on the ready marker's
target count, level count and dwell budget: use --reset when capturing the new
65-setting schedule. Without startup configuration, it defaults to historical
64-level interpretation and cannot verify the schedule.

RSSI statistics exclude invalid diagnostic/sentinel samples. Partial final
levels remain partial; success-only RSSI distributions do not include lost
packets. Printed status masks lack a 0x prefix; an all-digit status token can
be parsed as decimal by the generic numeric parser. Use the raw UART hex token
when decoding SYS_STATUS bits. The CSV is a measurement export, not a register
decoder or a one-way PRR result.

## Complete-cycle TX-power/RSSI table: export_power_rssi_map.py

This exporter turns one complete COMBINED sweep at a selected receiver into
Markdown, CSV and JSON. It supports the historical 64-setting schedule and the
current 65-setting schedule, including the separate 01010101 probe. Unlike a
pooled summary, it selects a single cycle so a partial later cycle cannot give
some power settings more samples than others.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/export_power_rssi_map.py \
  build/<capture>/init.log --peer 0 --cycle 0 \
  --out-prefix experiments/tx_power_rssi_mapping_UNIQUE_RUN
# Add --physical-distance-m 1.5 only when that antenna separation was measured.
```

The log must include a startup configuration and matching observed schedule.
Every selected level must have the compiled number of attempted-exchange rows;
incomplete sweeps are rejected. Failed exchanges stay in the denominator, while
range/RSSI statistics use completed/diagnostic-valid measurements. Output records
the full repeated-byte register, coarse/fine codes, counts, corrected RSSI
median/mean/min/max, legacy RSSI median, reported range spread and error counts.
Existing result files are not overwritten: choose a new prefix per dataset.

Without a supplied physical measurement, reports explicitly call distance a
UWB-reported range. Keep the setup fixed and record orientation/PHY; this table
is an empirical map for that condition, not a universal register-to-RSSI law.
No firmware is built or flashed by the exporter.

## Sort and check the power/RSSI trend: check_power_rssi_trend.py

This tool reads the JSON produced by export_power_rssi_map.py. It preserves
measured values and original acquisition levels, sorts the supported ladder
by nominal increasing gain, and writes Markdown, CSV and JSON with adjacent
RSSI differences, reversal listings and Spearman rank correlations. It supports
coarse-2 fine codes with the optional coarse-1/fine-0 probe, and rejects arbitrary
mixed-coarse maps whose physical order is not established by that rule.

First export one peer from the published full LOS capture:

```bash
python3 tools/export_power_rssi_map.py \
  experiments/data/2026-11-13/los_three_responders_run1/init.log \
  --peer 0 --cycle 0 --out-prefix build/los_peer0_map
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR="$PWD/build/.matplotlib" \
  python3 tools/check_power_rssi_trend.py \
  build/los_peer0_map.json \
  --out-prefix build/los_peer0_increasing_power --plot
```

The --plot option requires Matplotlib and creates a standalone PNG showing
median RSSI, observed sample min/max and adjacent changes. The shaded sample
range is not a confidence interval. Without --plot, the tool uses only the
Python standard library. Existing result prefixes are not overwritten.

It orders settings using coarse/fine fields, never by measured RSSI. It does
not smooth values, calibrate emitted dBm, reflash boards or run a new ascending
sweep. Small reversals are retained; descriptive correlation does not establish
their cause or prove perfect monotonicity. The published
[LOS run report](../experiments/los_three_responder_rssi_20261113.md) links the
raw three-peer evidence; the commands above derive a separate single-peer map.

## Historical local helpers

Older alternating-session build/flash helpers are outside this published
snapshot. Use the checked combined, BLE or fixed01 commands above for the
applications in [the published sample index](../samples/README.md).

## BLE collector: collect_spatial.py

This is for spatial_resolution_rx, not CHECKED/POWER/MULTI/COMBINED UART logs.
It requires Bleak and a functioning local Bluetooth adapter.

```bash
mkdir -p captures/spatial
python3 tools/collect_spatial.py --name DWM3001-RX --csv captures/spatial/run1.csv --duration 120
# Or select explicit receiver addresses, skipping discovery:
python3 tools/collect_spatial.py --addr AA:BB:CC:DD:EE:FF --csv captures/spatial/run2.csv
```

It scans by name prefix (default eight seconds), connects concurrently to
receivers, subscribes to NUS TX, and converts six integer notification fields
into wall_time,device,epoch,pos,received,N,prr_pct,rssi_db CSV. Epoch is only
eight-bit. The output file is opened for writing, so use a new filename per run.
Callbacks split notifications into lines but do not reassemble a CSV line split
across multiple notifications. Connection errors are printed without an automatic
reconnect loop. Neither missing rows nor a completed collector timer proves
zero UWB reception.

## C and Python host checks

| File | Purpose |
|---|---|
| samples/twr_checked_common/test_math.c | Independent clock epochs, timestamp wrap, interval rejection and LE serialization |
| tools/test_checked_variants.c | Nine-setting ladder, attempt-driven advance, DGC handling, peer rotation |
| tools/test_checked_combined.c | Initial 01 plus 64 gain codes, equal peer budgets, cycle wrap, fixed reply power |
| tools/test_analyze_checked_combined.py | Peer/level separation, missing peers, reset boundaries, partial captures and 64/65-level interpretation |

```bash
cc -std=c99 -Wall -Wextra samples/twr_checked_common/test_math.c -lm -o /tmp/checked_math
/tmp/checked_math
cc -std=c99 -Wall -Wextra -Isamples/twr_checked_power_common -Isamples/twr_checked_multi_common tools/test_checked_variants.c -o /tmp/checked_variants
/tmp/checked_variants
cc -std=c99 -Wall -Wextra -Werror -Isamples/twr_checked_combined_common tools/test_checked_combined.c -o /tmp/checked_combined
/tmp/checked_combined
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_analyze_checked_combined.py
```

These validate host-side math/schedules/parsing; hardware captures separately
establish packet exchange, returned diagnostics and observed range stability.
