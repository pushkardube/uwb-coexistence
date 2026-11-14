# Distance-informed control of a line of UWB receivers

Updated 2026-11-11 from the experiment owner's clarification and source/build inspection.

This file preserves the initial objective and historical split-firmware
investigation. The current checked three-board measurements are in
[the combined bench record](checked_combined_bench.md); the next line-of-boards
experiment is specified in [the execution plan](spatial_resolution_execution_plan.md).
References below to the then-current split applications describe that earlier stage.

## The actual objective

Put multiple boards along a line. Board 1 first ranges to every other board at a normal discovery/ranging power. The operator chooses the last intended receiver, for example physical board 4. Board 1 then adjusts its transmit power to achieve high reception at board 4 and low reception at board 5 and beyond. The ideal target is 100% versus 0% packet reception over a defined test window.

The desired behavior is a physical reception boundary, not merely addressing or having board 5 discard packets in software. Addressed polling in the current firmware avoids responder collisions; it does not establish that non-addressed boards cannot decode a transmission.

Power does not create a hard spatial wall or zero RF energy beyond board 4. The testable metric is successful packet reception on the selected receiver configuration. Distances provide an initial link-budget estimate; measured per-receiver PRR is required to decide whether a power level actually separates the adjacent boards.

For illustration, under an equal-gain free-space model the path-loss difference between 4 m and 5 m is only `20*log10(5/4) = 1.94 dB`. That is a model example, not a measurement of this setup. Orientation, receiver sensitivity variation, multipath, and fading can eliminate the available separation. Some geometries may have no power setting meeting the requested PRR targets.

## Intended experiment phases

1. Discover/range every board at the normal baseline power; retain physical-board labels separately from zero-based responder IDs.
2. Record distance and, where useful, receiver-side signal quality without changing the ranging exchange's timing assumptions.
3. Choose the intended last receiver and the first excluded receiver.
4. Use distance/link measurements to initialize a board-1 power setting.
5. Send fixed-count, numbered measurement bursts from board 1 and count decoded packets independently at every receiver.
6. Adjust power from the measured PRR at the selected boundary; verify other intended receivers as well.
7. Restore the discovery/control link between test bursts so that an excluded receiver can report its count, including zero.

Missing telemetry must remain distinct from zero reception. Record attempts and confidence over repeated windows; observing zero packets in one finite run is not proof of a permanent zero probability.

The current split firmware implements the ranging/RSSI preparation stage. It does not yet implement receiver selection, closed-loop power adjustment, or a validated per-power downlink PRR experiment.

## Current split applications

- `samples/twr_alt_init`: initiator only, two addressed responders, DS-TWR, five-cycle alternating RANGE/RSSI sessions.
- `samples/twr_alt_resp`: responder only, compile-time `RESPONDER_ID` guarded by `#ifndef`, built separately for IDs 0 and 1.
- Common configuration: channel 9, preamble code 9, length 128, DW-8 SFD, 6.8 Mb/s, STS off, antenna delay 16385.
- Reply constants: 900 multiplied by 63898 DTU, approximately 900 SI microseconds despite the UUS macro naming.

The initiator's DS RSSI read follows **Result RX**, so it measures the responder-to-initiator Result signal. It does not directly measure the strength of board 1's transmission at the responder. For the proposed power controller, receiver-side PRR/RSSI is more direct. Channel reciprocity alone does not remove differences in transmitter power, receiver calibration, or receive-chain behavior.

## Why RSSI additions can coincide with broken ranging

### What is actually established

Historical READMEs report correct ranging without a diagnostics read, then wrong ranges with diagnostics added. That implicates the changed execution path, but does not identify a unique internal mechanism.

Inspection of the linked `libdwt_uwb_driver-m4-hfp-6.0.14.a` gives stronger limits on the explanation:

- `dwt_nlos_alldiag()` dispatches operation 129 to the DW3000 implementation.
- Its Ipatov branch reads five 32-bit registers (accumulation count, F1, F2, F3, CIR power), then reads DGC decision: six SPI reads in total.
- That inspected branch does not write radio registers, toggle RX buffers, or reset the transceiver. It writes its output structure in host RAM.
- Caller object and archive both report `Tag_ABI_enum_size: small` and hard-float argument convention. An enum-width ABI mismatch was investigated and is not supported by these build attributes.
- The split samples do not call `dwt_setdblrxbuffmode()` to enable double buffering.

Therefore the older assertion that this read definitely desynchronizes a double RX buffer is not a demonstrated root cause. Full `dwt_readdiagnostics()` is a different, larger path and should be tested separately. The nearby vendor SDK source is another driver revision and must not be substituted for exact binary behavior without comparison.

### Candidate mechanisms and discriminating tests

| Candidate | Evidence/relevance | Test |
|---|---|---|
| Extra SPI work misses delayed-TX lead | Credible when placed before Response/Final arming; local history reports expensive SPI transaction overhead | Record radio scheduling margin, start-TX result, HPDWARN and SYS_STATE; compare diagnostics versus equal-duration delay |
| Diagnostics captured from wrong/not-ready frame | Current DS path clears Result RX/CIA flags, then reads RSSI without waiting for Result CIADONE | Capture required Result CIA completion and diagnostics before clearing, then report afterward |
| Stale timestamp or wrong association | Can produce large/negative ranges despite a completed exchange | Record T1–T6, four modular intervals, sequence/peer and frame lengths before/after feature addition |
| Receive-buffer overflow/short-frame parsing | Confirmed unchecked `rx_len-FCS_LEN` copies into 32/16-byte arrays; both peers hear other frames in multi-board operation | Require exact protocol lengths before reading and validate Final/Result sequences |
| 40-bit rollover | Confirmed plain subtraction of 40-bit timestamps in 64-bit containers | Test modular differences across synthetic wrap; rare wrap cannot alone explain every-exchange failure |
| Logging/math timing or memory-layout change | Immediate logging and extra math change execution; this alone does not prove a hardware defect | Separate raw diagnostic read, arithmetic, and printing; compare equal-duration control |
| SPI transport, driver state or library contract | Still possible after the above controls; register reads alone do not prove side effects | Trace exact register access/state, check SPI returns, freeze library/header versions and reproduce minimally |

Important qualification: in the current DS split application RSSI is read **after** the completed exchange, followed by a 100 ms inter-target sleep and a 300 ms inter-cycle sleep. A claim that this end-of-exchange read simply misses that same exchange's 900 µs Final deadline does not fit the current call placement. It can explain earlier placements, not automatically this one.

An additional source trap: `samples/twr_multi/src/main.c` currently has `RSSI_ISOLATION_PROBE=1`, returning a constant `-80.0` without measuring radio strength. A stable printed RSSI in that isolation build is not evidence of successful measurement. The split initiator does perform the real diagnostics call.

### Smallest useful diagnosis sequence

Keep identical artifacts for both responders and geometry. Compare initiator variants with:

1. No diagnostics logging configuration and no RSSI read.
2. Diagnostics configuration only, no register read.
3. Diagnostics register read only, preserve raw fields; no logarithm/report.
4. Same-duration wait instead of the register read.
5. Logarithm/report enabled only after completion.

For each, record attempt/success counts, raw timestamp intervals, start-TX failures, CIA status, and actual frame lengths. This separates radio configuration, SPI access, timing, and formatting. Alternating RANGE/RSSI is an existing workaround, not a proven root-cause repair or a simultaneous distance/RSSI measurement.

## Build results from this session

All three existing split images built successfully with NCS v3.2.4 / Zephyr 4.2.99 for `decawave_dwm3001cdk/nrf52833`. No firmware C or protocol behavior was changed. The logs contained no compiler warning/error matches.

| Image | Build directory | Flash usage | RAM usage |
|---|---|---:|---:|
| Initiator | `build/coex_split_init` | 98,272 B | 18,176 B |
| Responder 0 | `build/coex_split_resp0` | 93,940 B | 18,176 B |
| Responder 1 | `build/coex_split_resp1` | 93,940 B | 18,176 B |

The actual responder compiler commands contain `-DRESPONDER_ID=0` and `-DRESPONDER_ID=1` respectively. `build/coex_split_manifest.json` records the current image hashes and source hashes. Each sysbuild directory contains `merged.hex`, plus application ELF/HEX beneath `twr_alt_init/zephyr` or `twr_alt_resp/zephyr`.

The first build attempts hit an unwritable SDK-side Zephyr cache. Pointing both `XDG_CACHE_HOME` and ccache inside `build/` resolved it without modifying SDK files. A sysbuild-only `USER_CACHE_DIR` did not propagate to the child application; the environment setting covers both.

Reproduce all builds from the repository root:

```bash
bash tools/build_split_twr.sh
```

## Detection and flashing status

**Successful retry after execution permissions changed:** all three images were
programmed, verified, and reset with `west flash --skip-rebuild -r nrfutil`:

| Role | Probe | UART |
|---|---|---|
| Initiator | 760201778 | ttyACM0 |
| Responder ID 0 | 760201915 | ttyACM2 |
| Responder ID 1 | 760204734 | ttyACM1 |

Flash and 15-second UART capture logs are in
`build/split_flash_logs.QdxlWLR7/`. The images were checked against
`build/coex_split_manifest.json` before programming. All three nrfutil commands
reported successful programming and verification.

Live behavior is **not yet a healthy ranging validation**: the capture contains
repeated initiator `[RANGE] resp=0 warmup (discarded)` lines and responder-1
`id=1 served seq=1` lines. Responder 0 produced no UART bytes during that window.
The apparent stuck loop/sequence state requires diagnosis; successful flashing
does not establish that the intended round-robin state machine runs correctly.
No firmware C was changed during this retry. The records below describe earlier
attempts under restricted execution permissions.

**Latest retry, after reading `FLASHING.md`:** all three probes are now visible:
`760201778` (ttyACM0), `760204734` (ttyACM1), and `760201915` (ttyACM2).
Using a writable copy of the bundled nrfutil runtime at `build/.nrfutil`
resolved its initial SDK-side log-directory failure. `nrfutil device list`
reports three supported devices. A real `west flash --skip-rebuild -r nrfutil`
attempt for responder 0 on `760201915` reaches probe connection but fails with
`Error creating IPC server: Operation not permitted`. No successful programming
or boot verification is claimed. The helper now uses the documented nrfutil
runner. The following two-probe record describes the earlier attempt.

At the last check this session detected **two**, not three, SEGGER probes:

| Probe serial | USB port | Associated host tty from sysfs |
|---|---|---|
| 760201778 | 3-1.1 | ttyACM0 |
| 760204734 | 3-1.2 | ttyACM1 |

USB metadata was readable but `/dev/bus/usb` and serial device nodes were unavailable inside this execution session. Both a real `west flash --skip-rebuild ... -r jlink --dev-id 760201778` attempt and a direct J-Link connection check failed before establishing a connection. **No programming success or live ranging validation is claimed.** No reset/boot banner could be verified.

To complete programming from a host terminal with USB access, connect the third board and run:

```bash
bash tools/flash_split_twr.sh --list
bash tools/flash_split_twr.sh
```

With no arguments the flash script requires exactly three SEGGER probes and assigns the smallest serial to initiator, then IDs 0 and 1 to the other two. For a specific physical arrangement pass `INIT_SERIAL RESP0_SERIAL RESP1_SERIAL` instead. The script verifies all image hashes before programming, flashes responders first and initiator last with `--skip-rebuild`, and stops on error. Its device-selection and missing-board checks were exercised here; successful hardware flashing was not.

After successful programming, read the selected initiator's mapped UART at 115200 baud. Expect `twr_alt_init MODE=DS-TWR`, two responder IDs, alternating `[RANGE]`/`[RSSI ]`, and discarded warmup cycles. Distances must be checked against the physical setup; build success is not a range-correctness test.
