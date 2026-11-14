# BLE initiator: continuous fixed 01010101

Standalone Zephyr application for the fixed-power experiment. `src/main.c`
starts the existing BLE telemetry module and calls `checked_run()` from
`../twr_checked_fixed01_common/checked.c`. CMake selects initiator role,
two responders, the corrected overlay and CHECKED_BLE=1. `prj.conf` enables
NUS, FPU, assertions and stack protection with direct measurement reporting.

Poll and Final always use 01010101; there is no sweep or fallback to stronger
power. Protocol version 5 matches only the new fixed01 responders. The board
advertises UWB-COEX-INIT and waits for BLE subscription and START.

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 760201778 760204734 760204645
python3 tools/collect_checked_ble.py --seconds 3600
```

The first serial remains the initiator. The next two serials map to fixed01
responder IDs 0 and 1. See the [shared guide](../twr_checked_fixed01_common/README.md)
for power direction, data files, external power, units and interpretation.
