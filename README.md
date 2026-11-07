# uwb-coexistence

Zephyr / nRF Connect SDK project for the **DWM3001CDK** board
(Qorvo DW3000 UWB + nRF52833), aimed at UWB coexistence work.

The board-support layer (DW3000 driver, platform HAL, board overlay,
devicetree binding) was carried over from `zephyr-dwm3001cdk-app` so the
hardware plumbing doesn't have to be redone. This repo is a clean base to
build coexistence experiments on top of the same hardware.

---

## Structure

```
.
├── CMakeLists.txt / prj.conf / src/main.c   # Root app: LED + log heartbeat,
│                                             # sanity-checks the board/toolchain.
├── boards/
│   └── decawave_dwm3001cdk.overlay          # DW3000 SPI device node (spi3)
├── dts/bindings/decawave,dw3000/            # devicetree binding for the DW3000 node
├── drivers/
│   ├── dw3000/                              # Vendor DW3000 driver (precompiled lib + headers)
│   └── platform/                            # SPI glue / reset / IRQ / port abstraction (HAL)
├── research/                                # UWB co-existence background
│   │                                        #   (SteelSeries SPARK UWB mouse vs. 802.15.4z
│   │                                        #    ranging) — notes, product survey, saved sources
│   ├── SUMMARY_v2.md / uwb_products.md / MOUSE_VS_RANGING_INTERFERENCE.md ...
│   ├── sources/  (saved HTML + Spark SR1120 datasheet)
│   └── text/     (plaintext extractions)
├── experiments/
│   └── spatial_resolution.md                # Reception-cliff experiment design
├── tools/
│   ├── ncs_env.sh                           # activates the NCS v3.2.4 toolchain
│   └── collect_spatial.py                   # laptop BLE collector (bleak) -> CSV
└── samples/
    ├── simple_txrx/                         # Minimal DW3000 TX/RX starter, builds standalone
    ├── spatial_resolution_tx/               # Spatial-resolution experiment: transmitter
    └── spatial_resolution_rx/               # Spatial-resolution experiment: receiver + BLE stream
```

See [experiments/spatial_resolution.md](experiments/spatial_resolution.md)
for the spatial-resolution experiment (TX/RX firmware + BLE data collection).

The root app and every folder under `samples/` are independent Zephyr
applications — each has its own `CMakeLists.txt` + `prj.conf` and is built
separately. They share `drivers/` and `boards/` via relative paths, so
adding a new sample is just: copy `samples/simple_txrx`, rename, edit
`src/main.c`.

## Toolchain

This machine has nRF Connect SDK **v3.2.4** at `~/ncs/v3.2.4`, with the
toolchain bundle at `~/ncs/toolchains/2ac5840438`. The `nrfutil
toolchain-manager` plugin is not installed, so the toolchain is activated
by sourcing `tools/ncs_env.sh` (sets `PATH`, `ZEPHYR_BASE`,
`ZEPHYR_SDK_INSTALL_DIR`, etc.) before any `west` command.

```bash
source tools/ncs_env.sh
```

## Building

```bash
source tools/ncs_env.sh

# Root sanity-check app (no UWB, just blinks led0 and logs a heartbeat)
west build -b decawave_dwm3001cdk .

# DW3000 TX/RX starter sample
west build -b decawave_dwm3001cdk samples/simple_txrx

west flash
```

`samples/simple_txrx/src/main.c` has a `ROLE_TRANSMITTER` compile switch
(set `1` for TX, `0` for RX) — flash one board as TX and another as RX.

## Adding a new sample

1. `cp -r samples/simple_txrx samples/<new_name>`
2. Edit `samples/<new_name>/CMakeLists.txt`: change `project(...)` name.
3. Edit `samples/<new_name>/src/main.c` with your application logic.
4. Build with `west build -b decawave_dwm3001cdk samples/<new_name>`.
