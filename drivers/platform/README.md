# Zephyr platform layer used by the DW3000 samples

This is library glue, not a standalone application. Sample CMake files compile
these four C files alongside their application and link the vendor driver archive.
The [sample index](../../samples/README.md) identifies which applications use it.

## File ownership

| File | Responsibility |
|---|---|
| dw3000_spi.c | SPI read/write/CRC transactions, slow/fast configuration, CS wakeup |
| dw3000_hw.c | Reset/wakeup GPIO, optional SPI pins, interrupt setup and deferred ISR |
| port.c | Vendor-style Sleep/reset/SPI-rate entry points |
| deca_port.c | Probe function table, IRQ-mask hooks and driver sleep callbacks |

`dw_device_init()` calls hardware init and reset. Its void interface does not
propagate the initialization return code to callers. Samples then select slow
SPI, probe the driver, switch fast, initialize and configure the radio.
This ordering does not replace explicit API error checks.

## SPI behavior

The device is selected from the first qorvo,dw3000 devicetree instance. SPI uses
the spi3 node and manual CS spec from dwm3000. Slow configuration is 2 MHz.
Fast defaults to 8 MHz, but the nRF52833/nRF52840 branch selects 32 MHz except
the DWS3000-shield branch, which selects 16 MHz. The active DWM3001CDK build
uses the nRF52833 path. Changing spi-max-frequency in an overlay does not by
itself rewrite these hardcoded configuration frequencies.

Read transactions transmit a header and receive/discard corresponding header
bytes before collecting the requested payload. Writes send header/body; the
CRC callback adds a CRC byte. Return values come from spi_transceive, but the
sample/vendor call path must actually inspect them to detect transport failures.
The nRF52840-specific post-read spin workaround is conditional and should not
be assumed active on the nRF52833.

## GPIO overlay and the corrected checked-sample behavior

The shared [board overlay](../../boards/decawave_dwm3001cdk.overlay) contains:

| Function | Mapping |
|---|---|
| Reset | GPIO0.25, active low |
| IRQ | GPIO1.2, active high |
| SPI CS | GPIO1.6, active low |
| Optional wakeup | **GPIO1.19, inherited unsupported mapping** |

Assertion-enabled checked startup exposed an Unsupported pin panic at the
optional GPIO1.19 mapping. The checked sample families use their own overlays
that omit this property; shared legacy samples still use the original overlay.
No replacement pin was guessed. GPIO0.19 is used by the UART and is not a
drop-in alternative just because its pin number looks similar.

When wakeup-gpios is absent, dw3000_hw_wakeup falls back to CS. Checked ranging
does not use radio sleep mode; its healthy captures establish that tested
awake-use path, not every possible sleep/resume sequence. Reset drives the
active-low pin then releases it as an input, with millisecond delays.

## Interrupts and concurrency

GPIO IRQ submits a work item, whose handler calls dwt_isr. `port_set_dwic_isr()`
initializes that path rather than storing a supplied callback pointer. Most
current ranging loops poll radio status instead of relying on callbacks.

`decamutexon()` disables the radio GPIO interrupt and returns a constant;
`decamutexoff()` enables it again without restoring a saved prior state. This
is not a Zephyr mutex, not an SPI ownership lock and not a general nested critical
section. Do not infer thread-safe concurrent radio access from those names.
The checked experiment relies on a single application owner for its transactions.

## Build dependencies and review points

Samples need SPI, GPIO, the matching devicetree binding and the vendor probe
interface. [../dw3000/CMakeLists.txt](../dw3000/CMakeLists.txt) selects the
6.0.14 hard-float archive when CONFIG_FPU is enabled, soft-float otherwise,
and includes custom linker sections. Do not mix headers from another driver
revision simply because the function names match.

Hardware fini contains incomplete cleanup, optional GPIO configuration returns
are not comprehensively checked, and SPI initialization does not provide the
same readiness/ownership contract as a fully encapsulated Zephyr driver. These
are review findings retained here rather than changes to the currently tested
firmware. See [the API guide](../dw3000/DW3000_API_GUIDE.md) for reference types;
matching bundled headers and actual linked artifacts remain authoritative.
