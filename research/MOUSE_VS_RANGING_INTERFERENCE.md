# Why the UWB mouse is a different interference problem

Question: why worry about the SteelSeries UWB mouse interfering, when we didn't worry about several UWB devices ranging near each other?

Short answer: it isn't really "UWB vs UWB". It's **devices that follow the same rules vs a device that doesn't**. Interference between ranging devices is real, but the standard is built to keep it small. The mouse falls outside that system.

Labels: *(my guess)* = my own reasoning. *(background)* = general UWB knowledge, not from the saved pages. See `SUMMARY_v2.md` for the sources on the mouse itself.

## Why ranging devices mostly get along

Phones, tags and DW3000 boards all follow 802.15.4z, often with FiRa on top. That gives them several ways to avoid each other *(background)*:

- **They're quiet almost all the time.** One ranging exchange takes a few milliseconds and repeats a few to tens of times a second. Each device is transmitting well under 1% of the time, so two devices rarely collide.
- **They take turns.** In FiRa, one device runs the session and gives each device its own time slot.
- **They can tell each other apart.** Different preamble codes, scrambled timestamps (STS) and addresses let a receiver ignore packets that aren't meant for it.
- **They can move.** If channel 9 is busy, a session can use channel 5.
- **If a round fails, they retry.** You get a slightly slower update, not a wrong answer.

Even so, it's not zero. Dense setups (many tags in a warehouse, for example) are a known research problem. Our earlier work didn't need to worry about it because the standard handles normal densities.

## Why the mouse is different

| | Another ranging device | The mouse |
|---|---|---|
| Follows the same rules | Yes | No, it uses its own system *(my guess, but very likely)* |
| Takes turns / can be scheduled | Yes | No, it doesn't know our devices exist |
| Receiver can recognise and ignore it | Yes (preamble codes, STS, address) | No, to a DW3000 it's just unknown energy |
| How often it transmits | Well under 1% of the time | ~9,000 packets/s plus replies, so possibly a large share of the time |
| Channels it covers | One 0.5 GHz channel | Most of channel 5 **and** channel 9 at once (FCC: ~6.46 to 8.12 GHz) |
| Can you switch channel to avoid it? | Yes | No, both main channels are covered |
| How close it is | Usually across a room | On the same desk as a phone, maybe 10 to 30 cm away |
| How long it's on | Short sessions | Hours, a whole gaming session |

## Three things make it worse

### 1. Distance (the near-far problem)

UWB rules cap everyone at the same very low power, so the mouse isn't louder than a phone. But a mouse 10 cm from a phone arrives about **34 dB stronger** (≈2,500×) than a tag 5 m away. That's the free-space estimate, 20·log10(5 / 0.1). This means a weak, fully legal signal can still drown out the one you want if it's close enough.

### 2. Ranging cares about timing, not just bits

A data link only needs the bits to arrive. Ranging needs to find the exact moment the **first path** of the signal arrived, to well under a nanosecond (1 ns ≈ 30 cm). Interference can break this without breaking the packet:

- A mouse pulse arriving just before the real first path can be mistaken for it, so the **distance reads too short**.
- Extra noise can hide a weak first path, so the receiver locks onto a later reflection and the **distance reads too long**.

So the packet looks fine, but the distance is quietly wrong. That's worse than a failure, because nothing tells you it happened.

### 3. You can't dodge it

All the usual tricks (another channel, another preamble code, scheduling) assume the other device plays by the same rules. The mouse ignores them and covers both channels.

## What we don't know yet

It could still turn out harmless. If each mouse packet is very short (a few microseconds), it might only be on air a few percent of the time despite 9,000 packets a second. Its real power and timing aren't public.

That's why we need the FCC test report (signal strength, signal shape, maybe how often it transmits) and our own experiment. Right now, both "it's fine" (Tom's Guide's view) and "it's a problem" are guesses.

## What to measure

Things the experiment should look at:
- distance error that goes up without packets failing (the "quietly wrong" case)
- ranging success rate
- how both of those change with mouse distance and polling rate

The full experiment plan is in `SUMMARY_v2.md`.

## One-line version

Ranging devices share the band politely because they follow the same rules. The mouse is a nearby, always-on, non-standard transmitter covering both main channels, and ranging is sensitive enough that it could bend distances without anything visibly failing.

---

## Sources

Labels used below:
- **saved page** = in `sources/` (line numbers refer to the `text/` version)
- **paper** = UREY-ML, IEEE TIFS vol. 21, 2026 (`Downloads/Urey_ML_2026.pdf`)
- **background** = general knowledge; the standard or document to cite is named
- **my guess / my maths** = my own reasoning, not from a source

### The comparison table

| Row | The mouse side | The ranging-device side |
|---|---|---|
| Follows the same rules | **My guess.** Based on what's *missing*: no saved page mentions 802.15.4z, FiRa, ranging or STS. The FCC filing keeps the technical description secret (`text/12_fccid_ZHK-M033.txt`). | **Background:** IEEE 802.15.4z standard; FiRa Consortium specs |
| Takes turns / can be scheduled | **My guess**, following from the row above | **Background:** FiRa MAC spec (one controller, time slots) |
| Receiver can recognise and ignore it | **My guess** (it doesn't use the standard's preamble codes or STS) | **Background:** 802.15.4z (preamble codes, STS, addresses). **Paper** §III-B explains STS |
| How often it transmits | **Saved pages:** 9,000/s from Tom's Guide (`text/10_tomsguide_review.txt` line 1337) and Notebookcheck (`text/07_notebookcheck.txt`). One reply per packet from PC Gamer (`text/11_pcgamer_review.txt` line 1023), who says "apparently". "Large share of the time" is **my guess**. | "Well under 1%" is **my estimate**. One exchange takes a few ms (**paper** Fig. 2); "a few to tens of times a second" is **background** (typical FiRa ranging intervals) |
| Channels it covers | **Saved page:** FCC grant, centre 7290.88 MHz and 10 dB bandwidth 1.6678 GHz (`text/12_fccid_ZHK-M033.txt`). Overlap percentages are **my maths**. | **Background:** ch5 = 6489.6 MHz, ch9 = 7987.2 MHz, both 499.2 MHz wide (802.15.4z) |
| Can you switch channel | Follows from the FCC numbers (**my reasoning**) | **Background:** 802.15.4z / FiRa |
| How close it is | "Same desk" fits Tom's Guide's own AirTag-on-desk example (`text/10_tomsguide_review.txt` line 1317). **10 to 30 cm is my guess.** | **My guess** ("across a room") |
| How long it's on | Battery 16 h at 8K from the press release (`text/01_steelseries_press_release.txt`) and Notebookcheck. "Whole gaming session" is **my guess**. | **Background** |

### "Why ranging devices mostly get along"

- All **background**: 802.15.4z (preamble codes, STS, channels) and FiRa (sessions, time slots, retries).
- The **paper** backs up parts: the DS-TWR exchange (§III-A), STS (§III-B), and iPhones ending a session after repeated errors (§V-A).
- "Dense deployments are a known research problem" is **background**. Find a specific paper before citing it.

### "Three things make it worse"

1. **Near-far, 34 dB:** **my maths** using the free-space path loss formula, 20·log10(5 / 0.1). The shared low power cap is **background**: FCC limit −41.3 dBm/MHz, [47 CFR §15.519](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-F), which the FCC grant cites.
2. **First-path timing:** **background**. The **paper** §III-A-2 explains it (first peak in the CIR, about 2 to 3 ns wide). The "too short / too long" effects are **my reasoning** from that.
3. **Can't dodge it:** **my reasoning**, combining the table rows above.

### "What we don't know yet"

- Power and timing not public: **saved page**. The FCC filing lists the operational description, block diagram and schematics as confidential.
- "Short packets might mean only a few percent on air": **my guess**.
- "It's fine": Tom's Guide (`text/10_tomsguide_review.txt` line 1317), not tested.

### What to cite in a paper

| Claim | Proper source |
|---|---|
| Channel numbers, preamble codes, STS | IEEE Std 802.15.4z-2020 |
| Scheduling, sessions | FiRa Consortium MAC/PHY technical specs |
| Power limit | 47 CFR §15.519 / §15.521 |
| Mouse frequency and bandwidth | FCC grant for ZHK-M033 |
| Mouse 9K / ACK behaviour | Tom's Guide, PC Gamer (reviews, weak sources) |
| First-path / CIR ranging basics | A UWB ranging textbook or survey; UREY-ML §III as a secondary source |

**Weakest points of the argument:** the mouse's on-air time and its reply/ACK traffic. Both rest on reviewers repeating SteelSeries. The FCC test report is the only thing likely to confirm them.

### FCC links (ZHK-M033)

- Main page: https://fccid.io/ZHK-M033
- Test Report rev 5: https://fccid.io/ZHK-M033/Test-Report/Test-Report-rev-5-9246576
- Antenna Datasheet: https://fccid.io/ZHK-M033/Test-Report/Antenna-Datasheet-rev-9246568
- RF Exposure Info (MPE): https://fccid.io/ZHK-M033/RF-Exposure-Info/RF-Exposure-Info-MPE-9246575
- Internal Photos: https://fccid.io/ZHK-M033/Internal-Photos/Internal-Photos-9246535
- Official FCC search (grantee code ZHK, product code M033): https://apps.fcc.gov/oetcf/eas/reports/GenericSearch.cfm
