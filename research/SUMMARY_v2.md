# SteelSeries Sensei Pro / Rival Pro: UWB Mouse Research Summary (v2)

Written 2026-11-02 to prepare for the co-existence project talk with Ashutosh. Updated 2026-11-03 after checking every claim against the saved pages. The list of changes is at the end. The old version is still in `SUMMARY.md`.

How to read the labels:
- *(my guess)* = my own reasoning, not something a source says.
- *(not checked)* = the page it came from could not be saved, so I could not check it.
- *(background)* = general UWB knowledge, not from the saved pages.

## What's in this folder

```
uwb_coexistence_research/
├── SUMMARY.md       <- old summary (v1)
├── SUMMARY_v2.md    <- this file
├── MOUSE_VS_RANGING_INTERFERENCE.md  <- why the mouse is a different problem from other ranging devices
├── DW1000_TX_POWER_NOTES.md          <- Ashutosh's TX power code + register → gain table
├── sources/         <- the web pages as downloaded (HTML)
└── text/            <- the same pages as plain text (easier to search)
```

| # | File | Source | What it is |
|---|------|--------|------------|
| 01 | `01_steelseries_press_release` | [SteelSeries press](https://steelseries.com/press/165-steelseries-unleashes-ultra-wideband-uwb-for-unbridled-8k-performance-all) | Official launch announcement: frequency band, battery, price |
| 02 | `02_steelseries_product_page` | [SteelSeries LP](https://steelseries.com/gaming-products/sensei-rival-pro-lp) | Product page |
| 03 | `03_hothardware` | [HotHardware](https://hothardware.com/news/steelseries-rival-pro-sensei-pro-ultra-wideband) | News: "6.4 GHz band", "multiple channels" |
| 04 | `04_slashgear_review` | [SlashGear](https://www.slashgear.com/2276269/steelseries-senesi-pro-x-rival-pro-review/) | Review: base station, polling numbers (copied from SteelSeries, not tested), using two computers |
| 07 | `07_notebookcheck` | [Notebookcheck](https://www.notebookcheck.net/SteelSeries-Sensei-Pro-Rival-Pro-series-gaming-mice-boast-UWB-8K-connectivity-and-infinite-battery.1411249.0.html) | News: "9K over-polling", sensor model, battery size |
| 10 | `10_tomsguide_review` | [Tom's Guide](https://www.tomsguide.com/gaming/gaming-peripherals/steelseries-rival-pro-sensei-pro-review) | Most detailed review: how 9K works, range, the AirTag comment |
| 11 | `11_pcgamer_review` | [PC Gamer](https://www.pcgamer.com/hardware/gaming-mice/no-usb-connectivity-like-at-all-its-a-good-job-steelseries-new-gaming-mice-are-two-of-the-best-ive-felt-under-my-fingertips/) | Review: "one packet + one reply" at 8K; the mouse has no USB port |
| 12 | `12_fccid_ZHK-M033` | [fccid.io ZHK-M033](https://fccid.io/ZHK-M033) | **FCC approval record: frequency, bandwidth, rules, list of documents** |

Numbers 05, 06, 08 and 09 are missing because those pages failed to download (see below).

**Pages that blocked the download. Open them in a browser if you need them:**
- [Aroged article](https://www.aroged.com/2026/09/29/steelseries-launches-sensei-pro-and-rival-pro-wireless-gaming-mice-with-broadband-wireless-connectivity/)
- [Scan UK shop listing](https://www.scan.co.uk/products/steelseries-sensei-pro-wireless-gaming-mouse-black-optical-truemove-42k-pro-sensor-42k-dpi-6-buttons) (where the "1 m range" figure came from)
- [Manuals+ user guide](https://manuals.plus/steelseries/sensei-pro-wireless-gaming-mouse-manual). You don't need this one: the same manual is free on the FCC site (below).
- [BusinessWire: Waizowl mouse uses SPARK Microsystems UWB](https://www.businesswire.com/news/home/20250715760073/en/Waizowl-Leads-Wireless-Gaming-Revolution-with-New-Cloud-Ultra-Gaming-Mouse-Powered-by-SPARK-Microsystems)

**FCC documents to download by hand** (the site blocks scripts). Save them in `sources/`. Most useful first:

| Document | Why it's useful |
|---|---|
| [Test Report rev 5](https://fccid.io/ZHK-M033/Test-Report/Test-Report-rev-5-9246576) | The lab's measurements: signal strength, the shape of the signal across frequency, maybe how often it transmits |
| [Internal Photos](https://fccid.io/ZHK-M033/Internal-Photos/Internal-Photos-9246535) | Should show which radio chip is inside |
| [RF Exposure Info (MPE)](https://fccid.io/ZHK-M033/RF-Exposure-Info/RF-Exposure-Info-MPE-9246575) | Often gives the transmit power |
| [Users Manual rev 2](https://fccid.io/ZHK-M033/User-Manual/Users-Manual-rev-2-9269121) | The official manual; may give the range |
| [Antenna Datasheet](https://fccid.io/ZHK-M033/Test-Report/Antenna-Datasheet-rev-9246568) | Antenna details |
| [Test Set Up Photos](https://fccid.io/ZHK-M033/Test-Setup-Photos/Test-Set-Up-Photos-9246536) | How the lab set up the mouse for testing |
| [External Photos](https://fccid.io/ZHK-M033/External-Photos/External-Photos-9246534) | Photos of the outside, including the base station |

The block diagram, circuit diagrams and the technical description of how the radio works are kept secret long-term. They are **not** public.

---

## The product

- **Announced** 29 Sept 2026 (pre-orders). **In shops** 13 Oct 2026. Price $179.99.
- **Four mice:** Sensei Pro (same shape both sides) and Rival Pro (shaped for the right hand), each in normal and Mini size.
  - Weight: 53 g normal, 49 g Mini. HotHardware says the Rival Pro is 54 g. Notebookcheck says the white versions weigh 1 g more.
- **Who made it:** SteelSeries is owned by GN, the company that also owns Jabra. The FCC filing is under GN Audio USA Inc. The testing lab is Bureau Veritas in Taoyuan, Taiwan.
- **Sensor:** TrueMove 42K Pro, a modified PixArt PAW3955.
- **The mouse has no USB port at all** (PC Gamer). It can never be used with a cable. It always talks by UWB radio to the base station or the travel dongle. (Tom's Guide lists "Wired", but that means the base station's cable to the PC.)
- SteelSeries calls them "the world's first pure UWB wireless mice with true 8K performance".

## Why use UWB in a mouse at all?

Most people know UWB from AirTags and phones, where it's used to **measure distance and find things**. This mouse doesn't do that. It uses UWB only as a **data radio**, the same job Bluetooth or a normal 2.4 GHz dongle does. Nothing in any source mentions distance measurement.

**Why SteelSeries says it's better:**
1. **Less crowded.** Almost every wireless mouse, keyboard, headset, Wi-Fi router and Bluetooth device uses 2.4 GHz. At a gaming event or in a busy flat, that band gets crowded and packets get lost. The 6 to 9 GHz range has far fewer users.
2. **Much wider.** The whole 2.4 GHz band is only 83.5 MHz wide *(background)*. The mouse's signal is about 1,668 MHz wide. 83.5 × 20 ≈ 1,670, so this is probably where SteelSeries' "20x the bandwidth" claim comes from *(my guess)*.
3. **Wide signal = very short packets** *(background)*. A wider signal can carry the same data in less time. That makes it easier to send a report 8,000 to 9,000 times a second and still have time for a reply after each one.
4. **Harder to knock out** *(background)*. Because the signal is spread over a wide range, a narrow interferer (like one Wi-Fi channel) only hits a small part of it.

**The catch:**
- **Very short range.** US rules only allow UWB at a very low power level *(background)*. That's why the range is "just enough for a mousemat", about 1 m.
- **Uses a lot of battery.** 16 hours per battery at 8K, which is why it comes with two swappable batteries.
- **Is it actually better?** Normal 2.4 GHz 8K mice already work fine for most people. The real benefit is in crowded radio environments. No review in this folder has measured whether UWB actually drops fewer packets. That is a marketing claim.
- **6 to 9 GHz isn't empty either** *(background)*. Wi-Fi 6E and Wi-Fi 7 use 5.925 to 7.125 GHz in the US. That overlaps the bottom part of the mouse's band.

**Why it matters for our project:** UWB being useful for the mouse isn't really our question. What matters is that a cheap, popular gadget is now **sending UWB signals thousands of times per second, right next to phones, tags and ranging boards.** Nobody has tested whether that hurts UWB distance measurement. That's the research gap.

## How the radio works (what's public)

### From the FCC approval (official facts)

| Field | Value |
|---|---|
| FCC ID | ZHK-M033 (model M033) |
| Type of device | **UWB transmitter** |
| Rules it was approved under | **FCC Part 15, Subpart F** (the UWB rules; it mentions §15.519 for handheld devices and §15.521) |
| Centre frequency | **7290.88 MHz** (the only frequency listed) |
| Bandwidth (width of the signal where it's within 10 dB of its peak) | **1.6678 GHz**. If the signal is centred evenly, that's about **6.457 to 8.125 GHz** |
| Approval date | 5 May 2026 |

**Why this matters for co-existence:** standard UWB (802.15.4z, used by phones, tags and the DW3000 board) uses channels about 0.5 GHz wide:
- Channel 5: centre 6489.6 MHz, about 6.24 to 6.74 GHz
- Channel 9: centre 7987.2 MHz, about 7.74 to 8.24 GHz

The mouse's signal (about 6.46 to 8.12 GHz) **covers the top ~57% of channel 5, ~78% of channel 9, and everything in between.** So one mouse can disturb *both* main UWB channels at the same time. (The saved pages don't say which channels each phone or tag uses. Check that separately.)

The mouse's signal is more than 3 times wider than one normal UWB channel (1.67 GHz vs 0.5 GHz). Two possible reasons:
- it sends very short pulses (shorter pulse = wider signal), or
- it uses several channels at once, as SteelSeries claims, either as one wide signal or by jumping between channels very fast.

The FCC record lists just one frequency. That points to one wide signal rather than jumping, but it doesn't prove it. The test report should tell us.

### The numbers don't match: SteelSeries vs FCC

| | Range | Width |
|---|---|---|
| SteelSeries announcement | 6.4 to 9.056 GHz | ~2.66 GHz |
| FCC measurement | ~6.457 to ~8.125 GHz | 1.67 GHz |

SteelSeries' range is about 1 GHz wider and goes almost 1 GHz higher. Possible reasons:
- SteelSeries is quoting the range the chip *can* use, not what it actually sends.
- The mouse has other modes or channels that the FCC didn't measure as one signal.
- The signal isn't centred evenly around 7290.88 MHz.

The "20x" claim fits the 1.67 GHz FCC number, not the 2.66 GHz range *(my guess)*. **Check the test report's graphs.** If the signal really reaches 9 GHz, channel 9 is fully covered.

### What SteelSeries and the reviews say

- **Frequency:** "6.4 GHz to 9.056 GHz", "roughly 20x the bandwidth" of 2.4 GHz, and it "can leverage multiple wireless channels simultaneously" (announcement).
- **One reply per packet (PC Gamer):** "True 8K" means the mouse "apparently" sends **one packet and gets one reply back (an ACK, short for acknowledgement)** for each of the 8,000 reports per second. Most 2.4 GHz mice group reports together instead. The reviewer heard this from SteelSeries; they didn't test it.
- **"9K over-polling" (Tom's Guide, Notebookcheck):** the radio actually runs 9,000 times a second. After every 8 packets it sends a 9th as a backup, in case one gets lost. This makes sure 8,000 always get through.
- **Putting those two together** *(my guess)*: about **9,000 packets a second from the mouse, plus up to 9,000 replies a second from the base station.** So **both sides are transmitting almost all the time.** No source says this directly.
- **Polling numbers (SlashGear):** 8,000 Hz (one report every 0.125 ms), and up to 9,000 Hz (every 0.111 ms). These are SteelSeries' numbers, **not tested by the reviewer**.
- **Settings (SlashGear, Tom's Guide):** you can set the polling rate and the sensor rate to 125, 250, 500, 1K, 2K, 4K or 8K Hz. There are 5 presets (1K to 8K by default) that you switch with the button on the base station. Clicks and movement can use different rates.
- **Range:** "very short, but enough to cover a mousemat" (Tom's Guide). A shop lists **1 m** *(not checked)*. *(my guess)* So it probably transmits at much less than the legal maximum.
- **Base station:** plugs into a PC, Xbox Series X/S or PS5 with a USB-C to USB-A cable, and charges the spare battery. A $24.99 USB-C **travel dongle** can be a second receiver. The mouse connects to whichever one is on. If both are on, you switch by holding the Power/DPI button and pressing the scroll wheel.
- **Battery:** 310 mAh. About 16 hours at 8K or 60 hours at 1K per battery.
- **Tom's Guide on interference:** they say another UWB device (like an AirTag) on the desk "won't be an issue" because "most UWB devices use a very narrow channel". **They didn't test this.** It's a guess, and **testing it is our research opportunity.**

### Still unknown

- **Which radio chip:** nobody has opened one up and named it. The FCC internal photos should show it.
  - **Possible lead** *(not checked)*: SPARK Microsystems (Montreal) makes low-power UWB chips for data (SR1000 family, SR1120). Their chips are said to be in the Waizowl Cloud Ultra gaming mouse. No proof SteelSeries uses them.
  - Other options: Qorvo or NXP, but those focus on distance measurement, so less likely.
- **Standard UWB or their own system:** *(my guess)* almost certainly SteelSeries' own data system, not standard 802.15.4z. Nothing mentions distance measurement or the usual UWB standards (STS, FiRa).
- **Signal details, channel use, and what it does when it hits interference:** not public. That document is kept secret.
- **Radio delay:** the "0.35 ms" in the ads is for the click buttons, not the radio.

## Other devices worth knowing about

- **Cherry XTRFY K63W Pro Compact:** "the world's first ultra-wideband mechanical gaming keyboard" (Tom's Guide). **Another UWB device that could sit on the same desk as the mouse.**
- **Waizowl Cloud Ultra:** a gaming mouse said to use SPARK Microsystems UWB *(not checked)*.
- **Normal 2.4 GHz gaming mice** (Logitech G Pro X Superlight 2, Razer Viper V4 Pro) for comparison. Tom's Guide confirms both use 2.4 GHz. The Viper V4 Pro does 8K. The saved pages don't say whether the Superlight 2 does.

---

## What this means for the project

1. **A cheap, real interferer you can buy in a shop.** A $180 mouse sending about 9,000 packets a second, probably with replies coming back *(my guess)*, across ~6.46 to 8.12 GHz (maybe wider), is about as bad a neighbour as standard UWB on channels 5 and 9 could get.
2. **First experiment:** run DW3000 two-way ranging (two boards measuring the distance between them), and if possible iPhone, SmartTag2 or moto tag, at fixed distances. Move the mouse closer step by step, at polling rates of 1K, 4K and 8K. Measure:
   - how often a distance measurement succeeds
   - how wrong the distance is, and how much it jumps around
   - how often the first signal path is detected wrongly
   - how many packets are lost

   Note: you can't plug the mouse in, so for the "no mouse" test, take its battery out. The base station might still transmit on its own, so check that too.
3. **Test the other way round too:** does a lot of UWB ranging traffic make the mouse lose packets or stutter? A polling-rate testing tool would show missed reports.
4. **Links to his power-control idea.** The mouse is already a short-range, probably low-power UWB link (about 1 m). It's a real example of "only transmit as loud as the distance needs". A UWB network that knows distances could do this on purpose.
5. **Before the experiments:** download the FCC test report and the RF exposure document. They should give the signal strength, graphs of the signal (which would also settle the frequency mismatch above), and maybe how often it transmits. We need these numbers to model the interference properly.

---

## What changed from v1

| # | Change | Why |
|---|---|---|
| 1 | SlashGear's 8000/9000 Hz numbers now say "not tested" instead of "measured" | The review just repeats SteelSeries' numbers |
| 2 | "9,000 packets a second each way" marked as my guess | No source says this. It combines Tom's Guide (9K) and PC Gamer (one reply per packet) |
| 3 | Keyboard name fixed to K63W Pro **Compact** | That's the name Tom's Guide uses |
| 4 | "Rival 2.4 GHz mice" changed to "Normal 2.4 GHz gaming mice"; Superlight 2 8K claim flagged | "Rival" is also this mouse's name; no saved page says the Superlight 2 does 8K |
| 5 | New section on SteelSeries' range (6.4 to 9.056 GHz) vs the FCC's (~6.457 to 8.125 GHz) | v1 didn't point out the ~1 GHz difference |
| 6 | Added: the mouse has no USB port and can't be used with a cable | PC Gamer. Changes how to do the "no mouse" test |
| 7 | Added 4 more FCC documents to download; Manuals+ not needed | They're all public on the FCC page |
| 8 | SPARK/Waizowl, 1 m range, and which channels phones use marked "not checked" | Their sources weren't saved |
| 9 | Small fixes: weights, upper edge 8.125 GHz, missing file numbers explained, overlap percentages added, launch dates clarified | Accuracy |
| 10 | New section: why use UWB in a mouse at all | Asked during review |
| 11 | Rewritten in simpler English; technical terms explained | Asked during review |
