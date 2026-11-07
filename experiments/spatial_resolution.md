# Experiment: UWB Spatial Resolution via the Packet-Reception Cliff

**Status:** draft design
**Board:** DWM3001CDK (Qorvo DW3000, nRF52833)
**Firmware:** [`samples/spatial_resolution_tx`](../samples/spatial_resolution_tx) (transmitter) ·
[`samples/spatial_resolution_rx`](../samples/spatial_resolution_rx) (receiver + BLE)
**Collector:** [`tools/collect_spatial.py`](../tools/collect_spatial.py) (laptop)

---

## 1. Question

How *finely* can a UWB link distinguish position along a line? Concretely:
over what distance does a receiver go from **reliably hearing** the
transmitter to **not hearing it at all**? The width of that transition is
the "spatial resolution" we're after — the smallest spatial step at which
the link's behaviour changes from on to off.

## 2. Intuition / what we expect

Line up several receivers at known positions on a straight line, point one
transmitter down that line, and blast a long burst of packets. Plot the
**packet-reception ratio (PRR)** of each receiver against its position.

We expect a cliff, not a gentle slope:

```
PRR
100% |======o======o======o
      |                     \
      |                      \        <- the "cliff": how wide is it?
      |                       \
   0% |------------------------o======o======
      +----+----+----+----+----+----+----+---->  position along the line
          R1   R2   R3        R4   R5   R6
                      ^^^^^^^^
                 transition region = spatial resolution
```

In the sketch R3 still gets ~99% but R4 gets ~0%. The real boundary lies
somewhere between R3 and R4, and the **width of the uncertain region** is
what we want to measure. If it's a few cm, the link resolves position
sharply; if it's tens of cm, it's fuzzy.

## 3. Method — bracket, then zoom

This is the repositioning idea: find the cliff coarsely, then move the two
boards that bracket it into the gap to measure it finely.

1. **Coarse pass.** Place receivers at a regular pitch (e.g. 50 cm):
   R1…R6. Run one burst. Read each board's PRR off its console.
2. **Bracket.** Identify the adjacent pair straddling the cliff — the last
   high-PRR board (≈99%) and the first dead board (≈0%). Say that's R3/R4.
3. **Zoom.** Physically move R3 and R4 into the gap between their old
   positions as a new, finer pair (the "replace 3rd & 4th with 5 & 6, …"
   step) — e.g. put them at the 1/3 and 2/3 marks of the old R3–R4 gap.
   Re-run the burst.
4. **Repeat** step 3, halving the bracket each time, until the step size is
   below the resolution you care about or PRR stops being repeatable. The
   final bracket width is the measured spatial resolution.

Because every board reports its own PRR independently and the transmitter
doesn't care how many are listening, you can run all receivers
simultaneously in one burst — no need to move the transmitter.

> A receiver reporting **0%** stays silent (it can't count a burst it never
> heard). On the bench, treat "no output for a board during a burst" as 0%.
> The firmware prints a summary line only for boards that heard ≥1 packet.

## 4. Variables

- **Independent:** receiver position along the line (cm from TX).
- **Primary dependent:** PRR per receiver per burst (`received / N`).
- **Secondary dependent:** mean receive power estimate (RSSI, dB) — the PRR
  cliff should coincide with RSSI dropping through the sensitivity floor,
  which is the physical *why* behind the cliff and a sanity check that the
  cliff is an SNR edge and not a glitch.
- **Hold fixed:** channel, preamble length, PRF, data rate, TX power, TX
  antenna orientation, board height, burst length `N`, inter-packet
  interval. All of these move the cliff; only position should vary within a
  sweep.

## 5. Procedure detail

- Flash **one** board with `spatial_resolution_tx`, each receiver with
  `spatial_resolution_rx` after setting a distinct `RX_POSITION_ID` in its
  `src/main.c`.
- Transmitter sends bursts of `N` packets (default 500) at a fixed interval
  (default 10 ms → 5 s/burst), each packet tagged with an **epoch** (burst
  counter) and a **sequence number**. Between bursts it pauses
  (`INTER_BURST_MS`) so receivers can finalize and report.
- Each receiver counts unique sequence numbers seen within an epoch and, at
  end of burst (detected by epoch change or an RX gap longer than
  `RX_GAP_TIMEOUT_MS`), emits one line both to its UART **and over BLE**:
  `epoch, pos_id, received, N, PRR%, mean_rssi_dB`.
- Record several bursts per geometry and keep the per-burst PRR, not just
  the average, so you can see variance near the cliff.

## 6. Data path & recording

```
 TX board ──UWB──▶ RX board(s) ──BLE (NUS notify)──▶ laptop (collect_spatial.py) ──▶ CSV
```

Each `spatial_resolution_rx` board advertises as **`DWM3001-RX`** and
exposes the Nordic UART Service. The laptop runs the collector, which scans
for **every** advertising receiver, connects to all of them at once,
subscribes to notifications, and merges them into one CSV tagged by BLE
address and `pos_id`:

```bash
pip install bleak
python tools/collect_spatial.py --csv captures/spatial/run1.csv
# or a fixed window:
python tools/collect_spatial.py --csv captures/spatial/run1.csv --duration 120
```

The on-wire BLE line is all-integer (`epoch,pos,recv,N,prr_hundredths,
rssi_millidb`); the collector converts it to a CSV row:

| wall_time | device | epoch | pos | received | N | prr_pct | rssi_db |
|-----------|--------|-------|-----|----------|---|---------|---------|

UART still prints a human-readable copy, so you can also capture per-board
serial logs if BLE drops.

## 7. Analysis

- Plot PRR vs. position for each pass; overlay successive zoom passes.
- Define the cliff edges as the positions where PRR crosses, say, 95% and
  5%. The spatial resolution estimate is the distance between those two
  crossings (interpolate between boards).
- Cross-check against RSSI: the 95%→5% band should line up with RSSI
  passing through the receiver sensitivity floor.

## 8. Caveats (keep the ground truth honest)

- **Measure, don't assume, the positions.** Tape-measure every board; the
  whole result is a distance, so position error is error-for-error.
- **Multipath / reflections will smear the cliff.** A reflected copy can
  keep a "dead" board alive and widen the apparent transition. Run in as
  open/anechoic a space as you can, keep boards at constant height, and
  note the environment. The clean measurement is the **direct-path** cliff;
  if the cliff is ragged or non-monotonic, suspect reflections before
  trusting the number.
- **Orientation matters.** DW3000 antennas aren't isotropic. Fix the TX and
  all RX orientations and record them.
- **It's a link-budget edge, not a hard wall.** The cliff position depends
  on TX power, channel, preamble length and data rate. Report the
  resolution *together with* those settings; changing any of them moves the
  cliff.
- **Repeatability near the edge.** PRR right at the cliff is noisy by
  nature. Use multiple bursts and report variance, not a single number.

## 9. Firmware config knobs

**TX** — top of [`samples/spatial_resolution_tx/src/main.c`](../samples/spatial_resolution_tx/src/main.c):

| macro | meaning | default |
|-------|---------|---------|
| `BURST_LEN` | packets per burst, `N` | `500` |
| `TX_INTERVAL_MS` | gap between packets | `10` |
| `INTER_BURST_MS` | pause between bursts | `1500` |

**RX** — top of [`samples/spatial_resolution_rx/src/main.c`](../samples/spatial_resolution_rx/src/main.c):

| macro | meaning | default |
|-------|---------|---------|
| `RX_POSITION_ID` | per-board label in logs/BLE (**set per receiver**) | `1` |
| `BURST_LEN` | must match the TX app's `N` | `500` |
| `RX_GAP_TIMEOUT_MS` | RX silence that ends a burst | `300` |
| `LOG_RSSI` | compute/send mean RSSI | `1` |

The BLE device name is `CONFIG_BT_DEVICE_NAME` in the RX app's `prj.conf`
(default `DWM3001-RX`). The UWB PHY config (channel 9, PLEN 128, 6.8 Mbps,
PRF 64 MHz, STS off) matches `samples/simple_txrx` and **must be identical
on TX and all RX**.

## 10. Build & flash

```bash
source tools/ncs_env.sh

# transmitter board
west build -b decawave_dwm3001cdk samples/spatial_resolution_tx && west flash

# each receiver board (edit RX_POSITION_ID first), e.g. pristine build dir per board
west build -p -b decawave_dwm3001cdk samples/spatial_resolution_rx && west flash
```
