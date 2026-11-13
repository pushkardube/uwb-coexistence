# DW3000 TX power: register mapping (DWM3001CDK)

**Verdict: the DW1000 coarse/fine table in [`DW1000_TX_POWER_NOTES.md`](DW1000_TX_POWER_NOTES.md)
is NOT valid for the DWM3001CDK.** The DWM3001CDK carries a DW3000-family
part (DW3110), and its `TX_POWER` register is different from the DW1000 in
*structure, bit layout, direction, and valid range*. Use this file for the
DWM3001CDK; keep the DW1000 file only for DW1000 boards (e.g. DWM1001).

Sources checked (all local):
- DW3000 Family User Manual §8.2.2.21 "Transmit power control", REG 0x01:0C
  — `~/COSIC/COSIC papers/Docs/DWM3001CDK/DW3000_Family_User_Manual.pdf` (p.106–109)
- DW3xxx Software API Guide 4p12, §5.2.7 `dwt_configuretxrf`, Tables 6–8
  — `~/SDK/Documentation/Drivers/DW3XXX_Software_API_Guide_4p12.pdf`
- Qorvo SDK limits — `~/COSIC/qani-rtt-build/DW3_QM33_SDK_1.1.1/Src/Boards/Src/Common_OTP/OTP_config.h`
- Driver in this repo — `drivers/dw3000/inc/deca_device_api.h` (`dwt_txconfig_t`)

---

## How you set TX power on DW3000

Not by writing one gain byte like the DW1000 `DW1000Class` code. On DW3000 you
fill a `dwt_txconfig_t` and call `dwt_configuretxrf()`:

```c
dwt_txconfig_t tx = {
    .PGdly   = 0x34,          // pulse-generator delay (bandwidth), ch5 & ch9 = 0x34
    .power   = 0xfefefefe,    // 4 per-section power octets (see below)
    .PGcount = 0x0,
};
dwt_configuretxrf(&tx);       // call after dwt_configure()
```

(Already used exactly this way in the COSIC samples `section_power_test`,
`cicada_power_attack`, `cicada_twr_simple`.)

## The register — REG 0x01:0C, four octets *by frame section*

The DW1000 used one gain value for the whole frame (plus "smart TX power"
boost bytes selected by frame *duration*). The DW3000 instead splits power by
**which part of the frame** is being transmitted — four independent octets in
one 32-bit word:

```
bits:  31......24  23......16  15.......8  7........0
       STS_PWR     SHR_PWR     PHR_PWR     DATA_PWR
       (STS)       (preamble   (PHY        (payload)
                    + SFD)      header)
```

| byte index | field | covers |
|---|---|---|
| 3 `[31:24]` | `STS_PWR`  | STS portion |
| 2 `[23:16]` | `SHR_PWR`  | preamble **+ SFD** (one knob for both) |
| 1 `[15:8]`  | `PHR_PWR`  | PHY header |
| 0 `[7:0]`   | `DATA_PWR` | payload |

> This per-section control is what the Ghost Peak / Cicada attacks exploit
> (boost one section, suppress the rest). For a plain power sweep just set all
> four octets to the same value.

## How ONE octet decodes (the part that replaces the DW1000 table)

```
bit:  7  6  5  4  3  2 | 1  0
      FINE  (6 bits)   | COARSE (2 bits)
```

- **FINE** = bits `[7:2]`, **64 steps**, providing **~25 dB** of range
  ⇒ roughly **~0.4 dB per fine step**.
- **COARSE** = bits `[1:0]`, **4 steps (0–3)**, adding **~7 dB**.
- At fixed coarse gain, increasing the fine code gives nominally nondecreasing
  output gain. Increasing coarse at the same fine code also increases nominal
  gain. **Arbitrary mixed-coarse words cannot be sorted by numeric hex value
  alone**; coarse/fine contributions must be considered together. These are
  nominal relationships, not an absolute calibration or a guarantee that
  measured adjacent RSSI medians will rise without variation.
- For best current draw, **minimise coarse** and use fine for most of the range.

Decoding a byte:  `coarse = byte & 0x03;  fine = byte >> 2;`
Building a byte:   `byte = (fine << 2) | coarse;`

### Worked examples

| Byte | FINE `[7:2]` | COARSE `[1:0]` | meaning |
|---|---|---|---|
| `0xFE` | 63 | 2 | ch9 **recommended / near-max** (coarse 3 banned on ch9) |
| `0xFD` | 63 | 1 | ch5 recommended value (Table 7) |
| `0x82` | 32 | 2 | User-Manual default example per octet |
| `0x01` | 0  | 1 | Qorvo **minimum allowed** |
| `0xFE` | 63 | 2 | Qorvo **maximum allowed** |

## Valid range & recommended values

- **Per octet limits (Qorvo `OTP_config.h`):**
  `TX_POWER_MIN_ALLOWED_VALUE = 0x01010101`, `TX_POWER_MAX_ALLOWED_VALUE = 0xFEFEFEFE`.
  (Unlike DW1000 there is no "0xE0–0xFF = off" band; `0x00`/`0xFF` are just
  out of the allowed range.)
- **Recommended starting points (API Guide Table 7):**
  channel 5 → `0xFDFDFDFD`, channel 9 → `0xFEFEFEFE`.
- **Coarse caps (User Manual, Figure 27 note):**
  - **Channel 9:** max coarse = **2**; setting 3 **must not be used** — this is
    why the ch9 recommended byte is `0xFE` (coarse 2), not `0xFF` (coarse 3).
  - **Channel 5:** recommended coarse = 2; coarse 3 gives only marginal power
    for a large current increase.
- **PHR peak-power note:** the BPRF PHR is peak-power-limited; Qorvo recommends
  `PHR_PWR` be a touch lower than the others (e.g. DATA `0xFF` → PHR `0xFC`).

## Still true from the DW1000 note (general, not register-specific)

- **Register value is gain, not absolute dBm.** Actual dBm depends on channel,
  PRF, board, antenna and losses. Figure 27 in the User Manual gives the
  *relative* dB curve vs. fine/coarse, not calibrated dBm.
- **To get real dBm: start from the recommended value** (designed near the
  −41.3 dBm/MHz limit on Decawave's EVBs) and **measure** (spectrum analyser,
  or relative RX-power logging at fixed distance). Don't exceed the per-channel
  recommended/allowed values or you may break the emission limit.
- **For clean power-control experiments**, keep one setting = one known power.
  The DW1000's "disable smart TX power" step has no DW3000 equivalent in this
  register (power is per-section, not per-duration); just set all four octets
  equal and sweep that one value. `dwt_adjust_tx_power()` exists if you *do*
  want the short-frame boost, but leave it alone for a flat sweep.

## For the spatial-resolution experiment

If you sweep TX power to move the reception cliff ([`../experiments/spatial_resolution.md`](../experiments/spatial_resolution.md)),
set all four octets equal and step the single byte, e.g. in the TX app add a
`dwt_configuretxrf()` with `.power = 0xNNNNNNNN` after `dwt_configure()`.
Channel 9 (our PHY config) → stay within `0x01`…`0xFE`, remembering coarse must
be ≤ 2. The current experiment uses the separate 01 probe followed by all
64 fine codes at coarse 2. The historical mixed-coarse ladder is not a verified
equal-step or universally monotonic power calibration. See the
[checked combined sweep guide](../samples/twr_checked_combined_common/README.md)
for the schedule and receiver-side diagnostics, and the
[analysis tools](../tools/README.md) for exporting measurements and checking
whether corrected RSSI follows increasing nominal gain.
