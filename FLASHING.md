# Building and flashing the DWM3001CDK experiment

Updated 2026-11-14. Hardware is DW3000 UWB plus nRF52833, with on-board J-Link.
The working route here is **west → nrfutil**, using nRF Connect SDK 3.2.4.
This guide distinguishes the current checked firmware from preserved legacy apps.
See [the sample index](samples/README.md) and [tool details](tools/README.md).

## Current opposite-facing sweep setup

For the requested **ascending acquisition**, use the independent build:

```bash
bash tools/build_checked_ascending.sh
source tools/ncs_env.sh
export NRFUTIL_HOME="$PWD/build/.nrfutil"
west flash --skip-rebuild -d build/checked_ascending_init -r nrfutil --dev-id 760201915
```

The existing three responders remain compatible and their image hashes match
the builder's outputs. The BLE address and board mapping below are unchanged.
This variant visits 01,02,06,...,FE; the original restored build commands below
instead select 01,FE,FA,...,02. See
[the ascending run record](experiments/opposite_facing_ascending_sweep_20261114.md).

The restored protocol-4 sweep now uses this mapping:

| Role | Serial |
|---|---|
| BLE initiator | 760201915 |
| Responder 0 | 760201778 |
| Responder 1 | 760204734 |
| Responder 2 | 760204645 |

```bash
bash tools/build_checked_ble.sh 3 20
bash tools/flash_checked_variant.sh ble 760201915 760201778 760204734 760204645
python3 tools/collect_three_responder_rssi.py --seconds 720 \
  --address F1:FB:C0:BC:DB:75 --out experiments/data/opposite_facing_NEW_RUN
```

The initiator starts at 01010101, then sweeps FE..02 across all 64 fine-gain
codes at coarse 2. Replies stay at FEFEFEFE. One cycle is 3900 attempts.
The Bluetooth address is for the new physical initiator; do not use the old
760201778 initiator's address. See
[the orientation-repeat record](experiments/opposite_facing_sweep_20261114.md).

## Previous fixed-01010101 range test

The earlier fixed01 experiment uses independent protocol-5 firmware:

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 760201778 760204734 760204645
python3 tools/collect_checked_ble.py --seconds 3600
```

760201778 remains the BLE initiator. Fixed01 responder IDs 0 and 1 are
760204734 and 760204645 respectively. The initiator always uses 01010101;
the responders also reply at 01010101. They can use external power after flashing.
See [the fixed01 guide](samples/twr_checked_fixed01_common/README.md) for
logging commands and [the bench record](experiments/fixed01_both_directions_20261114.md).
At that time 760201915 retained its earlier protocol-4 responder. It has since
been programmed as the new sweep initiator in the setup above.

## Bluetooth host interface for the earlier sweep

For the BLE-enabled initiator and the currently connected two boards:

```bash
bash tools/build_checked_ble.sh 1 20
bash tools/flash_checked_variant.sh ble 760201778 760201915
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py --seconds 300
```

The BLE initiator advertises UWB-COEX-INIT and waits for subscription plus
START/RESUME. UART monitoring by itself does not start this variant's sweep.
The collector provides acknowledged data transfer and control over Bluetooth;
neither board needs a USB data connection after flashing, but both need power.
The plain combined workflow below is preserved as the UART-only alternative.
Read [the BLE guide](samples/twr_checked_ble_common/README.md) for commands,
external-power operation and reconnect behavior.

## Earlier three-board sweep setup

| Probe serial | Role | Build directory |
|---|---|---|
| 760201778 | Combined initiator, targets peers 0 and 1 | build/checked_combined_init |
| 760201915 | Combined responder 0 | build/checked_combined_resp0 |
| 760204734 | Combined responder 1 | build/checked_combined_resp1 |

The current firmware starts at **0x01010101**, then visits all 64 FE..02
fine-gain codes at coarse gain 2. Each peer gets 10 attempts per setting;
responder replies remain FEFEFEFE. All three boards have been programmed.
The exact probe/position mapping should be checked again when wiring changes.

```bash
cd ~/Georgia_Tech/uwb-coexistence
bash tools/build_checked_combined.sh
bash tools/flash_checked_variant.sh combined 760201778 760201915 760204734
```

The helper builds separate images, verifies compiler role/ID/count settings,
records hashes, then flashes only explicit targets after checking their live
presence and image hashes. Responders are flashed first, initiator last.
Building alone does not flash. The flash helper intentionally does not rebuild.

For a different peer count/dwell budget:

```bash
bash tools/build_checked_combined.sh 4 20
# Then explicitly supply initiator and the intended responder serials.
```

The board count is compiled into the initiator. Omitting a serial from a flash
command does not remove that ID from its schedule, and does not stop omitted
compatible hardware already running. Duplicate responder IDs can create
simultaneous replies; verify both compiled ID and physical probe selection.

## Environment and artifact locations

For manual west commands:

```bash
source tools/ncs_env.sh
export XDG_CACHE_HOME="$PWD/build/.host_cache"
export CCACHE_DIR="$PWD/build/.ccache"
mkdir -p "$XDG_CACHE_HOME"
```

The script selects the machine's NCS 3.2.4 installation and toolchain bundle
2ac5840438. It changes Python environment variables as well; use a fresh
system-Python shell for UART capture. Helpers source the build environment
internally. Their nrfutil runtime can use the writable build/.nrfutil directory;
manual commands can select it with:

```bash
export NRFUTIL_HOME="$PWD/build/.nrfutil"
```

That directory must contain a working nrfutil device installation, not just be
an empty folder. The legacy split-flash helper can seed it from the SDK runtime.
Do not assume every unrelated SDK/tool installation has the same paths.

With the current sysbuild layout:

- Flash image: build/<name>/merged.hex.
- Application ELF: build/<name>/<project>/zephyr/zephyr.elf.
- Actual compiler commands: build/<name>/<project>/compile_commands.json.
- Build/helper manifests: build/checked_variants_*_manifest.json.

## Separate directories and verified overrides

Keep one build directory per role, responder ID and comparison configuration.
For example, the standalone checked experiments use:

```bash
bash tools/build_checked_variants.sh all
# Produces five power-only/multi-only images, not the combined application.
```

For legacy split alternation, the corresponding helper is:

```bash
bash tools/build_split_twr.sh
```

These produce different protocols and manifests. Read the matching sample guide
before substituting a directory name.

A role defined unconditionally inside C is not reliably overridden by adding
-DROLE on the command line: the source redefinition can win. Edit that source
before building or use the newer fixed-role applications. The legacy split
responder's #ifndef RESPONDER_ID supports EXTRA_CFLAGS overrides; most older
combined-role samples do not guard every setting.

Sysbuild adds another boundary: a setting visible in the parent CMake cache may
not reach the application compiler. Newer checked power/multi/combined CMake
files use zephyr_get(). The original checked baseline lacks that forwarding;
only its tested defaults are established here. Inspect the actual checked.c
compiler command before claiming a diagnostic-off or alternate-ID control.

ELF strings are useful for role sanity, but a format string such as id=%u does
not reveal its compiled numeric argument. The current build helpers inspect
compiler definitions and hash the image. A parent cache entry by itself is not
proof of the final setting.

## Check live USB identities

```bash
ls -l /dev/serial/by-id/
# In an SDK-enabled shell:
nrfutil device list
```

SEGGER vendor ID is 1366 in sysfs. Check physical labels/USB paths when assigning
roles. Re-enumeration can change ttyACM numbering or listing order; that is not
proof that a physical probe's serial identity changed. Prefer the stable by-id
UART path and explicit numeric probe serial over a remembered ttyACM index.
Earlier notes conflated changing device assignments with changing serials.

## Manual programming of already verified images

```bash
source tools/ncs_env.sh
export NRFUTIL_HOME="$PWD/build/.nrfutil"
west flash --skip-rebuild -d build/checked_combined_resp0 -r nrfutil --dev-id 760201915
west flash --skip-rebuild -d build/checked_combined_resp1 -r nrfutil --dev-id 760204734
west flash --skip-rebuild -d build/checked_combined_init -r nrfutil --dev-id 760201778
```

Always select the actual intended probes. `--skip-rebuild` preserves the image
that was checked. A plain west flash may rebuild from current source first;
this repeatedly caused role confusion in older source-switched applications.
Initiator-last programming also provides a clean start once responders are ready.

A successful nrfutil run reports programming, verification and reset, ending in
Board(s) with serial number(s) ... flashed successfully. Save the log and board
mapping. Verification proves programming, not successful reception or credible
ranging. If a failure occurs after erase/programming starts, the previous image
may already be changed; do not assume every failed flash preserves it.

## Monitor and validate

UART is 115200, with DTR asserted. The current three-board capture command is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/capture_checked_variants.py \
  --variant combined --init 760201778 --responder 760201915 \
  --responder 760204734 --seconds 60 --reset
```

The capture tool opens ports before resetting responders and then initiator.
The initial 01 probe occupies 20 attempts, about a few seconds at this geometry.
Use a longer capture for an entire cycle; the default schedule has 1300 attempts.
Read the latest ready banner: targets=2, levels=65, attempts_per_peer=10.

Check that both peer IDs appear, sequences advance, diag is valid, and the
per-peer counters agree with logs. Code 2 can represent a radio timeout/error;
it is expected when a configured peer is absent, but still counts as failure.
A single healthy peer cannot establish concurrent multi-responder behavior.

Actual results and raw-log locations are in
[checked_combined_bench.md](experiments/checked_combined_bench.md). The 01 test
returned 10/10 at each peer; it does not imply every later geometry will receive.

## Failure diagnosis

| Symptom | First checks |
|---|---|
| No selected probes found | USB enumeration, cable/hub, live serials and environment device access |
| Probe readable in sysfs but programming denied | Actual USB device permissions and execution environment access |
| nrfutil cannot write runtime/log files | Correct writable NRFUTIL_HOME with installed device plugin |
| No UART records | Correct by-id path, DTR, baud, other process owning port, boot/reset state |
| Unsupported pin assertion | Effective overlay; inherited optional GPIO1.19 wakeup mapping |
| All peers time out | Matching protocol/PHY, one initiator, unique responder IDs and actual artifact roles |
| Only one peer fails | Its power/cable/ID/PHY/protocol and per-peer counters |
| RSSI always -80.0 | Legacy twr_multi isolation flag returns a constant |
| Strange or huge negative ranges | Frame lengths/association, modular intervals, CIA readiness, timing and raw timestamps |

Use `fuser /dev/ttyACM0` with the currently resolved port to check ownership.
A busy port may be an editor monitor; do not consume the same stream from two
readers and then interpret missing records as radio loss. Diagnose old RSSI
regressions with [the investigation](experiments/line_power_control_and_rssi_debug.md)
rather than assuming an unproven double-buffer mechanism.
