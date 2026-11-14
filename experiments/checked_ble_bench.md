# Checked ranging and power sweep over Bluetooth: bench record

Date: 2026-11-12. Board: DWM3001CDK, DW3000 + nRF52833.
Implementation: [BLE telemetry guide](../samples/twr_checked_ble_common/README.md).

## Topology and artifacts

| Probe | Firmware | Radio path |
|---|---|---|
| 760201778 | twr_checked_ble_init | UWB initiator + BLE NUS peripheral |
| 760201915 | twr_checked_combined_resp, ID 0 | UWB only |

The initiator advertises UWB-COEX-INIT at the observed address CB:56:11:3C:AB:ED.
The laptop connects over BLE NUS and receives the same COMBINED and COMBINED_LEVEL
text emitted to UART. The responder returns Final RSSI/T6 in UWB Result; it does
not need a Bluetooth or USB data connection to the host.

Build: `bash tools/build_checked_ble.sh 1 20`. The builder verified one target,
20 attempts per setting, the BLE-enabled initiator role and responder ID 0.
The checked UWB packet layout remains protocol 4. The 65-setting schedule begins
at 01010101; responders still transmit at FEFEFEFE. BLE transport/commands are
only invoked outside an active exchange.

The final build log is `build/checked_ble_build.log`; image hashes and compiler
commands are in `build/checked_variants_ble_manifest.json`. The initiator uses
235092 bytes flash and 60304 bytes RAM, below the board's 512 KB / 128 KB limits.
Responder usage is 119972 bytes flash and 22016 bytes RAM. No warning/error
diagnostics were found in the final build log. Final flash verification logs:
`build/ble_flash.U9mkRVE9/`.

The host Bluetooth adapter was initially soft-blocked and powered off. It was
unblocked and enabled before scanning. The working collector uses Bleak with
the existing BlueZ service; no serial port is opened by the BLE collector.

## Initial notification-only experiment and correction

The first prototype's `build/ble_capture_20261112_011015/` captured 321 records,
while simultaneous UART captured 324. A BLE connection timeout (reason 8)
occurred; reconnection resumed the sweep, but sequences 178–180 were missing
from the host BLE log even though local notification completion had succeeded.
UART reference: `build/combined_capture_20261112_011014/`.

This failed data-integrity check motivated application-level record ACKs. The
current sender retains each complete record until the host has reassembled and
written it, then acknowledged its boot nonce and record ID. Unacknowledged
records are replayed across reconnects; the collector filters duplicate replays.
Queue backpressure pauses new UWB attempts rather than silently overflowing.

## Acknowledged transport: forced disconnect

Final firmware was tested for a 75-second BLE interval while UART was captured
independently. The host deliberately disconnected CB:56:11:3C:AB:ED using
bluetoothctl; the board returned to advertising, and the collector reconnected
and sent RESUME rather than restarting the sequence.

- BLE logs: `build/ble_capture_20261112_011633/`.
- UART logs: `build/combined_capture_20261112_011632/`.
- Both streams contained **404 consecutive measurements**, sequences 1–404.
- UWB completion was **404/404** with valid range/RSSI reporting.
- There were no measurement sequence gaps or firmware queue drops in that run.

## Explicit replay test

In `build/ble_ack_replay_test/`, the host deliberately omitted the ACK for boot
dac99af4, record 435. The firmware retransmitted it after its acknowledgement
timeout. The collector counted one transport replay, acknowledged it, and did
not duplicate the saved record. This exercised actual on-air retry, not just
the Python framing helper.

Host tests also passed for byte-by-byte notification fragmentation, coalesced
records, disconnect tails, sequence gaps/duplicates, bounded input buffering
and envelope replay deduplication:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_collect_checked_ble.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_analyze_checked_combined.py
```

## Full-sweep BLE/UART comparison

The final 300-second BLE measurement run (303.4 seconds including command/
disconnect cleanup) is `build/ble_capture_20261112_012037/`. Independent UART
capture ran for 330 seconds in `build/combined_capture_20261112_012036/`.

Both transports contained **exactly the same 1698 measurement/error records**,
sequences 1–1698, with field-for-field equality. UWB completion was **1697/1698**;
every completed exchange returned valid diagnostics. Sequence 1205, level 60,
octet 12 returned radio error code 2. The error record reached both transports;
it was not a missing Bluetooth record.

The complete first sweep contains 1300 attempted exchanges, exactly 20 at
each of the 65 settings, with 1299 completed exchanges and one recorded radio
error. The sweep then continued into the next cycle. The existing map exporter
successfully generated `power_map.md`, `power_map.csv` and `power_map.json`
from the BLE-only init.log, retaining the 19/20 row rather than hiding its error.

Final host transport metrics:

| Metric | Observed |
|---|---:|
| Complete measurement/error records | 1698 |
| BLE connections in this run | 1 |
| Measurement sequence gaps | 0 |
| Duplicate/out-of-order measurements | 0 / 0 |
| Framing errors / discarded partial bytes | 0 / 0 |
| Reported firmware queue drops | 0 |
| Transport replays during this normal run | 0 |

Final STATUS showed running=0 and queue=0. The longer UART capture contained
no additional attempts after the collector's PAUSE. No fatal errors, dropped
UART logs or responder error reports appeared in either board's capture.
Reported distance: median 1541 mm, range 1483–1619 mm; no physical tape
ground truth was supplied. Bluetooth active did not reproduce the historical
extreme-distance failures in this bounded run, but one UWB radio error remains
part of the observed result rather than a claim of perfect ranging reliability.

The STATUS retry count was cumulative from the earlier deliberately omitted
ACK test; START resets UWB sweep counters rather than transport lifetime counters.
Image hashes, source hashes, the exact-match check, board assignment and metrics
are recorded in `build/checked_ble_validation.json`. Both connected boards remain
flashed with these images; the initiator advertises and waits for a collector.

## Scope and practical use

These tests use the currently connected bench boards. USB was still physically
available for power and independent UART comparison; the BLE collector itself
obtains all measurements wirelessly. Moving to USB power banks is the intended
standalone operating setup, but no physical unplug/move is claimed from this
software-driven bench session. Actual achievable distances depend on the
UWB link, BLE link to the initiator, power supply and physical environment.

This implements Bluetooth transport for the current ranging/sweep data. It does
not yet implement the spatial plan's independent broadcast PRR counter or zero
reception reports from a receiver whose UWB Result is unavailable. See
[the spatial execution plan](spatial_resolution_execution_plan.md).
