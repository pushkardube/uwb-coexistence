# CHECKED responder: standalone role application

Status: 188/188 consecutive exchanges in 60 seconds; one real responder.

## Files and responsibilities

[src/main.c](src/main.c) is a six-line entry point calling `checked_run()`.
The implementation is compiled from [../twr_checked_common/checked.c](../twr_checked_common/checked.c),
with timestamp helpers in [checked.h](../twr_checked_common/checked.h). This directory’s
CMakeLists.txt fixes CHECKED_INITIATOR=0, selects the matching
overlay, and links the vendor radio driver plus platform HAL. prj.conf owns
logging, FPU, stack/heap, assertions and stack-protection settings.

Answers only Polls addressed to its configured ID. Saves the Final RX timestamp before reading diagnostics, then sends both in Result. A served line reports local Result-TX completion; check the initiator to establish end-to-end exchange completion.

## Matching firmware and settings

Pair only with [../twr_checked_init](../twr_checked_init/README.md). Protocol version is
**1**; older marker-only samples and other checked protocol versions
are rejected. Matching the channel alone is insufficient.

Single peer ID 0, fixed radio configuration, diagnostics enabled by default. The legacy approximate RSSI field does not include the later sweep’s DGC correction.

CHECKED_RSSI controls receiver-side diagnostics in the responder branch. An
initiator compiled with that setting still does not read its own RX RSSI.
These baseline CMake files use cache defaults but do not contain the newer variants’ `zephyr_get()` forwarding. The tested configuration is ID 0 with diagnostics on. Before claiming a custom -D override worked under sysbuild, inspect the application’s actual checked.c compile command. A parent CMake cache entry alone is insufficient.

## Build and flash

Run from the repository root:

```bash
source tools/ncs_env.sh
west build -b decawave_dwm3001cdk samples/twr_checked_resp -d build/checked_resp
west flash --skip-rebuild -d build/checked_resp -r nrfutil --dev-id RESP0_SERIAL
```

These commands show this role’s image; flash matching responders before the
initiator. The helper-based builds may also produce the other role and distinct
responder IDs. For a whole current combined setup, use the explicit three-board
flash command in the shared guide. UART is 115200 with DTR asserted.

## Readout and limits

Format example (ellipsis fields are placeholders):

```text
CHECKED served seq=... id=0 diag=1 total=...
```

Distance is millimetres; RSSI fields are multiplied by 1000. `diag=0` marks
unavailable diagnostics, and -2147483648 is invalid RSSI. A radio error/timeout
must remain an error rather than being converted to a fabricated distance.
Exchange completion ratios count the full four-frame transaction, not one-way PRR.

See [the shared guide](../twr_checked_common/README.md) for the protocol, exact fields,
per-variant settings, error codes and capture commands, and [the bench record](../../experiments/line_power_control_and_rssi_debug.md)
for measured evidence and limitations. No hardware was reflashed for this
Markdown documentation update.
