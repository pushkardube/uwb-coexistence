# SteelSeries Sensei Pro / Rival Pro: UWB Mouse Research Summary

Collected 2026-11-02 to prepare for the co-existence project discussion with Ashutosh.

## Folder layout

```
uwb_coexistence_research/
├── SUMMARY.md       <- this file
├── sources/         <- raw HTML pages as downloaded
└── text/            <- plain-text extraction of each page (easier to grep/read)
```

| # | File | Source | What it is |
|---|------|--------|------------|
| 01 | `01_steelseries_press_release` | [SteelSeries press](https://steelseries.com/press/165-steelseries-unleashes-ultra-wideband-uwb-for-unbridled-8k-performance-all) | Official launch PR: band, bandwidth, battery, pricing |
| 02 | `02_steelseries_product_page` | [SteelSeries LP](https://steelseries.com/gaming-products/sensei-rival-pro-lp) | Product landing page |
| 03 | `03_hothardware` | [HotHardware](https://hothardware.com/news/steelseries-rival-pro-sensei-pro-ultra-wideband) | News: "6.4 GHz band", multiple channels |
| 04 | `04_slashgear_review` | [SlashGear](https://www.slashgear.com/2276269/steelseries-senesi-pro-x-rival-pro-review/) | Hands-on review: base station, measured 8K polling, multi-host |
| 07 | `07_notebookcheck` | [Notebookcheck](https://www.notebookcheck.net/SteelSeries-Sensei-Pro-Rival-Pro-series-gaming-mice-boast-UWB-8K-connectivity-and-infinite-battery.1411249.0.html) | News, 9K over-polling claim |
| 10 | `10_tomsguide_review` | [Tom's Guide](https://www.tomsguide.com/gaming/gaming-peripherals/steelseries-rival-pro-sensei-pro-review) | Most detailed review: over-polling mechanism, range, AirTag remark |
| 11 | `11_pcgamer_review` | [PC Gamer](https://www.pcgamer.com/hardware/gaming-mice/no-usb-connectivity-like-at-all-its-a-good-job-steelseries-new-gaming-mice-are-two-of-the-best-ive-felt-under-my-fingertips/) | Review: "one packet + one receipt" at 8K |
| 12 | `12_fccid_ZHK-M033` | [fccid.io ZHK-M033](https://fccid.io/ZHK-M033) | **FCC grant: center freq, 10 dB bandwidth, rule part** |

**Could not download (blocked: 403/503). Open these in a browser if needed:**
- [Aroged article](https://www.aroged.com/2026/09/29/steelseries-launches-sensei-pro-and-rival-pro-wireless-gaming-mice-with-broadband-wireless-connectivity/)
- [Scan UK listing](https://www.scan.co.uk/products/steelseries-sensei-pro-wireless-gaming-mouse-black-optical-truemove-42k-pro-sensor-42k-dpi-6-buttons) (source of the "1 m range" spec)
- [Manuals+ user guide](https://manuals.plus/steelseries/sensei-pro-wireless-gaming-mouse-manual)
- [BusinessWire: Waizowl mouse uses SPARK Microsystems UWB](https://www.businesswire.com/news/home/20250715760073/en/Waizowl-Leads-Wireless-Gaming-Revolution-with-New-Cloud-Ultra-Gaming-Mouse-Powered-by-SPARK-Microsystems)
- **FCC exhibits for ZHK-M033** (the most valuable items, but scripted downloads are refused): [Test Report rev 5](https://fccid.io/ZHK-M033/Test-Report/Test-Report-rev-5-9246576), [Internal Photos](https://fccid.io/ZHK-M033/Internal-Photos/Internal-Photos-9246535), [Antenna Datasheet](https://fccid.io/ZHK-M033/Test-Report/Antenna-Datasheet-rev-9246568). Download them manually and save them in `sources/`. Block diagram, schematics and operational description are under long-term confidentiality and are **not** public.

---

## What the product is

- **Launched:** late Sept 2026; shipped Oct 13, 2026. $179.99.
- **Lineup:** Sensei Pro (symmetrical) and Rival Pro (ergonomic), each in full size (53 g) and Mini (49 g).
- **Makers on the filing:** SteelSeries is owned by GN (Jabra's parent). The FCC grantee is GN Audio USA Inc. The test lab is Bureau Veritas, Taoyuan.
- **Sensor:** TrueMove 42K Pro, a customised PixArt PAW3955.
- Marketed as "the world's first pure UWB wireless mice with true 8K performance".

## How the wireless link works (what's public)

### From the FCC grant (hard facts)

| Field | Value |
|---|---|
| FCC ID | ZHK-M033 (model M033) |
| Equipment class | **UWB, Ultra Wideband Transmitter** |
| Rule part | **47 CFR Part 15 Subpart F** (UWB rules; the grant cites §15.519 handheld and §15.521) |
| Center frequency | **7290.88 MHz** |
| 10 dB bandwidth | **1.6678 GHz**, so roughly **6.457 to 8.124 GHz** |
| Grant date | 2026-05-05 |

**Why this matters for co-existence:** the 802.15.4z channels used by phones, tags and the DW3000 are about 499.2 MHz wide:
- Channel 5: center 6489.6 MHz, about 6.24 to 6.74 GHz
- Channel 9: center 7987.2 MHz, about 7.74 to 8.24 GHz

The mouse's 10 dB band, about 6.46 to 8.12 GHz, **overlaps the upper part of ch5 and most of ch9**, and covers everything in between. One mouse can therefore put energy into *both* channels that iPhones, Pixels, Samsung SmartTags and DW3000 boards use. It's a much wider pulse than a single 802.15.4z channel (about 1.67 GHz versus 0.5 GHz). Possible explanations:
- a very short pulse, or
- the "multiple channels simultaneously" marketing claim, i.e. one wideband signal or fast hopping.

The test report should settle this.

### From SteelSeries and reviews (claims and observations)

- **Band:** "6.4 GHz to 9.056 GHz spectrum", "roughly 20x the bandwidth" of 2.4 GHz, and it "can leverage multiple wireless channels simultaneously".
- **Protocol style (PC Gamer):** "True 8K" means **one packet sent and one receipt (ACK) received** for every report at 8 kHz, instead of batching reports like most 2.4 GHz mice. If true, that's about 8,000 transmissions per second from the mouse *plus* 8,000 ACKs per second from the base station, so **both ends transmit with a very high duty cycle**.
- **"9K over-polling" (Tom's Guide):** the link actually runs at 9 kHz. An extra (ninth) packet follows every eighth one as redundancy against loss, which guarantees an effective 8 kHz. So there are roughly **9,000 packets/s each way at max settings**. In other words, the link deliberately carries extra packets so it can tolerate losses.
- **Measured (SlashGear):** true 8000 Hz polling (0.125 ms); over-polling up to 9000 Hz (0.111 ms).
- **Rate settings:** polling and sensor rates can each be set to 125, 250, 500, 1K, 2K, 4K or 8K Hz, with 5 presets cycled from the base station button. Click polling and sensor polling can be set independently.
- **Range:** described as "very short, but enough to cover a mousemat"; a retailer lists **1 m**. This suggests transmit power well below the Part 15F cap, or a very short link budget at these data rates.
- **Base station:** a USB-C hub (cable to the PC, Xbox or PS5) that also charges the spare battery. A $24.99 USB-C **travel dongle** is the second receiver. The mouse pairs with whichever is active, with a manual button combo to switch.
- **Power:** 310 mAh battery. About 16 h at 8K or 60 h at 1K per battery. The radio plus 8K sensor uses a lot of power.
- **Tom's Guide on interference:** they claim another UWB device (an AirTag) on the desk "won't be an issue" because "most UWB devices use a very narrow channel". **No measurement backs this up.** It's an assumption, and **testing it is the research opportunity.**

### Unknown or not public

- **Which chip it uses:** no teardown names it. The internal photos on FCC should show it.
  - **Lead:** SPARK Microsystems (Montreal) makes low-power UWB *data* transceivers (SR1000 family, SR1120) and already powers the Waizowl Cloud Ultra gaming mouse. No confirmed SteelSeries link.
  - Other candidates: Qorvo or NXP, less likely for a pure data link.
- **802.15.4z or proprietary:** almost certainly a **proprietary UWB data link**, not 15.4z ranging. Nothing about it mentions ranging, STS or FiRa.
- **Modulation, PRF, channel access, hopping, and what it does when it detects interference:** none of this is public. The operational description is confidential.
- **Wireless latency:** the advertised **0.35 ms** is for the click switches, not the radio link.

## Related devices worth knowing about

- **Cherry XTRFY K63W Pro:** a "world's first UWB mechanical gaming keyboard" (Tom's Guide sidebar). **A second UWB peripheral that could also share the desk with the mouse.**
- **Waizowl Cloud Ultra:** a gaming mouse using SPARK Microsystems UWB.
- Rival 2.4 GHz 8K mice (Logitech G Pro X Superlight 2, Razer Viper V4 Pro) show the "old way", useful as a baseline.

---

## Takeaways for the co-existence project

1. **A real-world interferer that's easy to buy.** A $180 consumer mouse transmitting about 9,000 packets/s *in both directions* across 6.46 to 8.12 GHz is a near-worst-case neighbour for 802.15.4z ranging on ch5/ch9.
2. **First experiment to run:** DW3000 TWR (and if possible iPhone NI, SmartTag2 or moto tag) at fixed distances, with the mouse at increasing distances and polling rates (1K, 4K, 8K). Measure:
   - ranging success rate
   - ranging error / variance
   - first-path detection errors
   - packet error rate
3. **Test the reverse direction too:** does heavy ranging traffic make the mouse lose packets or stutter? Missed reports would show up in a polling-rate logging tool.
4. **Connects directly to his power-control idea.** The mouse is already a short-range, presumably low-power UWB link (about 1 m). It shows "transmit only as loud as the distance requires" in practice. A ranging-aware network could do the same deliberately.
5. **Before the experiments:** download the FCC test report. It should give the measured EIRP/PSD, the pulse/emission plots, and possibly the duty cycle, which are the numbers needed to model interference properly.
