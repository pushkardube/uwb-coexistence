# Power threshold analysis: opposite-facing three-responder sweep

Analyzed 2026-11-14 from the complete first cycle of the
[ascending sweep](opposite_facing_ascending_sweep_20261114.md).

The clearest sustained low-power drop occurs at the farthest responder.
**0A0A0A0A is the strongest selective-reception candidate observed in this
sample:** the two nearer peers completed 20/20 ranging exchanges each, while
the farthest completed 0/20. This is a candidate for repeated testing, not an
established long-term 100%/0% reception boundary.

## Source and measurement conditions

- [Complete first-cycle CSV](data/2026-11-14/opposite_facing_ascending_sweep_run1/cycle0_rssi_by_tx_setting.csv).
- [Individual readings and errors](data/2026-11-14/opposite_facing_ascending_sweep_run1/measurements.csv).
- [Validation and provenance](data/2026-11-14/opposite_facing_ascending_sweep_run1/validation.json).
- Initiator: 760201915; three addressed responders, protocol 4.
- Actual acquisition order: 01010101, 02020202, 06060606, ... FEFEFEFE.
- 65 settings, 20 attempts per responder per setting: 3900 attempts total.
- Initiator Poll/Final power varied; responder Response/Result power stayed FEFEFEFE.
- The user described the antennas as facing in opposite directions. Exact
  angles and tape-measured distances were not supplied.

The tables below are presented from **stronger to weaker** settings to make the
onset of losses easier to read. This reverses the display order only; the actual
capture proceeded upwards in nominal gain. No measurements have been changed.

## Responders and distance reference

Distances here are the median **UWB-reported range at FEFEFEFE**, where every
peer completed 20/20. They identify the approximate near/middle/far arrangement;
they are not tape ground truth or a substituted low-power range measurement.

| Position | Peer | Board serial | Median range at FE (m) | Median corrected RSSI at FE (dB) |
|---|---:|---|---:|---:|
| Nearest | 0 | 760201778 | 0.8630 | -64.0345 |
| Middle | 2 | 760204645 | 1.8945 | -70.8685 |
| Farthest | 1 | 760204734 | 2.1545 | -75.4160 |

## Low-power transition

Each count is a completed four-message ranging exchange divided by 20 attempts.
The received-power values are estimates, so register settings are used directly
rather than assigning them an unmeasured emitted dBm value.

| Initiator TX_POWER | Peer 0: near, ~0.86 m | Peer 2: middle, ~1.89 m | Peer 1: far, ~2.15 m |
|---|---:|---:|---:|
| 0x16161616 | 20/20 | 19/20 | 20/20 |
| 0x12121212 | 20/20 | 20/20 | 19/20 |
| 0x0E0E0E0E | 19/20 | 20/20 | 10/20 |
| 0x0A0A0A0A | 20/20 | 20/20 | 0/20 |
| 0x06060606 | 20/20 | 17/20 | 0/20 |
| 0x02020202 | 20/20 | 8/20 | 0/20 |
| 0x01010101 | 20/20 | 1/20 | 0/20 |

### Farthest: peer 1, approximately 2.15 m

Every setting from 16161616 through FEFEFEFE completed 20/20. Moving downwards,
completion first falls to **19/20 at 12121212**, then **10/20 at 0E0E0E0E**,
and **0/20 at 0A0A0A0A and every weaker tested setting**.

This is the clearest sustained power-associated transition in this run. Median
corrected RSSI among successful frames was approximately -94.14 dB at 12121212
and -94.30 dB at 0E0E0E0E. There is no valid received-frame RSSI at settings
where no exchange completed. These estimates are not calibrated dBm or an
independently measured receiver sensitivity.

### Middle: peer 2, approximately 1.89 m

The low-power decline appears below 0A0A0A0A: **17/20 at 06060606**,
**8/20 at 02020202**, and **1/20 at 01010101**. At 0A0A0A0A itself this peer
completed 20/20.

There were also isolated single losses at 16161616 and B6B6B6B6, each 19/20.
Consequently there is no perfectly monotonic guarantee across all settings;
those isolated failures should not be confused with the sustained low-power
transition or removed from the evidence.

### Nearest: peer 0, approximately 0.86 m

This peer completed **20/20 even at 01010101**, so a low-power cutoff for the
nearest peer was not reached. It had four isolated failed exchanges across the
whole cycle: one each at 0E0E0E0E, 52525252, AEAEAEAE and BABABABA. Other settings
completed 20/20. Those isolated failures are not a progressively worsening
low-power boundary.

## Selective setting worth repeating

At **0A0A0A0A**:

| Peer | Completed / attempts | Observed completion fraction |
|---|---:|---:|
| 0: nearest | 20/20 | 100% |
| 2: middle | 20/20 | 100% |
| 1: farthest | 0/20 | 0% |

This is the only tested setting in this cycle where both nearer peers completed
all 20 attempts while the farthest completed none. Weaker settings also lose
middle-peer exchanges; the next stronger setting, 0E0E0E0E, already completes
10/20 at the farthest peer and has one isolated nearest-peer failure.

## Comparison with the earlier LOS, directly facing run

The user describes the earlier 2026-11-13 layout as completely LOS with the
boards directly facing one another. It is compared here with the 2026-11-14
opposite-facing run. These orientation descriptions are user-supplied; exact
antenna angles and tape-measured separations were not recorded.

Sources:

- [Earlier LOS/facing-each-other complete-cycle CSV](data/2026-11-13/los_three_responders_run1/cycle0_rssi_by_tx_setting.csv)
  and [its experiment report](los_three_responder_rssi_20261113.md).
- [Opposite-facing ascending complete-cycle CSV](data/2026-11-14/opposite_facing_ascending_sweep_run1/cycle0_rssi_by_tx_setting.csv)
  and [its experiment report](opposite_facing_ascending_sweep_20261114.md).

Both datasets contain the same 65 TX register settings, 20 attempts per peer
per setting, protocol-4 ranging and FEFEFEFE responder replies. Both were
collected over BLE. Only the first complete cycle of each run is used below;
partial second-cycle records are excluded.

### Match positions and boards before comparing counts

Peer numbers do not identify the same physical position in the two runs.
The initiating board changed from **760201778** to **760201915**; those two
boards swapped initiator/responder roles. The near/middle/far ordering and
reported distances also changed.

The following positional comparison uses median UWB-reported distances at
FEFEFEFE. It does not imply equal physical separation or an identical board
at each position.

| Position | Facing-each-other board (peer) | Earlier range at FE (m) | Opposite-facing board (peer) | Later range at FE (m) |
|---|---|---:|---|---:|
| Nearest | 760204645 (2) | 0.7470 | 760201778 (0) | 0.8630 |
| Middle | 760204734 (1) | 1.7515 | 760204645 (2) | 1.8945 |
| Farthest | 760201915 (0) | 2.8120 | 760204734 (1) | 2.1545 |

### Low-power completion comparison

Each entry is completed ranging exchanges / 20 attempts. The table is displayed
from stronger to weaker settings, matching the threshold discussion above.

| TX_POWER | Facing: near | Facing: middle | Facing: far | Opposite: near | Opposite: middle | Opposite: far |
|---|---:|---:|---:|---:|---:|---:|
| 0x16161616 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 | 20/20 |
| 0x12121212 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 |
| 0x0E0E0E0E | 20/20 | 20/20 | 20/20 | 19/20 | 20/20 | 10/20 |
| 0x0A0A0A0A | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 0/20 |
| 0x06060606 | 20/20 | 20/20 | 20/20 | 20/20 | 17/20 | 0/20 |
| 0x02020202 | 20/20 | 20/20 | 20/20 | 20/20 | 8/20 | 0/20 |
| 0x01010101 | 20/20 | 20/20 | 20/20 | 20/20 | 1/20 | 0/20 |

In the facing-each-other run, **all three responders completed 20/20 even at
01010101**, including the farthest at approximately 2.81 m. No sustained
low-power completion cutoff was reached in that earlier capture.

In the opposite-facing run, the farthest responder at approximately 2.15 m
completed 0/20 at 0A0A0A0A and below, while the middle responder declined below
0A0A0A0A. The earlier run had **no setting** with two peers at 20/20 and one at
0/20. The later run had exactly one such setting: **0A0A0A0A**.

Therefore the useful selective result was observed only in the later setup;
it cannot be assumed to hold for the earlier facing-each-other arrangement.
The shorter farthest reported distance in the later run also shows that distance
alone does not account for the observed difference.

### Whole-cycle completion

| Position | Facing each other | Opposite-facing |
|---|---:|---:|
| Nearest | 1298/1300 | 1296/1300 |
| Middle | 1300/1300 | 1264/1300 |
| Farthest | 1300/1300 | 1209/1300 |
| **All three** | **3898/3900 (99.95%)** | **3769/3900 (96.64%)** |

The earlier run's two failures were isolated nearest-peer losses at 3E3E3E3E
and 46464646. It did not show the sustained low-power decline seen later.
The later run retained 131 failures, including the isolated stronger-setting
losses already listed above. No failure records were removed from either count.

### RSSI comparison for boards that remained responders

Boards 760204734 and 760204645 were responders in both captures, but their
ranges and near/middle/far positions changed. At FEFEFEFE, all groups below had
20 successful readings, making these particular medians less affected by
missing low-power samples.

| Board | Earlier range at FE (m) | Later range at FE (m) | Earlier median RSSI (dB) | Later median RSSI (dB) | Later minus earlier (dB) |
|---|---:|---:|---:|---:|---:|
| 760204734 | 1.7515 | 2.1545 | -69.0165 | -75.4160 | -6.3995 |
| 760204645 | 0.7470 | 1.8945 | -63.1705 | -70.8685 | -7.6980 |

These are descriptive differences between the two recorded setups, **not
measured antenna-orientation losses**. They cannot be converted directly into
dB per metre or a correction for antenna angle. At settings with 0/20 completed
exchanges, there is no valid RSSI median to subtract; do not replace it with an
invented sensitivity-floor value.

### What the comparison supports and what remains uncontrolled

The later setup showed weaker usable links and a pronounced low-power transition
that was absent in the earlier LOS run. That is consistent with orientation
being important, but this pair of captures does not isolate its causal effect:

- The initiating physical board changed, and boards changed positions/roles.
- The reported distances changed; they are not independent tape measurements.
- Acquisition order changed: the earlier run used 01,FE,FA,...,02, while the
  later run used 01,02,06,...,FE.
- Measurements were taken at different times, with no independently controlled
  multipath environment or recorded exact antenna angles.
- RSSI is an uncalibrated estimate conditional on successfully received frames.

For an orientation-only comparison, retain the same initiator, responder boards,
positions, heights and TX-setting order, then change only antenna orientation
and repeat the measurements. The current data establishes a difference between
two setups; it does not establish a universal orientation penalty or a guaranteed
reception boundary.

## Interpretation and next measurement

These are **observed fractions from 20 attempts**, not guarantees of true
100% or 0% reception probabilities. A completed TWR exchange requires Poll,
Response, Final and Result; a failed exchange does not identify which frame
was lost or establish that no UWB energy reached the responder. Failed entries
must remain failed attempts, not zero RSSI or invented distances.

Repeat 0A0A0A0A at the same fixed geometry with substantially more attempts,
then repeat adjacent settings and board/position swaps. That would test whether
the separation persists across time and board variation. A one-way numbered
burst instrument is needed before describing these full-TWR counts as one-way
packet-reception probabilities.

This analysis does not fit dB per metre or a universal distance cutoff. Antenna
orientation, multipath, board calibration and successful-frame selection affect
interpretation. The prior LOS run also used a different initiating board, so
the two runs do not isolate orientation alone.
