# UWB Products and the Chips Inside Them

Compiled 2026-11-04. Confidence is noted where it matters: **confirmed** means a vendor press release or official spec, **list** means the Wikipedia UWB device list (some of its entries are inferred), and **unknown** means nobody has published it.

The big picture for co-existence: there are now **two families of UWB devices sharing 6–9 GHz**:

1. **Ranging UWB (IEEE 802.15.4z / FiRa / Apple NI):** phones, watches, tags, car keys, smart locks. Short, sparse bursts on ~500 MHz channels (ch5 at 6.5 GHz, ch9 at 8 GHz).
2. **Data UWB (SPARK LE-UWB, proprietary):** gaming mice, keyboards, headphones, speakers. Continuous high-rate links. The mouse sends about 9,000 packets/s each way. Uses 500 MHz instantaneous channels hopped across 6–9 GHz.

Nobody has published measurements of how these two families interfere with each other.

---

## 1. Data UWB: gaming peripherals and audio (almost all SPARK Microsystems)

| Product | Type | UWB chip | Notes | Confidence |
|---|---|---|---|---|
| **SteelSeries Sensei Pro / Rival Pro** (+ Mini) | Gaming mouse | **SPARK LE-UWB** (exact part not named) | SPARK is the "exclusive connectivity platform". 8K polling, 9K over-polling. FCC ID ZHK-M033: 7290.88 MHz centre, 1.67 GHz 10 dB BW. NXP LPC5528 MCU (per IT之家). Launched Sept 2026. | **Confirmed** (SPARK PR, Oct 1 2026) |
| **ELECOM VM800 series** (VM800, VM800L) | Gaming mouse | **SPARK LE-UWB** | Called the first shipping UWB gaming mouse (Japan, Sept 2025). 8 kHz. Range about 1.5 m. UWB is its only wireless option. | **Confirmed** (SPARK PR) |
| **Waizowl Cloud Ultra** (incl. Nebula Edition) | Gaming mouse | **SPARK LE-UWB** | 8 kHz polling. | **Confirmed** (SPARK PR, Jul 2025) |
| **Cherry XTRFY K63W Pro Compact** | Gaming keyboard | **SPARK LE-UWB** | Called the first UWB gaming keyboard. 8 kHz. Computex 2026, about $170 / €180. | **Confirmed** (SPARK PR, Jun 2026) |
| **LEWITT LW6** | Studio headphones | **SPARK LE-UWB** | Uncompressed audio, about 5.8 ms latency, about 5 m range, $699. Sept 2026. | **Confirmed** (SPARK PR) |
| **Focal Diva Alta Utopia** | Wireless speakers | **SPARK LE-UWB** | Lossless speaker-to-speaker link. | **Confirmed** (SPARK boilerplate) |
| SPARK reference designs | Mouse / keyboard / headset demos | SPARK SR1120 / SR1020 | Headset demo: 96 kHz/24-bit, 5 ms latency. Not a retail product. | Vendor demo |

**SPARK chips:**
- **SR1020:** 6.0–9.3 GHz, first generation.
- **SR1010:** sub-6 GHz variant.
- **SR1120:** 6.2–9.5 GHz, up to 41 Mbps, 25 µs airtime per 1 kbit, OOK modulation, non-coherent receiver. Runs a **proprietary impulse radio plus an IEEE 802.15.4ab draft** mode. Uses 500 MHz instantaneous bandwidth and sends at several centre frequencies within 1 ms.
- Datasheet: `sources/spark/SR1120_datasheet.pdf`.

---

## 2. Phones (ranging)

| Phone | UWB chip | Confidence |
|---|---|---|
| Apple iPhone 11 – 14 | **Apple U1** | List |
| Apple iPhone 15 – 17 | **Apple U2** | List |
| Google Pixel 6 Pro | **Qorvo DW3720** | List |
| Google Pixel 9 Pro / XL / Fold | **Qorvo QM35725** | List |
| Google Pixel 10 Pro / XL / Fold | Qorvo QM35725 (inferred). One source says Samsung S3JU100 instead | List, conflicting |
| Samsung Galaxy Note20 Ultra, S21+/Ultra, S22+/Ultra, Z Fold2/3 | **NXP SR100T** | List |
| Samsung Galaxy S23 Ultra | **NXP SR200** | Yole Group |
| Samsung Galaxy S24+/Ultra | NXP SR200T (inferred) | List |
| Samsung Galaxy S26+/Ultra | Qualcomm FastConnect 7900, UWB built into the Wi-Fi/BT combo chip (inferred) | List |
| Xiaomi MIX4 | **NXP SR100T** | List |
| Xiaomi 15s Pro | NXP SR200T (inferred) | List |
| Xiaomi Poco F9 | Qualcomm FastConnect 7900 (inferred) | List |
| Meizu 20 Infinity | **NXP SR100T** | List |
| Sharp AQUOS R8 | **NXP SR100T** | List |
| Blackview BV8900 Pro | **GiantSemi GT1500** | List |
| NIO Phone 2 | Qorvo UWB SoC (inferred) | List |
| Motorola Edge 50 Ultra, Razr Ultra, Signature; Huawei Mate XT | UWB present, chip unknown | Unknown |

**Trend:** UWB is moving out of standalone chips and into combo chips (Qualcomm FastConnect 7900). New Chinese suppliers like GiantSemi are entering cheaper devices.

---

## 3. Watches, earbuds and speakers (ranging)

| Product | UWB chip | Confidence |
|---|---|---|
| Apple Watch Series 6 – 8, Ultra (1st gen) | **Apple U1** | List |
| Apple Watch Series 9+, Ultra 2+ | **Apple U2** | List (later models inferred) |
| Google Pixel Watch 3 | **NXP SR100T** | List |
| AirPods Pro 2 case (Lightning and USB-C) | **Apple U1** | List |
| AirPods Pro 3 case | **Apple U2** | List |
| HomePod mini, HomePod (2nd gen) | **Apple U1** | List |

---

## 4. Trackers and tags (ranging)

| Product | UWB chip | Confidence |
|---|---|---|
| Apple AirTag (1st gen) | **Apple U1** | List |
| Apple AirTag (2nd gen) | **Apple U2** | List |
| Samsung Galaxy SmartTag+ / **SmartTag2** | **NXP SR040** | List + arXiv paper |
| **Motorola Moto Tag** | **Qorvo DW3210** (ch5 and ch9, PCB antenna) | List + Technotrend teardown |
| Motorola Moto Tag 2 | **GiantSemi GT1500** | List |
| Blackview BV8900 Pro tag | **GiantSemi GT1500** | List |
| Changhong Neo Tag | NXP (part not given) | List |
| Google Pixel Tag, Xiaomi Tag | UWB present or rumoured, chip unknown | Unknown |

The Technotrend teardown roundup (AirTag, SmartTag2, Moto Tag, Blackview) is paywalled.

---

## 5. Cars and smart home (ranging)

| Product | UWB chip | Notes | Confidence |
|---|---|---|---|
| **BMW** Digital Key Plus (iX and others) | **NXP Trimension NCJ29D5** (car and fob) | 6.0–8.5 GHz, CCC Digital Key 3.0 | **Confirmed** (NXP) |
| Genesis, NIO, BYD digital keys | NXP named as supplier for first OEMs | Exact parts per model not given | NXP slide deck |
| **Aqara U400** smart lock | UWB walk-up unlock (Apple Home Key, Samsung Wallet) | Chip not published | Unknown |
| Aqara U200 | **No UWB** (NFC/Thread only) | Common confusion | Confirmed (Aqara forum) |

---

## 6. Dev boards (what you can actually program)

| Board | UWB chip | Notes |
|---|---|---|
| Qorvo **DWM3001CDK** | Qorvo DW3110 + Nordic nRF52833 | Ch5/ch9, 802.15.4z. What you've been using for the attacks. |
| Qorvo DWM3000EVB / DW3000 family | Qorvo DW3000 series | Interoperable with Apple U1/U2 (Qorvo). |
| NXP Trimension SR150 / SR040 eval kits | NXP SR150 / SR040 | SR040 is the SmartTag2 chip. |
| SPARK SR1020 / SR1120 EVKs | SPARK | Only way to get a programmable **data UWB** radio like the mouse's. |

---

## Chip vendor map

| Vendor | Chips | Where they show up |
|---|---|---|
| **Apple** | U1, U2 | All Apple devices (in-house) |
| **NXP** | SR100T, SR200T, SR040, SR150, NCJ29D5 (auto) | Samsung, Xiaomi, Pixel Watch, SmartTag, BMW and other cars |
| **Qorvo** (ex-Decawave) | DW3000/DW3110/DW3210/DW3720, QM35725 | Pixel phones, Moto Tag, dev kits |
| **SPARK Microsystems** | SR1010, SR1020, SR1120 (LE-UWB, proprietary + 15.4ab draft) | **All the data-UWB peripherals:** SteelSeries, ELECOM, Waizowl, Cherry, LEWITT, Focal |
| **GiantSemi** | GT1500 | Moto Tag 2, Blackview |
| **Qualcomm** | FastConnect 7900 (UWB integrated) | Newer Samsung/Xiaomi flagships (inferred) |
| **Samsung LSI** | S3JU100 | Possibly Pixel 10 Pro (conflicting) |

---

## Sources

- SPARK × SteelSeries PR: https://www.sparkmicro.com/news/spark-microsystems-teams-with-steelseries-to-boost-wireless-gaming-performance-with-low-energy-uwb-le-uwb
- SPARK × ELECOM: https://www.businesswire.com/news/home/20250910728088/en
- SPARK × Waizowl: https://www.businesswire.com/news/home/20250715760073/en/Waizowl-Leads-Wireless-Gaming-Revolution-with-New-Cloud-Ultra-Gaming-Mouse-Powered-by-SPARK-Microsystems
- SPARK × Cherry XTRFY: https://secure.businesswire.com/news/home/20260602855621/en/CHERRY-XTRFY-Tops-Keyboard-Performance-Benchmarks-with-SPARK-Microsystems-Low-Energy-UWB-Wireless-Connectivity
- SPARK × LEWITT: https://www.businesswire.com/news/home/20260922652824/en/SPARK-Microsystems-Brings-Premium-Sound-to-Pro-Audio-Market-Powering-LEWITTs-Debut-Studio-Headphones
- LEWITT LW6 specs: https://www.ecoustics.com/products/lewitt-lw6-wireless-studio-headphones/
- SPARK / Focal: https://fineeng.eu/spark-le-uwb-transceivers-deterministic-wireless-technology/
- SPARK SR1120: https://www.sparkmicro.com/products/sr1120/
- SPARK SR1020: https://www.sparkmicro.com/products/sr1020/
- SPARK gaming reference designs: https://www.sparkmicro.com/applications/gaming/
- ELECOM VM800 review (range): https://gaming-st.com/peripherals/elecom-vm800-uwb-2026-review/
- IT之家 (Rival Pro FCC, NXP MCU): https://www.ithome.com/0/981/795.htm
- FCC ZHK-M033: https://fccid.io/ZHK-M033
- Wikipedia UWB device list: https://en.wikipedia.org/wiki/List_of_UWB-enabled_mobile_devices
- Yole Group on NXP/Qorvo/Apple: https://www.yolegroup.com/press-release/unlocking-ultra-wideband-yole-group-analyzes-nxps-qorvos-and-apples-technical-choices/
- Smartphones with UWB (arXiv): https://arxiv.org/pdf/2303.11220
- Moto Tag teardown: https://technotrend.substack.com/p/motorola-moto-tag-brief-product-analysis
- UWB tag teardown roundup (paywalled): https://technotrend.substack.com/p/the-new-uwb-cycle-behind-my-latest
- NXP NCJ29D5: https://www.nxp.com/products/NCJ29D5
- BMW Digital Key 3.0 (EE Times): https://www.eetimes.com/nxp-adds-latest-automotive-uwb-chip-as-bmw-drives-digital-key-3-0/
- NXP automotive UWB deck: https://www.nxp.com/docs/en/training-presentation/TP-TD24-EUF-AUT-T4768.pdf
- Aqara U400 review: https://www.derekseaman.com/2026/05/aqara-u400-the-ultimate-smart-lock.html
- Aqara U200 no-UWB thread: https://forum.aqara.com/t/uwb-for-smart-lock-u200-kit/206734
