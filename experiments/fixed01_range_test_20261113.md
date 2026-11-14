# Fixed 01010101 range-test firmware

Date: 2026-11-13. Requested experiment: move two responders onto external power
and find how far the initiator's 01010101 transmissions can be received.
Implementation: [fixed01 shared guide](../samples/twr_checked_fixed01_common/README.md).

## Programmed boards

| Role | Serial | Fixed01 peer ID |
|---|---|---|
| Same BLE initiator | 760201778 | Targets 0 and 1 |
| Responder formerly sweep peer 1 | 760204734 | 0 |
| Responder formerly sweep peer 2 | 760204645 | 1 |

The separately powered 760201915 was not programmed. The new experiment uses
protocol 5, so that board's older protocol-4 responder does not participate.
Radio settings and frame structure are inherited from the checked combined
implementation; its earlier source and builds remain separate.

## Fixed settings

- Initiator Poll and Final: **0x01010101 at every attempt**.
- Responder Response and Result: **0xFEFEFEFE**, to isolate the weak forward link.
- Channel 9, code 9, 128-symbol preamble, 6.8 Mbps, DW-8 SFD, STS off.
- Two responders alternate after every attempt, including failures.
- One power level; 20 attempts per peer per reporting window, 40 attempts total.
- A new cycle is a statistics window, not a change in power.
- BLE name UWB-COEX-INIT; address CB:56:11:3C:AB:ED on this initiator.

The fixed power is implemented by a separate plan that returns 01 for every
level argument and always returns level 0. The checked C implementation differs
from the combined reference only in its protocol version and explicit fixed-mode
banners. No ranging-timestamp or diagnostic timing logic was modified.

## Build and flash

```bash
bash tools/build_checked_fixed01.sh
bash tools/flash_checked_variant.sh fixed01 760201778 760204734 760204645
```

All three images built with NCS 3.2.4/west. The builder verified compiler role,
responder ID, two-target count, RSSI selection and BLE selection for the initiator.
Image hashes and compiler commands are in
`build/checked_variants_fixed01_manifest.json`.

Flashing verified each programmed image and reset both responders, then the
initiator. Logs: `build/checked_fixed01_flash_console.log` and
`build/fixed01_flash.zghYplMw/`. No previous sweep image was overwritten on disk.

## Host checks

- Fixed-plan C test passed across 10000 attempts: power invariant, round-robin
  addressing, reporting windows, FE replies and DGC checks.
- Three fixed-mode analyzer tests passed, including absent-peer failures and
  rejection of changed TX power/reporting cycles.
- Five existing combined analyzer tests and four three-responder summary tests
  passed after adding single-level fixed-mode analysis.
- The previously saved LOS sweep log produced an identical summary after the
  analyzer change. Existing sweep interpretation was preserved.
- Build/flash shell syntax checks passed.

## BLE validation capture

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py \
  --seconds 60 --address CB:56:11:3C:AB:ED --quiet \
  --out experiments/data/2026-11-13/fixed01_validation
```

The 60-second BLE-only capture saved **337 consecutive attempts**, with
**318 completed exchanges** and valid diagnostics for every completed exchange.
The ready banner reported targets=2, levels=1, mode=fixed and
tx_power=0x01010101. Every measurement/error record used level 0/octet 01
across nine observed reporting windows (eight full windows and one partial).
The fixed-power schedule check passed.

| Fixed01 peer | Serial | Completed / attempts | Median reported range (m) | Median corrected RSSI (dB) |
|---|---|---:|---:|---:|
| 0 | 760204734 | 150/169 | 1.7420 | -92.969 |
| 1 | 760204645 | 168/168 | 0.7725 | -85.162 |

All 19 failures were peer-0 radio error code 2. No range/interval error records
or fatal reports appeared. Reported successful ranges spanned 1665–1862 mm for
peer 0 and 734–1258 mm for peer 1; the latter includes an outlying range and
should not be mistaken for independently measured movement.

BLE had one connection and no connection errors. It reported no sequence gaps,
duplicates, out-of-order records, framing errors, discarded partial bytes,
queue drops or transport replays. Each individual CSV record matched the raw
log fields; valid RSSI corrections matched `final_rssi_mdB + 6000*D` exactly.
Final STATUS showed running=0 and queue=0, ready for a new START.

The missing exchanges establish reduced full-transaction completion in this
short window, not an isolated measurement of which weak frame was lost. The
user's external-power walking test has not yet been performed in this record.

Saved evidence:

- [Individual readings](data/2026-11-13/fixed01_validation/measurements.csv)
- [Raw BLE log](data/2026-11-13/fixed01_validation/init.log)
- [Capture/transport metrics](data/2026-11-13/fixed01_validation/capture.json)
- [Per-peer summary](data/2026-11-13/fixed01_validation/summary.json)
- [Power invariant, image hashes and source checks](data/2026-11-13/fixed01_validation/validation.json)

## External-power walking test

Keep the initiator by the laptop, move both responders to external USB supplies,
then run the collector with a new output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/collect_checked_ble.py \
  --seconds 3600 --address CB:56:11:3C:AB:ED \
  --out experiments/data/fixed01_walk_NEW_RUN
```

START resets counters and starts the fixed-power ranging. Power remains 01
through errors, position changes and reporting windows. The host saves individual
timestamps, peer ID, range, RSSI, errors, raw C/N/D and BLE integrity metrics.
Only the initiator needs Bluetooth range to the laptop.

A failed ranging exchange is not proof of zero frame reception. This instrument
measures full DS-TWR completion and successful-Final RSSI, not one-way PRR.
The inherited range guard is -2 to 100 m. RSSI is uncalibrated dB, not absolute
dBm. No moved-distance validation or maximum operating range is claimed by
the initial stationary capture.
