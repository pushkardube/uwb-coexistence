# BLE initiator for the ascending 01010101-to-FEFEFEFE sweep

Standalone application using `../twr_checked_ascending_common/checked.c` and
the existing BLE telemetry module. CMake selects initiator role, three targets,
20 attempts per peer per setting, CHECKED_BLE=1 and the corrected overlay.
prj.conf retains the tested BLE, stack, assertion and FPU settings.

The six-line main initializes BLE and calls checked_run. Protocol 4 is unchanged,
so existing addressed combined responders work. The initiator advertises
UWB-COEX-INIT and waits for the host's START command.

```bash
bash tools/build_checked_ascending.sh
python3 tools/collect_three_responder_rssi.py --seconds 720 --address F1:FB:C0:BC:DB:75
```

Build alone does not flash. Read the [shared guide](../twr_checked_ascending_common/README.md)
for explicit flashing, data storage, power direction, units and test results.
