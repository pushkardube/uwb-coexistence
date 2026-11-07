# DW1000 TX power: code and register mapping

Code shared by Ashutosh (2026-11-03) for the arduino-dw1000 library (`DW1000Class`), plus how to read the TX power register values.

Note: this is for the **DW1000**. The **DW3000 uses a different TX_POWER bit layout**. Check the DW3000 User Manual before using these numbers on DW3000 boards.

> ⚠️ **Verified 2026-11-06: this mapping does NOT apply to the DWM3001CDK**
> (DW3000/DW3110). The DW3000 register differs in structure (4 octets by frame
> *section*), bit split (fine `[7:2]` / coarse `[1:0]`), direction (bigger =
> *more* output, not reversed), and range (`0x01`–`0xFE`, no "off" band).
> Use **[`DW3000_TX_POWER_NOTES.md`](DW3000_TX_POWER_NOTES.md)** for this board.
> Keep this file only for actual DW1000 hardware (e.g. DWM1001).

## The code (as shared)

```cpp
//Added to set high TX power
void DW1000Class::set_specificpower(uint32_t pwr){
    //Set the higher transmit power always for all nodes

    byte txpower[LEN_TX_POWER];
    readBytes(TX_POWER, NO_SUB, txpower, LEN_TX_POWER);
        uint32_t data;
        data = txpower[0]<<24+txpower[1]<<16+txpower[2]<<8+txpower[3];
    data = (data & 0xFF0000FF) | (pwr) ; //C0 = 0dB gain//1C = 14dB gain

    writeValueToBytes(txpower, data, LEN_TX_POWER);
    writeBytes(TX_POWER, NO_SUB, txpower, LEN_TX_POWER);
}
```

## How one TX power byte works

The TX_POWER register (0x1E) is 4 bytes. **Each byte** is one gain setting, made of two parts:

```
bit:   7  6  5 | 4  3  2  1  0
       coarse  |     fine
     (DA gain) |  (mixer gain)
```

**Total gain (dB) = coarse gain + fine gain**

### Coarse gain (bits 7:5)

| Bits 7:5 | Coarse gain |
|---|---|
| 000 | 15.0 dB |
| 001 | 12.5 dB |
| 010 | 10.0 dB |
| 011 | 7.5 dB |
| 100 | 5.0 dB |
| 101 | 2.5 dB |
| 110 | 0.0 dB |
| 111 | **OFF (no output)** |

Note the coarse scale is **backwards**: a bigger number means **less** gain.

### Fine gain (bits 4:0)

Fine gain = value × 0.5 dB, from 0 dB (`00000`) to 15.5 dB (`11111`). Here the scale is the normal way round.

| Value | Gain | Value | Gain | Value | Gain | Value | Gain |
|---|---|---|---|---|---|---|---|
| 0 | 0.0 | 8 | 4.0 | 16 | 8.0 | 24 | 12.0 |
| 1 | 0.5 | 9 | 4.5 | 17 | 8.5 | 25 | 12.5 |
| 2 | 1.0 | 10 | 5.0 | 18 | 9.0 | 26 | 13.0 |
| 3 | 1.5 | 11 | 5.5 | 19 | 9.5 | 27 | 13.5 |
| 4 | 2.0 | 12 | 6.0 | 20 | 10.0 | 28 | 14.0 |
| 5 | 2.5 | 13 | 6.5 | 21 | 10.5 | 29 | 14.5 |
| 6 | 3.0 | 14 | 7.0 | 22 | 11.0 | 30 | 15.0 |
| 7 | 3.5 | 15 | 7.5 | 23 | 11.5 | 31 | 15.5 |

### Building a byte

```
byte = (coarse_code << 5) | fine_code
```

Range: 0 dB (`0xC0`) up to 30.5 dB (`0x1F`), in 0.5 dB fine steps on top of 2.5 dB coarse steps. `0xE0` to `0xFF` = output off.

### Worked examples

| Byte | Coarse | Fine | **Total gain** |
|---|---|---|---|
| `0xC0` | 110 = 0 dB | 0 = 0 dB | **0 dB** (lowest that still transmits) |
| `0x1C` | 000 = 15 dB | 28 = 14 dB | **29 dB** |
| `0x1F` | 000 = 15 dB | 31 = 15.5 dB | **30.5 dB** (maximum) |
| `0x48` | 010 = 10 dB | 8 = 4 dB | **14 dB** |
| `0xE0` | 111 = off | — | **no output** |

⚠️ **The code comment says "1C = 14dB gain", but `0x1C` is really 29 dB total.** 14 dB is only the fine part; the coarse part adds 15 dB more. If you want 14 dB total, use something like `0x48` (10 + 4) or `0x7D` (7.5 + 6.5). Worth confirming with Ashutosh which one he meant.

## What the 4 bytes are for

What each byte controls depends on whether "smart TX power" is on (the `DIS_STXP` bit in SYS_CFG):

| Byte | Smart TX power **off** | Smart TX power **on** |
|---|---|---|
| 0 (bits 7:0) | not used | BOOSTNORM: normal frames |
| 1 (bits 15:8) | TXPOWPHR: PHY header part | BOOSTP500: frames ≤ 0.5 ms |
| 2 (bits 23:16) | TXPOWSD: preamble + data part | BOOSTP250: frames ≤ 0.25 ms |
| 3 (bits 31:24) | not used | BOOSTP125: frames ≤ 0.125 ms |

Smart TX power lets **short frames** use higher power, because the legal limit is averaged over 1 ms. **For power-control experiments, turn smart TX power off**, so one setting means one known power.

## Notes on the code

- The mask `0xFF0000FF` keeps the outer bytes and replaces the **middle two bytes** (bits 23:8) with `pwr`. So `pwr` should be given **already shifted** into bits 23:8. For example, to set both middle bytes to `0xC0`: `pwr = 0x00C0C000`. Bits of `pwr` outside 23:8 would leak into the other bytes.
- **The `data = ...` line doesn't do what it looks like.** In C/C++, `+` binds tighter than `<<`, so `txpower[0]<<24+txpower[1]<<16...` is read as `txpower[0] << (24+txpower[1]) << ...`. Those shifts are usually 32 or more, which is undefined behaviour, so the **outer two bytes written back are unpredictable** (probably 0). The middle bytes are fine, because they come straight from `pwr`.
- Even with brackets added, the byte order would be reversed: `readBytes` gives the least significant byte first, but the line puts `txpower[0]` at the top. Then bytes 0 and 3 would swap, and so would bytes 1 and 2.
- **Why it still works:** with smart TX power **off**, only the two middle bytes matter, and setting both to the same value hides any swap. With smart TX power **on**, the outer bytes (BOOSTNORM, BOOSTP125) would get junk. So keep smart TX power off with this function.
- A safer version just sets the bytes directly, without the shifting:
  ```cpp
  txpower[1] = gain_byte;   // PHR part
  txpower[2] = gain_byte;   // preamble + data part
  ```

## Gain (dB) is not output power (dBm)

The register sets **gain**, not an absolute output power. The actual dBm depends on:
- channel and PRF
- the board, its antenna and any losses
- whether smart TX power is on

So there is **no fixed register → dBm table**. To get real dBm numbers:
1. Start from the **reference TX_POWER values** in the DW1000 User Manual for your channel and PRF. These are designed to hit about the legal limit (−41.3 dBm/MHz). Treat that as your "0 dB below max" point.
2. Every dB of gain you remove from there = 1 dB lower output (roughly, within the coarse/fine steps).
3. For accurate numbers, **measure**: a spectrum analyzer if the lab has one, or at least log the receiver's reported signal strength at a fixed distance for each setting, and use that as a relative calibration.

Also: **don't exceed the reference values** for the channel, or the board may go over the legal emission limit.
