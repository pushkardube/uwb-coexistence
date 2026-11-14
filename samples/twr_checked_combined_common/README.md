# Combined multi-responder ranging and 65-setting TX sweep

This is the combined version of the independently tested checked power-sweep
and multi-responder experiments. It has two standalone Zephyr applications:

- `../twr_checked_combined_init`: initiator; addresses peers and sweeps its TX power.
- `../twr_checked_combined_resp`: responder; answers its own ID with fixed TX power.

The original checked baseline and the two standalone experiments remain intact.
The combined firmware has now been tested with one initiator and two real
responders across the earlier 64-setting sweep. The updated schedule starts
with an additional `0x01010101` reception probe, tested successfully at both
responders. All three selected boards run the updated firmware.
Read [the hardware validation record](../../experiments/checked_combined_bench.md)
for the measured results and which boards were actually tested.

The published [three-responder LOS capture](../../experiments/los_three_responder_rssi_20261113.md)
uses three responders and 20 attempts per peer per setting. Its full first cycle
completed 3898/3900 exchanges across all 65 settings. Raw BLE readings, CSV tables
and source/image-hash provenance are included with that report. The earlier
two-board mapping is retained locally as a separate historical result.

## Sweep and peer schedule

There are **65 settings**. Level 0 tests `0x01010101` (coarse gain 1, fine gain 0).
Levels 1–64 retain the complete previous sweep at coarse gain 2, descending
through fine-gain codes 63 to 0. The TX_POWER octet sequence is:

```text
01
FE FA F6 F2 EE EA E6 E2 DE DA D6 D2 CE CA C6 C2
BE BA B6 B2 AE AA A6 A2 9E 9A 96 92 8E 8A 86 82
7E 7A 76 72 6E 6A 66 62 5E 5A 56 52 4E 4A 46 42
3E 3A 36 32 2E 2A 26 22 1E 1A 16 12 0E 0A 06 02
```

Each octet is repeated in all four TX_POWER bytes: 01 means `0x01010101`;
FE means `0xFEFEFEFE`;
02 means `0x02020202`. The register steps are **not calibrated or evenly spaced
dB steps**. The initial probe changes coarse gain and is analyzed separately
from the FE-to-02 ladder. RF settings remain channel 9, `PGdly=0x34`, `PGcount=0`, 128-symbol
preamble, code 9, 6.8 Mb/s, STS off.

Default configuration is two addressed responders (IDs 0 and 1) and **10 attempts
per responder per setting**. At each setting:

1. Poll peer 0, finish or fail its exchange, then poll peer 1.
2. Repeat that round 10 times, preserving the same initiator TX power.
3. Emit a separate level summary for each peer and advance to the next setting.
4. After all 65 settings, return to 01 and increment the cycle number.

Missing peers and failed exchanges consume their slots. They cannot prevent
another peer from being polled or the sweep from advancing. The pause after
each attempt is 150 ms. Default cycle length is 1,300 attempts; a cycle takes
several minutes, depending on reply timeouts and the number of configured peers.
Compare RSSI distributions for each **peer and setting** rather than pooling
different receivers or different power levels.

## Measurement direction and ranging safeguards

Only the initiator sweeps. Both its Poll and Final use the selected power.
Every responder transmits Response and Result at fixed `0xFEFEFEFE`.
The reported RSSI belongs to the initiator's Final received **at that responder**,
which is the direction required for downstream-receiver power experiments.

The exchange stays Poll → Response → Final → Result. All frames include the
target peer and global 32-bit sequence. Responders answer only their own ID;
the initiator accepts only the selected peer and sequence. One exchange is
active at a time. This is addressed polling, not automatic peer discovery or
multiple-initiator arbitration.

Retained baseline safeguards include exact frame lengths before copying,
bounded radio/host waits, CIA completion before ranging RX timestamps, modular
40-bit timestamp math, actual initiator Final TX timestamp, and memory guards.
The responder saves its Final RX timestamp before reading diagnostics. Power
register programming and measurement logging stay outside delayed-reply windows.
The sample-specific overlay retains the corrected optional wakeup mapping.

Protocol version is **4**, header `C7 51 04 type peer seq32_le`. Frame payload
sizes are unchanged: Poll 9, Response 19, Final 19, Result 26 bytes, excluding
the two-byte FCS. Version 1 baseline, version 2 power-only, and version 3
multi-only applications will reject this firmware's frames. Flash matching
combined initiator/responder images together.

## Build

From the repository root:

```bash
# Default: two responder images, 10 attempts per peer at each of 65 settings.
bash tools/build_checked_combined.sh

# Example: four responders, 20 attempts per peer at each setting.
bash tools/build_checked_combined.sh 4 20
```

Supported responder count is 1–16; attempt budget is 1–10000 per peer per setting.
The helper sources the NCS 3.2.4 environment and builds through west into:

| Directory | Firmware |
|---|---|
| `build/checked_combined_init` | Initiator with configured responder count and dwell budget |
| `build/checked_combined_resp0` | Responder ID 0 |
| `build/checked_combined_resp1` | Responder ID 1 |
| `build/checked_combined_respN` | Additional IDs, if requested |

The helper checks actual compiler arguments for role, ID, responder count and
attempt budget, then records image hashes in
`build/checked_variants_combined_manifest.json`. Application CMake uses
`zephyr_get()` to propagate settings through sysbuild; a parent cache entry
alone is insufficient proof that an override reached the firmware.

Manual custom build after sourcing `tools/ncs_env.sh`:

```bash
west build -b decawave_dwm3001cdk samples/twr_checked_combined_init \
  -d build/combined_custom_init -- -DCHECKED_N_RESPONDERS=3 -DSWEEP_ATTEMPTS=20
west build -b decawave_dwm3001cdk samples/twr_checked_combined_resp \
  -d build/combined_custom_resp2 -- -DCHECKED_N_RESPONDERS=3 -DCHECKED_RESP_ID=2
```

Use a separate directory per role and ID. Custom directories require explicit
manual `west flash --skip-rebuild` commands; the provided flash helper uses
only its named build directories and matching verified manifest.

## Flash the selected boards

To program the current three-board setup (one initiator and two responders):

```bash
bash tools/flash_checked_variant.sh combined 760201778 760201915 760204734
```

To program only two boards for a missing-peer test:

```bash
bash tools/flash_checked_variant.sh combined 760201778 760201915
```

This programs responder 0 and initiator only. To test a missing peer, also
disconnect or stop any previously programmed responder 1. With peer 1 absent,
the default two-target initiator's failures for that peer are expected.

When programming additional boards is intended, list them explicitly:

```bash
bash tools/flash_checked_variant.sh combined INIT_SERIAL RESP0_SERIAL RESP1_SERIAL
```

Additional serial arguments map to IDs 2, 3, and so on. The helper verifies
selected live probes and image hashes, then runs west/nrfutil with
`--skip-rebuild`, responders first and initiator last. It does not program every
connected probe automatically. See the root [FLASHING.md](../../FLASHING.md).

## Capture and analyze

UART: 115200, DTR asserted. Capture the current three-board setup:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/capture_checked_variants.py \
  --variant combined --init 760201778 --responder 760201915 \
  --responder 760204734 --seconds 260 --reset
```

Repeat `--responder SERIAL` for additional selected boards. A 260-second capture
is sized to cover a default cycle with two targets, including a missing-peer test;
actual timing varies. Larger responder counts/budgets need longer captures.
Logs and `summary.json` go under `build/combined_capture_<timestamp>/`.

```bash
python3 tools/analyze_checked_variants.py build/<capture>/init.log \
  --json build/<capture>/analysis.json --csv build/<capture>/measurements.csv
```

The analyzer groups results by both peer and power level (`by_peer_level`).
It also reports per-peer totals and endpoint RSSI changes, checks the sequence
and configured schedule, and detects fatal/log-drop reports. Endpoint trends
compare the 64 coarse-2 settings (levels 1–64) and remain unset until that
ladder has appeared for the peer. The initial 01 probe is returned separately
under `probe_01010101`, with completion and RSSI statistics per peer. Missing
RSSI is retained as missing. Pooled per-peer RSSI summaries span all observed powers,
so use `by_peer_level` for power-response interpretation.

## Actual output example

These lines were captured at the initial 01 setting with both responders running:

```text
COMBINED seq=1 peer=0 dist_mm=409 final_rssi_mdB=-86519 diag=1 C=18 N=107 D=0 ok=1/1 peer_ok=1/1 cycle=0 level=0 octet=0x01 rssi_dgc_mdB=-86519 level_ok=1/1
COMBINED seq=2 peer=1 dist_mm=902 final_rssi_mdB=-84681 diag=1 C=28 N=108 D=0 ok=2/2 peer_ok=1/1 cycle=0 level=0 octet=0x01 rssi_dgc_mdB=-84681 level_ok=1/1
COMBINED_LEVEL cycle=0 level=0 octet=0x01 peer=0 attempted=10 completed=10 valid_rssi=10 mean_dgc_mdB=-86594
COMBINED_LEVEL cycle=0 level=0 octet=0x01 peer=1 attempted=10 completed=10 valid_rssi=10 mean_dgc_mdB=-84977
```

| Field | Interpretation |
|---|---|
| `dist_mm` | Reported DS-TWR range, millimetres; 378 means 0.378 m |
| `final_rssi_mdB` | Original approximate RSSI estimate, multiplied by 1000 |
| `rssi_dgc_mdB` | Gain-corrected estimate; -64162 means -64.162 dB |
| `diag` | 1 means valid diagnostics; always check this |
| `C`, `N`, `D` | Raw CIR power, accumulation count and DGC decision |
| `ok` | Global completed exchanges / attempted exchanges |
| `peer_ok` | Completed / attempted for this peer, across settings |
| `level_ok` | Completed / attempted for this peer in the current level and cycle |
| `cycle`, `level` | Zero-based sweep cycle and level (0–64); 0 is the 01 probe |
| `octet` | Repeated-byte initiator TX_POWER setting |
| `COMBINED_LEVEL` | Completed dwell summary for one peer; includes failed attempts |

The corrected estimate is the inherited `10*log10(C*2^21/N^2)-121.7`, plus
`6*D`, following the vendor DGC model already used in the independent sweep.
Both estimates remain uncalibrated; neither register settings nor readings
prove absolute emitted dBm. Invalid RSSI is `-2147483648`.

Both peers complete 10/10 exchanges at the setting shown. In the separate
missing-peer test, unanswered polls produced error 2. With one of two peers
absent, global completion is near 50% even when the present peer succeeds every
time; inspect `peer_ok` and `level_ok` rather than inferring which link failed
from the global total.
Error codes: 1 host timeout, 2 radio error/timeout, 3 frame length, 4 header/type/peer,
5 sequence, 6 CIA completion, 7 delayed TX, 8 interval, 9 memory guard,
10 range outside the accepted bounds. Errors do not produce a fabricated range.

## Scope and remaining spatial experiment

This combines multi-responder ranging and a finer TX sweep. It does not yet
choose a cutoff receiver, discover arbitrary peers, or close a power-control
feedback loop. Four-frame exchange completion is not one-way reception ratio:
a failure alone cannot identify which frame or direction was lost.

The eventual board-4 versus board-5 experiment needs numbered one-way bursts
and PRR at all receivers. This version supplies distance and received-strength
measurements at known TX settings to prepare that experiment. See the
[bench record](../../experiments/checked_combined_bench.md) for the later
three-board run as well as the initial missing-peer test.

## C implementation walkthrough

See [the checked protocol/source guide](../CHECKED_PROTOCOL.md) for the
function map, timestamp ownership, frame layout, diagnostic ordering, guards,
and differences among these independent implementations. The
[sample index](../README.md) links every role and its validation record.
