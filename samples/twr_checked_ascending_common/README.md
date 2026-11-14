# Ascending 65-setting TX sweep

This independent copy of the checked combined core changes acquisition order
to **01, 02, 06, 0A, …, FA, FE**. Thus a full run starts at 01010101 and ends
at FEFEFEFE. It uses the same 65 settings as the original sweep. The original
combined/BLE sources and build directories remain intact.

Only `combined_plan.h` and the ready banner differ in behavior: the plan's
level-to-octet mapping is `level == 0 ? 1 : ((level-1)<<2)|2`, and the banner
includes `order=ascending`. Timestamp handling, frame checks, diagnostics and
the responder-side Final RSSI calculation are inherited unchanged.

The [ascending BLE initiator](../twr_checked_ascending_init/README.md) uses this
core and the existing acknowledged BLE telemetry module. Existing protocol-4
[combined responders](../twr_checked_combined_resp/README.md) remain compatible.
Their Response/Result TX power stays FEFEFEFE; the initiator sweeps Poll/Final.

There are three peers and 20 attempts per peer per setting. Peers alternate
after every attempt, including failures. Each setting lasts 60 attempts and
a complete cycle lasts 3900 attempts. All four TX_POWER fields repeat the
selected octet. The initial 01 uses coarse 1/fine 0; the subsequent 64 settings
use coarse 2 and fine codes 0–63. These are nominal gain steps, not equal or
calibrated dB increments.

## Build and flash

```bash
bash tools/build_checked_ascending.sh
source tools/ncs_env.sh
export NRFUTIL_HOME="$PWD/build/.nrfutil"
west flash --skip-rebuild -d build/checked_ascending_init -r nrfutil --dev-id 760201915
```

The builder also produces compatible responder images in
`build/checked_ascending_resp0..2`, compiling the original responder application.
All role/ID/count settings and image hashes are checked in
`build/checked_variants_ascending_manifest.json`. Only the initiator needs
reprogramming if the matching protocol-4 responders are already installed.
Otherwise flash the respective responder build directory with its explicit
serial before the initiator. No old build directory is reused.

## Bluetooth-only capture

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_three_responder_rssi.py \
  --seconds 720 --address F1:FB:C0:BC:DB:75 \
  --out experiments/data/2026-11-14/opposite_facing_ascending_sweep_run1
```

Use a new output directory on later runs. No serial ports are opened for
measurement. The collector starts a fresh sweep and pauses after the selected
window. Confirm 3900 attempts with 20 per setting per peer before claiming a
complete cycle; the wall-clock budget alone does not establish completeness.

The individual CSV retains host timestamps, peer, cycle, level, actual TX octet,
distance in mm, corrected/legacy RSSI, validity, raw C/N/D and radio errors.
The comparison CSV reports all three peers' median distances in metres, RSSI
statistics and completion counts at each common setting. Missing measurements
stay blank/null. JSON analysis labels `sweep_order=ascending`; old descending
captures retain their original interpretation.

RSSI is an uncalibrated DGC-corrected estimate in dB. Reported ranges are not
tape ground truth. Full TWR completion is not one-way PRR. Keep geometry and
orientation fixed during the sweep.

## Checks and measured record

```bash
cc -std=c99 -Wall -Wextra -Werror -Isamples/twr_checked_ascending_common \
  tools/test_checked_ascending.c -o /tmp/checked_ascending
/tmp/checked_ascending
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_analyze_ascending.py
```

The host checks cover all 65 ordered codes, two full cycles, equal peer budgets,
FE replies, order-aware log validation and endpoint interpretation.
See [the experiment report](../../experiments/opposite_facing_ascending_sweep_20261114.md)
for the actual capture, board mapping and validation limits.
