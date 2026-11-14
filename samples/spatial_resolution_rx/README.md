# UWB burst receiver with UART and BLE reception summaries

Status: experimental one-way PRR receiver; no new end-to-end hardware result
is claimed here. Companion transmitter:
[spatial_resolution_tx](../spatial_resolution_tx/README.md). Laptop collector:
[tools/collect_spatial.py](../../tools/collect_spatial.py).

## Code paths

[src/main.c](src/main.c) enables BLE, advertises `DWM3001-RX`, initializes the
DW3000, and enters `rx_loop()`. Packets use the transmitter's six-byte format:
`55 epoch seq16_le N16_le`. A bitmap deduplicates sequence numbers. An epoch
change or an RX gap longer than 300 ms finalizes the current burst.

| Setting | Default | Meaning |
|---|---:|---|
| `RX_POSITION_ID` | 1 | Per-board position label; edit for every receiver |
| `BURST_LEN` | 500 | Fallback denominator if packet N is zero |
| `RX_GAP_TIMEOUT_MS` | 300 ms | Silence that ends the current burst |
| `MAX_BURST_LEN` | 2000 | Maximum sequence index tracked by the bitmap |
| `LOG_RSSI` | 1 | Read diagnostics and include mean approximate RSSI |

RX yields while waiting so BLE work can run. UWB PHY matches the TX: channel 9,
preamble 128, code 9, 6.8 Mb/s, STS off. The RSSI estimate uses Ipatov C/N data
from `dwt_readdiagnostics()`, without the checked sweep's `+6*D` correction.
`-200000` means unavailable RSSI; RSSI zero when LOG_RSSI=0 is a placeholder.

## UART/BLE contract

Every finalized nonempty burst can produce an integer notification:

```text
epoch,pos,received,N,prr_hundredths,rssi_millidb
```

Illustrative payload: `3,2,495,500,9900,-85000` means epoch 3, position 2,
495/500 packets, 99.00%, approximate mean RSSI -85.000 dB. This is a schema
example, not a saved bench result. UART also prints a human-readable summary.

The Nordic UART Service uses service UUID `6e400001-b5a3-f393-e0a9-e50e24dcca9e`;
the laptop subscribes to TX notifications at UUID ending `0003`. The RX write
characteristic accepts data but does not implement radio commands. BLE connection
count is one per receiver, and MTU exchange supports longer notifications.
`bt_gatt_notify()` return values are currently ignored and summaries are not
queued for later reconnection.

## Build and collect

`RX_POSITION_ID` is an unconditional source define; edit it before each build.

```bash
source tools/ncs_env.sh
# Set RX_POSITION_ID=1 in source, then build:
west build -b decawave_dwm3001cdk samples/spatial_resolution_rx -d build/spatial_rx1 -p always
west flash --skip-rebuild -d build/spatial_rx1 -r nrfutil --dev-id RX_SERIAL
```

Use another build directory for each additional position label. In a separate
system-Python shell with Bleak installed:

```bash
mkdir -p captures/spatial
python3 tools/collect_spatial.py --csv captures/spatial/run1.csv --duration 120
```

The collector tags rows by BLE address as well as position; identical advertised
names are expected. Review [collector limitations](../../tools/README.md).

## Issues to resolve before treating this as a PRR instrument

No summary is emitted for a burst with zero received packets. Missing telemetry
alone does not prove 0% PRR. Use a known TX epoch schedule and independently
verify receiver health/telemetry availability before assigning a zero.

The RX path checks a minimum frame size but does not bound a copy to its 128-byte
buffer. Bitmap admission checks sequence <2000, not sequence <advertised N, and
inconsistent N values within an epoch are not rejected. Long RF gaps can split
a single epoch into multiple summaries. The eight-bit epoch wraps, and BLE
notification failures are not retried. These limits matter near a reception edge.

This app still uses the legacy shared wakeup overlay, unlike checked ranging.
See [platform notes](../../drivers/platform/README.md) and
[the experimental method](../../experiments/spatial_resolution.md).
