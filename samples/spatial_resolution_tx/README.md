# Numbered UWB bursts for spatial reception measurements

Status: experimental packet generator; this documentation pass does not establish
a successful end-to-end PRR/BLE hardware test. Pair with
[spatial_resolution_rx](../spatial_resolution_rx/README.md). This is the one-way
burst experiment, separate from the checked DS-TWR power sweep.

## Purpose and packet format

[src/main.c](src/main.c) repeatedly sends numbered bursts so every receiver can
count unique packets independently. No receiver sends a UWB response, so any
number of receivers can observe the same burst without response collisions.
The transmitter does not learn who received it.

| Payload bytes | Field |
|---|---|
| 0 | Magic 0x55 |
| 1 | Eight-bit burst epoch |
| 2–3 | Sixteen-bit sequence, little-endian |
| 4–5 | Advertised packet count N, little-endian |

Payload length is six bytes, plus the two-byte hardware FCS. Sequence runs
0 through N-1. Epoch increments after each burst and wraps after 256 bursts;
it is not a globally unique run identifier.

| Source define | Default |
|---|---:|
| `BURST_LEN` | 500 packets |
| `TX_INTERVAL_MS` | 10 ms pause after each packet |
| `INTER_BURST_MS` | 1500 ms additional inter-burst pause |

The nominal packet pauses total five seconds per burst, plus actual TX/SPI
work and the inter-burst gap. PHY: channel 9, preamble 128, code 9, 6.8 Mb/s,
STS off. No TX-power sweep is programmed here; an explicit power setting or
experimental power controller would need to be added before interpreting
results as a recorded power-dependent reception boundary.

## Build, flash and readout

```bash
source tools/ncs_env.sh
west build -b decawave_dwm3001cdk samples/spatial_resolution_tx -d build/spatial_tx -p always
west flash --skip-rebuild -d build/spatial_tx -r nrfutil --dev-id TX_SERIAL
```

There is no role switch in this project. Edit burst settings in source before
building, and record the values with each run. Receiver PHY and expected burst
length must agree. UART is 115200; an illustrative log shape is:

```text
TX burst epoch=0 N=500 interval=10ms
```

This line announces the intended burst. It does not prove all 500 packets were
transmitted successfully or received. The TX completion wait has no host deadline
and the start-TX return value is not checked.

## Experiment boundaries

The actual reception data comes from receiver summaries or the BLE collector,
not the TX startup log. Record transmitter burst epochs independently so a
receiver with zero observed packets can be distinguished from a disconnected,
crashed or unmonitored board. The receiver currently cannot emit its own row
for an epoch it never hears.

The application uses the legacy shared overlay with the inherited wakeup-GPIO
issue; consult [platform integration](../../drivers/platform/README.md).
For the intended board-4/board-5 test, see
[the spatial experiment](../../experiments/spatial_resolution.md) and
[the current distance/power experiment](../../experiments/checked_combined_bench.md).
