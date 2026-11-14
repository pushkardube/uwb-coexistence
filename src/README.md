# Root application's hardware heartbeat

[main.c](main.c) belongs to the repository-root Zephyr application, not any
radio sample. It checks that `led0` is ready, configures it, toggles every
500 ms, and logs `DWM3001CDK app boot` followed by `heartbeat` messages.

```bash
# Run from the repository root:
source tools/ncs_env.sh
west build -b decawave_dwm3001cdk . -d build/heartbeat -p always
west flash --skip-rebuild -d build/heartbeat -r nrfutil --dev-id SELECTED_SERIAL
```

This tests the CPU/build/console/LED path. The root CMake file does not link
the DW3000 library or platform sources, and the app does not range or transmit
UWB frames. A heartbeat therefore does not establish working DW3000 wiring.
Flashing it replaces whichever radio role was on the selected board.

Configuration is in [../prj.conf](../prj.conf), with immediate logging and a
4096-byte main stack. UART is 115200 with DTR asserted. GPIO errors return from
main; there is no separate LED-recovery mechanism. Use
[the sample index](../samples/README.md) to select the next radio application.
