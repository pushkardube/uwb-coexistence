# Firmware index

This index covers applications included in this repository snapshot. The original
65-setting sweep and the fixed-01010101 experiment have separate source and build
directories. Historical local attempts are outside this published application list.

## Current fixed-power experiment

| Component | Purpose |
|---|---|
| [twr_checked_fixed01_init](twr_checked_fixed01_init/README.md) | BLE initiator, protocol 5, Poll/Final always 01010101 |
| [twr_checked_fixed01_resp](twr_checked_fixed01_resp/README.md) | Two addressed responder images; Response/Result also 01010101 |
| [twr_checked_fixed01_common](twr_checked_fixed01_common/README.md) | Fixed plan, checked DS-TWR, timestamp helpers and corrected overlay |

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 INIT_SERIAL RESP0_SERIAL RESP1_SERIAL
python3 tools/collect_checked_ble.py --seconds 3600
```

The current both-directions configuration is documented in
[the 2026-11-14 validation](../experiments/fixed01_both_directions_20261114.md).
The [earlier FE-reply trial](../experiments/fixed01_range_test_20261113.md) remains
historical, with raw data and a source-hash-verified reproduction patch.

## Preserved 65-setting sweep

An independent [ascending-order variant](twr_checked_ascending_common/README.md)
now acquires 01,02,06,...,FE with the same protocol-4 responders. Its
[BLE initiator](twr_checked_ascending_init/README.md) and build directories are
separate; the original sweep below retains its tested acquisition order.

| Component | Purpose |
|---|---|
| [twr_checked_ble_init](twr_checked_ble_init/README.md) | BLE initiator using the combined sweep core |
| [twr_checked_ble_common](twr_checked_ble_common/README.md) | NUS telemetry, commands and acknowledged record replay |
| [twr_checked_combined_init](twr_checked_combined_init/README.md) | UART-only initiator reference |
| [twr_checked_combined_resp](twr_checked_combined_resp/README.md) | Addressed UWB responder with fixed FE reply power |
| [twr_checked_combined_common](twr_checked_combined_common/README.md) | Protocol-4 ranging, peer schedule and 65-setting sweep |

The schedule is 01010101 first, then all 64 coarse-2 fine-gain settings FE..02.
A three-responder build with 20 attempts per peer per setting needs 3900 attempts
per full cycle. Do not mix protocol-4 sweep peers with protocol-5 fixed peers.

```bash
bash tools/build_checked_ble.sh 3 20
bash tools/flash_checked_variant.sh ble INIT_SERIAL RESP0_SERIAL RESP1_SERIAL RESP2_SERIAL
python3 tools/collect_three_responder_rssi.py --seconds 720
```

See [the full three-responder LOS capture](../experiments/los_three_responder_rssi_20261113.md)
and [the three-responder collector guide](../tools/THREE_RESPONDER_RSSI.md).
Source/image hashes from the saved sweep were checked after creating the fixed
experiment; the sweep firmware and four saved images were unchanged.

## Independent checked controls

| Family | Initiator | Responder | Shared source and guide |
|---|---|---|---|
| Baseline, protocol 1 | [twr_checked_init](twr_checked_init/README.md) | [twr_checked_resp](twr_checked_resp/README.md) | [twr_checked_common](twr_checked_common/README.md) |
| Power-only, protocol 2 | [twr_checked_power_init](twr_checked_power_init/README.md) | [twr_checked_power_resp](twr_checked_power_resp/README.md) | [twr_checked_power_common](twr_checked_power_common/README.md) |
| Multi-only, protocol 3 | [twr_checked_multi_init](twr_checked_multi_init/README.md) | [twr_checked_multi_resp](twr_checked_multi_resp/README.md) | [twr_checked_multi_common](twr_checked_multi_common/README.md) |

The simpler implementations remain separate experimental controls. Their
[bounded validation record](../experiments/checked_variants_bench.md) distinguishes
isolated peer-ID tests from concurrent multi-responder measurements.

## Original applications and supporting documentation

- [simple_txrx](simple_txrx/README.md): minimal radio packet example.
- [spatial_resolution_tx](spatial_resolution_tx/README.md) and
  [spatial_resolution_rx](spatial_resolution_rx/README.md): existing experimental
  burst/PRR preparation; a finished zero-reporting instrument is still planned.
- [Checked C walkthrough](CHECKED_PROTOCOL.md): timestamps, frames and guards.
- [Build and flash guide](../FLASHING.md) and [host tools](../tools/README.md).
- [Root heartbeat](../src/README.md), [platform HAL](../drivers/platform/README.md)
  and [vendor driver](../drivers/dw3000/README.md).
- [Spatial execution plan](../experiments/spatial_resolution_execution_plan.md):
  planned one-way reception measurements and line-of-boards expansion.

Read the role's README before building: common directories are source modules,
not standalone Zephyr applications. Keep data units, invalid-reading semantics,
actual validation and planned work explicit when extending an experiment.
