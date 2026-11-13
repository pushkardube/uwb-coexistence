# Checked two-board DS-TWR with receiver-side RSSI

Status: built and bench-tested on two DWM3001CDK boards on 2026-11-11.
See the bounded validation record below; longer-term/environmental validation remains open.

Two standalone applications use this shared implementation:

- `../twr_checked_init`: initiator, one peer (ID 0).
- `../twr_checked_resp`: responder, default ID 0.

Existing samples remain unchanged. The new protocol is deliberately incompatible
with their marker-only frames. Only two boards are flashed for this test.

## Changes

- Exact payload length checked before subtracting FCS or copying bytes.
- Distinct magic/version, frame type, peer ID and 32-bit sequence on every frame.
- Modular 40-bit timestamp differences and interval limits.
- Actual Final TX timestamp used in initiator distance calculation.
- 2500 SI microsecond delayed replies, explicitly expressed as 159744000 DTU.
- CIA completion required before each ranging RX timestamp.
- Responder captures Final RSSI only after saving its Final RX timestamp.
- Result carries T6 and responder-side Final RSSI, plus raw C/N/D diagnostics.
- No diagnostic reads at the initiator; no alternating/warmup session workaround.
- Checked TX/RX arming and bounded waits; explicit error codes and memory guards.
- Integer-only reporting; stack protection and assertions enabled.

Large work buffers/state are file-scope to make ownership explicit and guardable.
This is not claimed as a repair of an identified driver memory overwrite.
An estimate of RSSI is reported in milli-dB with raw diagnostics retained; it is
not calibrated dBm. Antenna delay is an inherited starting value, not pair calibration.
Negative ranges below -2 m or ranges above 100 m are reported as errors, never
clipped into valid output. Smaller negative values remain visible for calibration.

## Board overlay

`board.overlay` omits the inherited optional `wakeup-gpios = <&gpio1 19 ...>`.
With assertions enabled, that mapping caused an `Unsupported pin` panic during
platform initialization on these boards. The existing HAL falls back to CS for
wakeup, and this sample does not use sleep mode. No alternative wake pin is guessed.
The shared project overlay is not modified.

## Protocol (payload lengths exclude two-byte hardware FCS)

All frames start with `[C7,51,01,type,peer,seq32_le]` (9 bytes).

| Frame | Type | Bytes after header | Payload length |
|---|---:|---|---:|
| Poll | 1 | None | 9 |
| Response | 2 | T2[5], predicted T3[5] | 19 |
| Final | 3 | T4[5], predicted T5[5] | 19 |
| Result | 4 | T6[5], RSSI signed32 milli-dB, valid[1], C[4], N[2], D[1] | 26 |

All integers are little-endian. The initiator calculates DS-TWR from its actual
T1/T4/T5 and received T2/T3/T6. Result is delayed by 3 ms after diagnostics to
allow initiator RX arming. Every new exchange starts with a clean RX/status state.

## Build

From the `uwb-coexistence` root:

```bash
source tools/ncs_env.sh
export XDG_CACHE_HOME="$PWD/build/.host_cache"
export CCACHE_DIR="$PWD/build/.ccache"
mkdir -p "$XDG_CACHE_HOME"
west build -b decawave_dwm3001cdk samples/twr_checked_init -d build/checked_init -p
west build -b decawave_dwm3001cdk samples/twr_checked_resp -d build/checked_resp -p
```

For a diagnostic-off A/B control, a separate directory is required. The original
command was the following; under sysbuild it is an intended override, not proof
that the compiler received it:

```bash
west build -b decawave_dwm3001cdk samples/twr_checked_resp \
  -d build/checked_resp_nodiag -p -- -DCHECKED_RSSI=0
```

Both peers must use the same `CHECKED_RESP_ID` (default 0). These original CMake
files do not contain the newer variants’ `zephyr_get()` forwarding. Inspect the
application checked.c compile command for `-DCHECKED_RSSI=0` before treating it
as a diagnostic-off control; a parent cache entry alone is insufficient. A
correctly disabled build keeps the protocol and marks RSSI invalid (`diag=0`).
The measured baseline used ID 0 and diagnostics enabled.

## Flash two boards only

Re-read live serials first per the root `FLASHING.md`. Selected mapping:

- Initiator: `760201778`, `/dev/ttyACM0`.
- Responder 0: `760201915`, `/dev/ttyACM2`.
- Third board `760204734` is left unchanged.

```bash
west flash --skip-rebuild -d build/checked_resp -r nrfutil --dev-id 760201915
west flash --skip-rebuild -d build/checked_init -r nrfutil --dev-id 760201778
```

## Readout

UART 115200, DTR asserted. Expected initiator columns:

```text
CHECKED seq=... peer=0 dist_mm=... final_rssi_mdB=... diag=1 C=... N=... D=... ok=.../...
```

`final_rssi_mdB` is measured **at the responder**, on the initiator's Final,
which is the useful direction for later board-1 transmit-power control.
`-2147483648` is the invalid RSSI sentinel. Always check `diag`.

Errors: 1 timeout; 2 radio error; 3 length; 4 header/type/peer; 5 sequence;
6 CIA completion; 7 delayed TX; 8 interval; 9 memory guard; 10 range outside
allowed bounds. A memory-guard failure stops the app rather than hiding it by
relaxing validation. Unexpected traffic is rejected and does not produce a range.

## Host verification

```bash
cc -std=c99 -Wall -Wextra samples/twr_checked_common/test_math.c \
  -lm -o /tmp/checked_math
/tmp/checked_math
```

Tests exercise independent clock epochs, wrap in either radio's timestamp domain,
invalid/oversized intervals, and five-byte little-endian serialization. Hardware
validation must separately establish reception, counters and believable distances.

## Scope

This is the two-board ranging/RSSI baseline, not yet the multi-board discovery
or automatic transmit-power controller. It does not establish that a radio signal
can stop at a selected physical board. That experiment still needs numbered
broadcast bursts and measured PRR at all receivers.

## Bench record (final build)

The final pair was programmed/verified with west/nrfutil, then captured for 60.2 seconds after resetting with UART already open. The initiator produced 188 complete consecutive measurements (sequences 1–188), with 188/188 successes reported, every diagnostic-valid flag set, no error records, no guard/panic reports, and no log-drop reports. Reported distance: median 366.0 mm, range 328–420 mm. Approximate RSSI: -86.355 to -79.858 dB. Physical ground-truth separation was not supplied, so this establishes stable combined readout rather than absolute ranging/RSSI calibration.

Raw logs and machine-readable summary: `build/checked_monitor_20261111_143759/`. Image hashes and selected probes: `build/checked_pair_manifest.json`. The third probe was never programmed in this test.

The first assertion-enabled startup exposed the inherited invalid GPIO1.19 wakeup mapping. It was removed only in this sample overlay. The initial healthy run also exposed dropped deferred printk messages; final measurement records bypass that queue (`CONFIG_LOG_PRINTK=n`). No controlled isolation claims which change fixes every historical RSSI regression; this is a separately validated baseline.

## C implementation walkthrough

See [the checked protocol/source guide](../CHECKED_PROTOCOL.md) for the
function map, timestamp ownership, frame layout, diagnostic ordering, guards,
and differences among these independent implementations. The
[sample index](../README.md) links every role and its validation record.
