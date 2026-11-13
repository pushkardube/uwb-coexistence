# MULTI initiator: standalone role application

Status: IDs 0 and 1 each completed 92/92 when tested separately; simultaneous two-responder validation belongs to the combined variant.

## Files and responsibilities

[src/main.c](src/main.c) is a six-line entry point calling `checked_run()`.
The implementation is compiled from [../twr_checked_multi_common/checked.c](../twr_checked_multi_common/checked.c),
with timestamp helpers in [checked.h](../twr_checked_multi_common/checked.h). This directory’s
CMakeLists.txt fixes CHECKED_INITIATOR=1, selects the matching
overlay, and links the vendor radio driver plus platform HAL. prj.conf owns
logging, FPU, stack/heap, assertions and stack-protection settings.

Owns Poll/Final transmission, reply validation, DS-TWR calculation and the measurement log. It never reads receiver diagnostics locally; RSSI arrives in Result from the selected responder.

## Matching firmware and settings

Pair only with [../twr_checked_multi_resp](../twr_checked_multi_resp/README.md). Protocol version is
**3**; older marker-only samples and other checked protocol versions
are rejected. Matching the channel alone is insufficient.

Default targets: IDs 0 and 1. Fixed radio power; the baseline RSSI estimator is retained without DGC correction. The next peer is selected after every attempted exchange, even if the current peer is absent.

CHECKED_RSSI controls receiver-side diagnostics in the responder branch. An
initiator compiled with that setting still does not read its own RX RSSI.
The newer CMake files use `zephyr_get()` to forward application settings through sysbuild. Build helpers verify actual compiler definitions and image hashes. Use CHECKED_RESP_ID for identity, CHECKED_N_RESPONDERS for the target count, and SWEEP_ATTEMPTS for the per-peer dwell in the combined version; consult the shared guide for which switches this variant supports.

## Build and flash

Run from the repository root:

```bash
bash tools/build_checked_variants.sh multi
west flash --skip-rebuild -d build/checked_multi_init -r nrfutil --dev-id INIT_SERIAL
```

These commands show this role’s image; flash matching responders before the
initiator. The helper-based builds may also produce the other role and distinct
responder IDs. For a whole current combined setup, use the explicit three-board
flash command in the shared guide. UART is 115200 with DTR asserted.

## Readout and limits

Format example (ellipsis fields are placeholders):

```text
MULTI seq=... peer=... dist_mm=... final_rssi_mdB=... diag=1 C=... N=... D=... ok=.../... peer_ok=.../...
```

Distance is millimetres; RSSI fields are multiplied by 1000. `diag=0` marks
unavailable diagnostics, and -2147483648 is invalid RSSI. A radio error/timeout
must remain an error rather than being converted to a fabricated distance.
Exchange completion ratios count the full four-frame transaction, not one-way PRR.

See [the shared guide](../twr_checked_multi_common/README.md) for the protocol, exact fields,
per-variant settings, error codes and capture commands, and [the bench record](../../experiments/checked_variants_bench.md)
for measured evidence and limitations. No hardware was reflashed for this
Markdown documentation update.
