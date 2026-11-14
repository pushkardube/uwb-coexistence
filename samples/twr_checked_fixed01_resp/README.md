# UWB responder: fixed01 initiator range experiment

Standalone Zephyr application linking `../twr_checked_fixed01_common/checked.c`
with CHECKED_INITIATOR=0. Its six-line entry point calls `checked_run()`.
CMake forwards CHECKED_RESP_ID through sysbuild and uses the corrected overlay;
`prj.conf` leaves Bluetooth disabled while preserving FPU/assertion protections.

Responds only to its addressed protocol-5 Poll. Saves Final's RX timestamp
before diagnostics and sends timestamp plus RSSI/C/N/D in Result. Replies
now use 01010101, matching the initiator's Poll and Final. All four frames
therefore use the same fixed low setting.

The builder produces two images with distinct IDs:

| Fixed01 ID | Serial in this setup | Build directory |
|---|---|---|
| 0 | 760204734 | build/checked_fixed01_resp0 |
| 1 | 760204645 | build/checked_fixed01_resp1 |

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 760201778 760204734 760204645
```

After flashing, use an external USB supply and move the board while collecting
through the initiator's BLE connection. No responder Bluetooth link or UART
reader is needed. Protocol-4 sweep initiators/responders are incompatible.
See the [shared guide](../twr_checked_fixed01_common/README.md) for measurement
semantics and the [experiment record](../../experiments/fixed01_both_directions_20261114.md).
