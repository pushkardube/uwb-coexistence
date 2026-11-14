# Minimal UWB transmit/receive sample

Status: source reference; no new radio validation was performed for this documentation update.
Use this to understand the smallest polling TX/RX loop. For current ranging and
power measurements, use [the checked combined firmware](../twr_checked_combined_common/README.md).

## Code and configuration

All application logic is in [src/main.c](src/main.c). `uwb_init()` initializes
GPIO/SPI, resets the radio, probes the vendor driver, configures the PHY, and
sets both antenna delays to 16385. Those delays are inherited starting values,
not calibration of a particular pair.

| Source setting | Current value | Meaning |
|---|---:|---|
| `ROLE_TRANSMITTER` | 0 | RX; change to 1 for the transmitter |
| `ANCHOR_ID` | 1 | Printed receiver label; no on-air addressing |
| TX pause | 500 ms | Pause after each completed transmission |
| Channel / preamble / rate | 9 / 128 / 6.8 Mb/s | Must match on both boards |
| STS | Off | This is a plain packet demo |

The three-byte payload is `AB CD seq8`. The transmitter increments an eight-bit
sequence and logs its actual TX timestamp. The receiver logs payload bytes and
its RX timestamp. The two radios' absolute timestamps have different clock
epochs; subtracting a TX timestamp from another board's RX timestamp does not
yield propagation time. This sample does not calculate distance, RSSI or PRR.

## Build and flash

Commands run from the repository root. The role is an unconditional source
define, so edit it before each build; a `-DROLE_TRANSMITTER` flag is not a
reliable override of that source definition.

```bash
source tools/ncs_env.sh
# Set ROLE_TRANSMITTER=1 before this build:
west build -b decawave_dwm3001cdk samples/simple_txrx -d build/simple_tx -p always
# Set ROLE_TRANSMITTER=0 before this build:
west build -b decawave_dwm3001cdk samples/simple_txrx -d build/simple_rx -p always
west flash --skip-rebuild -d build/simple_rx -r nrfutil --dev-id RESP_SERIAL
west flash --skip-rebuild -d build/simple_tx -r nrfutil --dev-id INIT_SERIAL
```

Keep both build directories and verify their role strings before flashing.
UART is 115200 with DTR asserted. Illustrative log shapes, not captured results:

```text
TX data send 7  ts=0x...
ANCHOR 1  RX [7]  ts=0x...  len=3  data: AB CD 07
```

## Review points before extending

The RX path copies `len-FCS_LEN` into a 128-byte buffer without first bounding
the received length or requiring the three-byte payload. It then indexes bytes
0–2 without validating the magic/length. TX and RX completion loops have no
host deadline, and some radio return values are ignored. These are reasons to
borrow the checked receive/send helpers rather than copy this loop into the
multi-board experiment.

This application uses the shared board overlay, which contains the inherited
unsupported GPIO1.19 wakeup mapping. See [platform notes](../../drivers/platform/README.md)
and the corrected overlays in the checked samples. An assertion-enabled panic
at startup is a board-integration issue, not evidence of a failed RF link.
