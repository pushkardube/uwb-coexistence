# uwb-coexistence

Zephyr / nRF Connect SDK firmware for the **DWM3001CDK** (Qorvo DW3000
UWB + nRF52833), with checked ranging, transmit-power sweeps, multiple
responders and Bluetooth telemetry.

The experiment aims to place boards along a line, range to them, select the
last intended receiver, and adjust the first board's transmit power to obtain
high reception at that receiver and low reception farther away. The current
firmware provides ranging and receiver-side RSSI across a power sweep.
Automatic power selection and a measured one-way reception cutoff remain
future work; completion of a ranging exchange is not one-way packet reception.

The driver and platform support originated in `zephyr-dwm3001cdk-app`.
The existing vendor libraries, headers, HAL, board overlay and devicetree
binding remain required build dependencies.

## Start with Bluetooth reporting

Use [the BLE initiator](samples/twr_checked_ble_init/README.md) with
[plain UWB responders](samples/twr_checked_combined_resp/README.md).
Both boards can use external USB power. The laptop connects over Bluetooth
to the initiator; the distant responder reports its measurements over UWB.
Only the initiator needs to remain within Bluetooth range of the laptop.

Run from the repository root:

```bash
# One responder, 20 attempts per power setting. Build only; does not flash.
bash tools/build_checked_ble.sh 1 20

# Replace these placeholders with the connected boards' numeric J-Link serials.
# The helper flashes the responder first, then the initiator.
bash tools/flash_checked_variant.sh ble INIT_SERIAL RESP0_SERIAL

# Run in a normal host Python environment with bleak installed.
python3 tools/collect_checked_ble.py --seconds 300
```

The initiator advertises as `UWB-COEX-INIT`. The collector connects, subscribes,
starts the sweep, acknowledges complete records, and writes logs and CSV under
`build/`. Use this collector for the acknowledged telemetry protocol.
The [BLE telemetry guide](samples/twr_checked_ble_common/README.md) explains
commands, reconnection, queueing and output files.

## Firmware families

Each role application has its own `CMakeLists.txt` and `prj.conf`. Common
implementation directories are shared source modules, not standalone apps.
Keep matching initiator/responder families together: their protocol versions
differ even though they use the same radio channel.

| Family | Applications | Shared implementation and guide |
|---|---|---|
| Checked one-peer baseline | `twr_checked_init`, `twr_checked_resp` | [twr_checked_common](samples/twr_checked_common/README.md) |
| Isolated power sweep | `twr_checked_power_init`, `twr_checked_power_resp` | [twr_checked_power_common](samples/twr_checked_power_common/README.md) |
| Isolated multiple responders | `twr_checked_multi_init`, `twr_checked_multi_resp` | [twr_checked_multi_common](samples/twr_checked_multi_common/README.md) |
| Combined power sweep and multiple responders | `twr_checked_combined_init`, `twr_checked_combined_resp` | [twr_checked_combined_common](samples/twr_checked_combined_common/README.md) |
| Combined firmware with BLE reporting | `twr_checked_ble_init`, matching combined responders | [twr_checked_ble_common](samples/twr_checked_ble_common/README.md) |

The checked implementations validate frame lengths, peer IDs and sequences,
use wrap-safe timestamps and bounded waits, and retain explicit errors.
The simpler baseline and independent variants remain experimental controls.

## Power sweep and RSSI

The combined and BLE initiators use **65 TX settings**: an initial
`0x01010101` probe followed by all 64 fine-gain codes at coarse gain 2,
from `0xFEFEFEFE` down to `0x02020202`. Each setting gets a fixed attempt
budget for every configured responder, including attempts that fail.

The initiator changes its Poll and Final transmit power. Each responder saves
Final's receive timestamp, measures Final's Ipatov diagnostics, and returns
them in a Result packet at fixed `0xFEFEFEFE` reply power. The initiator reports
those remote measurements; it does not substitute the return packet's RSSI.

- `dist_mm`: reported range in millimetres.
- `C`, `N`, `D`: raw CIR power, preamble accumulation count and DGC decision.
- `final_rssi_mdB`: legacy received-power estimate retained for comparison.
- `rssi_dgc_mdB`: corrected estimate, including `6000 * D`; divide by 1000 for dB.
- `diag=0` or RSSI `-2147483648`: unavailable diagnostics, not a weak valid reading.

RSSI is an uncalibrated received-power estimate. Register steps are not equal
dB steps, and arbitrary mixed-coarse values cannot be ordered by numeric hex
alone. See [DW3000 TX power notes](research/DW3000_TX_POWER_NOTES.md) for the
four power fields, coarse/fine mapping and channel-9 restrictions.

## Build and capture other variants

```bash
# UART combined variant: one responder, 20 attempts per setting.
bash tools/build_checked_combined.sh 1 20
bash tools/flash_checked_variant.sh combined INIT_SERIAL RESP0_SERIAL

# Capture selected boards over UART; requires pyserial in the host environment.
python3 tools/capture_checked_variants.py --variant combined \
  --init INIT_SERIAL --responder RESP0_SERIAL --seconds 300

# Build both independent variants: two power images and three multi images.
bash tools/build_checked_variants.sh all
```

The combined builder defaults to two responders and 10 attempts per peer per
setting when arguments are omitted. For two responders, supply both responder
serials after the initiator serial when flashing. The BLE builder defaults to
one responder and 20 attempts. Match the built peer count to the intended setup.

The [tool guide](tools/README.md) covers UART analysis, measured-map export,
nominal-power sorting, plotting and host checks. The relevant scripts are
`analyze_checked_variants.py`, `export_power_rssi_map.py`, and
`check_power_rssi_trend.py`. Generated captures and builds stay under `build/`.

## Toolchain

The build helpers activate nRF Connect SDK **v3.2.4** using
[tools/ncs_env.sh](tools/ncs_env.sh). It currently expects the SDK at
`~/ncs/v3.2.4` and toolchain bundle at `~/ncs/toolchains/2ac5840438`.
Adjust those installation paths for another machine and install the `west`
and `nrfutil device` support needed by the helpers. Flashing explicitly uses
`west flash --skip-rebuild -r nrfutil` with selected serials and verified images.

The environment script changes Python settings for the Nordic toolchain.
Run host collectors and analysis in a separate normal Python environment.
BLE collection needs `bleak`, UART capture needs `pyserial`, and plotting needs
`matplotlib`; the analysis and host test modules otherwise use the standard library.

For the root LED/console heartbeat, which does not run UWB:

```bash
source tools/ncs_env.sh
west build -b decawave_dwm3001cdk . -d build/heartbeat -p always
west flash --skip-rebuild -d build/heartbeat -r nrfutil --dev-id SELECTED_SERIAL
```

## Host checks

```bash
cc -std=c99 -Wall -Wextra -Werror samples/twr_checked_common/test_math.c -lm -o /tmp/checked_math
/tmp/checked_math
cc -std=c99 -Wall -Wextra -Werror -Isamples/twr_checked_power_common -Isamples/twr_checked_multi_common tools/test_checked_variants.c -o /tmp/checked_variants
/tmp/checked_variants
cc -std=c99 -Wall -Wextra -Werror -Isamples/twr_checked_combined_common tools/test_checked_combined.c -o /tmp/checked_combined
/tmp/checked_combined
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_analyze_checked_combined.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_collect_checked_ble.py
```

These check timestamp math, schedules, log parsing, BLE fragmentation and
replay handling. Reception, timing and RF behavior require board measurements.

## Repository layout

```text
src/                    Root LED/console heartbeat
boards/ and dts/        Board overlay and DW3000 binding
drivers/                Vendor libraries, headers and platform HAL
samples/twr_checked*/  Checked role applications and shared implementations
tools/                  Build, flash, collection, analysis and host checks
research/               Background research and TX power references
experiments/            Existing spatial experiment overview
```

The original `simple_txrx` and spatial TX/RX sources remain separate experiments.
See the [existing spatial overview](experiments/spatial_resolution.md) for their
context. Extend the closest checked family for new ranging work, keep a README
beside each application/module, and record configuration, output units and
actual validation separately from planned behavior.
