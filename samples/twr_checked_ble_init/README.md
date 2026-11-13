# Checked UWB initiator with Bluetooth reporting

This standalone role application links the combined checked ranging core and
the BLE telemetry module. The responder remains a plain checked combined UWB
responder. Both boards can be powered from USB power banks; only the initiator
needs a BLE connection to the laptop.

main.c initializes Bluetooth, then calls checked_run. CMake fixes initiator role
and CHECKED_BLE=1, selects the corrected combined overlay, and forwards peer-count/
dwell settings through sysbuild. prj.conf enables BLE NUS with a 247-byte L2CAP
TX MTU, one connection, bounded queue/thread memory, and the checked FPU/assertion/
stack-protection settings. UART reporting is retained for comparison/debugging.

```bash
bash tools/build_checked_ble.sh 1 20
bash tools/flash_checked_variant.sh ble 760201778 760201915
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py --seconds 300
```

At boot the initiator advertises UWB-COEX-INIT and waits for the collector. The
collector subscribes and starts the sweep at 01010101. It receives distances,
RSSI, errors and level summaries over Bluetooth, acknowledges complete records,
and saves logs/CSV without opening a serial port.

Read [the complete BLE guide](../twr_checked_ble_common/README.md) for topology,
commands, reconnection, power supply, data integrity and limitations, and
[the bench record](../../experiments/checked_ble_bench.md) for actual validation.
