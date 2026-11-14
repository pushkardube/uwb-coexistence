# Combined TX-power sweep and addressed ranging: validation

Date: 2026-11-11. Implementation and commands:
[combined sample README](../samples/twr_checked_combined_common/README.md).

## Implementation

The checked power-sweep and multi-responder implementations are combined in
`samples/twr_checked_combined_common`, with separate initiator and responder
applications. The preceding baseline and standalone experiments remain unchanged;
their recorded source hashes were checked before this run.

The initiator exercises all 64 fine-gain codes, holding the previously tested
coarse setting at 2. A setting lasts 10 addressed attempts per peer by default.
With two configured peers, 20 attempts finish a level and 1,280 finish a cycle.
The target rotates after every attempt, including errors. Replies remain at
fixed `0xFEFEFEFE`, and the responder reports diagnostics for the received Final.
The wire protocol uses version 4 to reject older incompatible applications.

## Build and host checks

`bash tools/build_checked_combined.sh` successfully built the combined
initiator and responders 0 and 1 with west / NCS 3.2.4. There were no
`warning:` or `error:` diagnostics in `build/checked_combined_build.log`.
Compiler settings and image hashes are in
`build/checked_variants_combined_manifest.json`.

Host scheduling checks passed for these configurations:

| Responders | Attempts per peer per level |
|---:|---:|
| 2 | 10 (default) |
| 3 | 7 |
| 16 | 1 |

The checks count actual visits to each peer across every level of two cycles,
verify the descending 64-setting ladder and repeated TX octets, and check
gain correction and invalid RSSI handling. Analyzer tests passed for separate
peer/level grouping, missing peers, reset boundaries, partial sweeps, and
detecting an incorrect configured schedule. Previous real power/multi logs
produce exactly the same summaries after adding COMBINED support.

```bash
cc -std=c99 -Wall -Wextra -Werror -Isamples/twr_checked_combined_common \
  tools/test_checked_combined.c -o /tmp/test_checked_combined
/tmp/test_checked_combined
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_analyze_checked_combined.py
```

## Initial two-board hardware setup

Initially only two probes were programmed, preserving the earlier two-board
restriction. The later three-board run is recorded separately below.

| Probe | Firmware |
|---|---|
| 760201778 | Combined initiator, targets IDs 0 and 1 |
| 760201915 | Combined responder ID 0, fixed reply power |
| 760204734 | Unchanged; never programmed during this combined test |

Flash logs: `build/combined_flash.Z1Km2vrH/`. Each image was programmed and
verified through west/nrfutil with `--skip-rebuild`, responder before initiator.
Both serial ports were opened at 115200 with DTR asserted before resetting
the selected responder and then initiator.

The full UART capture is `build/combined_capture_20261111_150920/`. The capture
tool analyzes only the latest application startup, excluding buffered data
from before reset. With peer 1 absent, its error-2 records are expected and
must be retained in the attempt counts. The present peer's completion ratio
is the relevant link-health figure; global completion also counts absent peers.

## Full-sweep hardware result

The 260-second capture contains **1,331 consecutive attempt records**, sequences
1–1331. Responder 0 completed **666/666** exchanges, all with valid diagnostics.
Absent responder 1 completed **0/665**, with the expected error-2 records.
There were no range/interval error records, fatal/guard reports, responder
error reports, or dropped-log reports in either captured UART stream.

The first cycle completed all 64 settings, with exactly **10 attempts per peer
at every setting**. The initiator then returned to maximum power and began
cycle 1. There were 132 firmware level summaries (128 from the complete first
cycle and four from the next cycle). The configured peer/level/cycle/octet
schedule matched every recorded attempt. Printed global, per-peer and per-level
counters were checked against counts reconstructed independently from the log.

First-cycle measurements from responder 0:

| Level | Repeated TX octet | Completed / attempts | Median corrected RSSI (dB) |
|---:|---|---:|---:|
| 0 | FE | 10/10 | -64.068 |
| 16 | BE | 10/10 | -65.173 |
| 32 | 7E | 10/10 | -68.302 |
| 48 | 3E | 10/10 | -71.670 |
| 63 | 02 | 10/10 | -85.320 |

The full-cycle endpoint difference was **21.2525 dB**. The analyzer's pooled
endpoint difference across the complete first cycle and partial second cycle
was 21.092 dB. Adjacent-setting medians were not uniformly monotonic, as expected
when fine steps are compared using small samples with gain-state/fading noise.
Reported distance across the capture: median 379.5 mm, minimum 294 mm,
maximum 429 mm. Even the lowest setting completed 10/10 exchanges in the first
cycle; this geometry did not reach a reception cliff.

Selected unedited records demonstrate the changing setting and received strength:

```text
COMBINED seq=1 peer=0 dist_mm=378 final_rssi_mdB=-82162 diag=1 C=50 N=108 D=3 ok=1/1 peer_ok=1/1 cycle=0 level=0 octet=0xfe rssi_dgc_mdB=-64162 level_ok=1/1
COMBINED seq=641 peer=0 dist_mm=340 final_rssi_mdB=-80811 diag=1 C=67 N=107 D=2 ok=321/641 peer_ok=321/321 cycle=0 level=32 octet=0x7e rssi_dgc_mdB=-68811 level_ok=1/1
COMBINED seq=1261 peer=0 dist_mm=390 final_rssi_mdB=-85615 diag=1 C=23 N=109 D=0 ok=631/1261 peer_ok=631/631 cycle=0 level=63 octet=0x02 rssi_dgc_mdB=-85615 level_ok=1/1
COMBINED_LEVEL cycle=0 level=63 octet=0x02 peer=0 attempted=10 completed=10 valid_rssi=10 mean_dgc_mdB=-85411
COMBINED_LEVEL cycle=0 level=63 octet=0x02 peer=1 attempted=10 completed=0 valid_rssi=0 mean_dgc_mdB=-2147483648
```

Raw logs, `summary.json`, `analysis.json`, and `measurements.csv` are retained
under `build/combined_capture_20261111_150920/`. Build/source/validation hashes
are recorded in `build/checked_combined_validation.json`. At the end of that
initial test, both selected boards ran these combined images and the third
board was unchanged. The user subsequently authorized programming the third board.

## Three-board follow-up: both responders operating together

The user subsequently authorized programming the third board. All three
selected images were hash-checked, programmed and verified with west/nrfutil:

| Probe | Current firmware |
|---|---|
| 760201778 | Combined initiator, targets 0 and 1 |
| 760201915 | Combined responder ID 0 |
| 760204734 | Combined responder ID 1 |

Flash logs: `build/combined_flash.LEZrnors/`. Three UART streams were captured
after resetting the selected responders and then initiator. The capture is
`build/combined_capture_20261111_180916/`.

Both real responders completed the first full sweep, with exactly 10 attempts
per peer at all 64 settings. Peer 0 completed **638/640** exchanges; peer 1
completed **640/640**. Peer-0 radio errors occurred at sequences 59 and 113,
levels 2 and 5. At the lowest setting, both peers completed **10/10** exchanges.

First complete cycle, median DGC-corrected RSSI:

| Level | TX octet | Peer 0 (dB) | Peer 1 (dB) |
|---:|---|---:|---:|
| 0 | FE | -64.747 | -63.026 |
| 16 | BE | -65.030 | -64.218 |
| 32 | 7E | -68.892 | -65.456 |
| 48 | 3E | -71.357 | -70.166 |
| 63 | 02 | -85.247 | -83.911 |

The endpoint differences are **20.4995 dB** for peer 0 and **20.885 dB** for
peer 1. A visible power/RSSI trend is therefore observed concurrently at both
responders. These are measurements at the current geometry and do not establish
an absolute power calibration or a reception cutoff.

Actual consecutive successful records:

```text
COMBINED seq=1 peer=0 dist_mm=417 final_rssi_mdB=-83079 diag=1 C=39 N=106 D=3 ok=1/1 peer_ok=1/1 cycle=0 level=0 octet=0xfe rssi_dgc_mdB=-65079 level_ok=1/1
COMBINED seq=2 peer=1 dist_mm=861 final_rssi_mdB=-81308 diag=1 C=62 N=109 D=3 ok=2/2 peer_ok=1/1 cycle=0 level=0 octet=0xfe rssi_dgc_mdB=-63308 level_ok=1/1
```

The earlier missing-peer test remains a historical recovery check; peer 1 is
now present and running the combined responder firmware.

The final 260-second three-board capture contains **1,472 consecutive attempts**
and **1,469 completed exchanges**. Peer 0 completed **733/736** (99.59%);
peer 1 completed **736/736** (100%). Every completed exchange had valid RSSI.
Peer-0 median reported distance was 393 mm (310–436 mm); peer 1 was 864 mm
(791–918 mm). The initiator completed a full sweep and entered the next cycle.

All three UART streams had no detected fatal errors, dropped logs or responder
error reports. The three incomplete exchanges were initiator radio errors
(code 2) on peer 0. Global, per-peer and per-level counters matched reconstructed
counts, and the peer/level/cycle/octet schedule matched the compiled configuration.
Raw logs, JSON analysis and measurement CSV are in the capture directory;
`build/checked_combined_three_board_validation.json` records the image hashes,
all three probe assignments and validation findings. All three boards remain
running these combined images.

## Initial 01010101 probe: 65-setting firmware

At the user's request, the current firmware starts each cycle with
**`0x01010101`**, then retains the complete FE-to-02 sweep. There are now 65
settings: level 0 is octet 01 (coarse 1, fine 0), and levels 1–64 are the earlier
64 codes at coarse 2. The initial probe has the same 10-attempt-per-peer budget.
Replies remain fixed at **`0xFEFEFEFE`**; changing the first initiator setting
must not change responder TX power. Startup now explicitly selects fixed FE
for responders rather than deriving it from the first sweep entry.

All three images were rebuilt and their roles/IDs/hashes verified. Build log:
`build/checked_combined_01_build.log`; successful west/nrfutil flash logs:
`build/combined_flash.52Jzdh6v/`. Host schedule tests now cover the new initial
probe, all 64 subsequent codes, peer budgets, wrap, and fixed reply power.
Analyzer tests cover separating the 01 probe from the FE-to-02 endpoint comparison.
Earlier 64-setting capture summaries remain identical under the updated analyzer.

The 60-second capture `build/combined_capture_20261111_181925/` contains **340/340
completed exchanges**, sequences 1–340, with valid RSSI throughout and no detected
errors, panics, dropped logs or responder error reports on any UART stream.
The configured 65-setting schedule matched every recorded attempt. This capture
covers the initial probe and the following 16 settings, rather than an entire
new 65-setting cycle.

At **0x01010101 specifically**:

| Responder | Completed / attempts | Median corrected RSSI (dB) | Median reported distance (mm) |
|---|---:|---:|---:|
| Peer 0 | **10/10** | -86.5195 | 399 |
| Peer 1 | **10/10** | -84.9235 | 903.5 |

Both the initiator's Poll and Final use 01010101, so each completed exchange
demonstrates reception of those two frames at the selected responder. This
establishes reception in the tested 10-attempt windows at the current geometry;
it does not establish a long-term 100% one-way PRR.

Actual logs from that setting:

```text
COMBINED seq=1 peer=0 dist_mm=409 final_rssi_mdB=-86519 diag=1 C=18 N=107 D=0 ok=1/1 peer_ok=1/1 cycle=0 level=0 octet=0x01 rssi_dgc_mdB=-86519 level_ok=1/1
COMBINED seq=2 peer=1 dist_mm=902 final_rssi_mdB=-84681 diag=1 C=28 N=108 D=0 ok=2/2 peer_ok=1/1 cycle=0 level=0 octet=0x01 rssi_dgc_mdB=-84681 level_ok=1/1
COMBINED_LEVEL cycle=0 level=0 octet=0x01 peer=0 attempted=10 completed=10 valid_rssi=10 mean_dgc_mdB=-86594
COMBINED_LEVEL cycle=0 level=0 octet=0x01 peer=1 attempted=10 completed=10 valid_rssi=10 mean_dgc_mdB=-84977
```

Current image hashes, probe assignments, UART checks and probe analysis are in
`build/checked_combined_01_validation.json`. All three boards remain on the
updated firmware, starting each cycle at 01010101. Raw logs, JSON analysis and
measurement CSV are retained under the capture directory.

## Interpretation limits

All 64 codes are register settings; a one-code step does not establish an
equal or calibrated dB power step. Corrected RSSI uses the inherited vendor-model
`+6*D` term, while raw C/N/D and the legacy estimate remain visible. Small adjacent
steps can be obscured by fading and DGC fluctuations; individual level medians
need not decrease monotonically.

This two-board setup can check the whole power ladder, strict addressing,
per-peer/per-level counters, and recovery after every absent-peer attempt.
It cannot establish concurrent operation with two real responders. Reported
distance also has no supplied physical ground truth or pair-specific antenna
calibration. Four-frame DS-TWR completion does not measure one-way PRR or prove
a spatial reception cutoff at a chosen board.
