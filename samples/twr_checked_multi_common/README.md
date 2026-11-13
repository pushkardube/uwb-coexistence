# Checked DS-TWR: independent multi-responder experiment

This experiment forks the working `twr_checked_common` baseline and adds
addressed round-robin ranging. Its applications are `../twr_checked_multi_init`
and `../twr_checked_multi_resp`. It does not incorporate the power sweep.
The baseline and the power experiment retain independent implementations.

## Scheduling and addressing

The initiator targets IDs `0..CHECKED_N_RESPONDERS-1`, default **two responders**.
One complete Poll → Response → Final → Result exchange is attempted at a time.
The target advances after every attempt, including timeouts, followed by a
150 ms pause. An absent responder therefore cannot stall the other peers.

Every frame contains the targeted peer ID and a global 32-bit sequence number.
Responders answer only Polls for their own compile-time `CHECKED_RESP_ID`.
The initiator rejects another peer's responses; Final and Result also carry
the expected peer and sequence. Give every responder a distinct ID and use
only one initiator in this experiment. This is addressed polling, not automatic
discovery or multiple-initiator arbitration.

The initiator reports global `ok=success/attempts` and independent
`peer_ok=success/attempts`. Each successful record includes that peer's range
and the RSSI measured **at the responder on Final**. The estimator and fixed
radio behavior are inherited unchanged from the baseline, including the raw
uncalibrated RSSI estimate. The power experiment's DGC-corrected reporting is
deliberately kept in its own fork for later evaluation and merge.

## Build

From the repository root:

```bash
bash tools/build_checked_variants.sh all
```

This produces separate verified images:

| Directory | Application | Role / settings |
|---|---|---|
| `build/checked_multi_init` | `samples/twr_checked_multi_init` | Initiator, targets 0 and 1 |
| `build/checked_multi_resp0` | `samples/twr_checked_multi_resp` | Responder ID 0 |
| `build/checked_multi_resp1` | `samples/twr_checked_multi_resp` | Responder ID 1 |

For custom configurations after sourcing `tools/ncs_env.sh`:

```bash
west build -b decawave_dwm3001cdk samples/twr_checked_multi_init \
  -d build/checked_multi_init_3 -- -DCHECKED_N_RESPONDERS=3
west build -b decawave_dwm3001cdk samples/twr_checked_multi_resp \
  -d build/checked_multi_resp2 -- -DCHECKED_RESP_ID=2
```

`CHECKED_N_RESPONDERS` accepts 1–16; on-air IDs fit one byte. CMake explicitly
uses `zephyr_get()` to read overrides from sysbuild. The helper verifies the
actual compiler command contains the intended ID. A parent cache entry alone
does not prove responder ID 1 reached the compiler.

## Flash and monitor

Only pass board IDs you intend to program. Two-board testing keeps ID 1 absent:

```bash
bash tools/flash_checked_variant.sh multi 760201778 760201915
python3 tools/capture_checked_variants.py --variant multi \
  --init 760201778 --responder 760201915 --seconds 60 --reset
```

To test both responders concurrently, supply a third explicitly selected probe:

```bash
bash tools/flash_checked_variant.sh multi INIT_SERIAL RESP0_SERIAL RESP1_SERIAL
python3 tools/capture_checked_variants.py --variant multi \
  --init INIT_SERIAL --responder RESP0_SERIAL --responder RESP1_SERIAL \
  --seconds 60 --reset
```

The flash helper validates live probe presence and artifact hashes, then
flashes responders first and initiator last through west/nrfutil. The supplied
two-board command does not program the third connected board. UART is 115200,
DTR asserted. Logs and summaries go under `build/multi_capture_<timestamp>`.

Expected healthy records alternate `peer=0` and `peer=1`. With only responder 0
present, peer 1 errors are expected, and subsequent peer 0 attempts must recover.
The full acceptance test needs both peers reporting stable distances/RSSI,
separate counters, no sequence gaps, and recovery after unplugging one peer.
Read the [bench record](../../experiments/checked_variants_bench.md) for what has
actually been tested.

## Protocol and retained safeguards

The header uses protocol **version 3** (`C7 51 03 ...`). All four frame lengths,
40-bit modular timestamp math, actual initiator Final TX timestamp, reply
timing, memory guards, CIA completion checks, and post-timestamp diagnostics
follow the [checked baseline](../twr_checked_common/README.md).
The peer selection also has an inverse-value guard. Other protocol versions
and wrongly addressed frames are rejected.

This version keeps fixed RF power and does not select a boundary receiver.
Per-peer exchange completion ratios are not one-way PRR. Merge with the sweep
only after the independent tests establish the required behavior.

## C implementation walkthrough

See [the checked protocol/source guide](../CHECKED_PROTOCOL.md) for the
function map, timestamp ownership, frame layout, diagnostic ordering, guards,
and differences among these independent implementations. The
[sample index](../README.md) links every role and its validation record.
