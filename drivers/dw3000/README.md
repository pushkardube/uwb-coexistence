# Linked DW3000 vendor driver

This directory contains headers, linker sections and precompiled 6.0.14 driver
archives rather than the application ranging implementation. See
[DW3000_API_GUIDE.md](DW3000_API_GUIDE.md) for the existing API reference and
[../platform/README.md](../platform/README.md) for the Zephyr transport/IRQ glue.

CMake selects libdwt_uwb_driver-m4-hfp-6.0.14.a when CONFIG_FPU is enabled and
the corresponding sfp archive otherwise, links it whole-archive, exposes inc/,
and installs custom-sections.ld. A firmware sample is built from its own
directory; this driver folder is not a standalone west application.

The checked experiment's source is under samples/twr_checked_*_common. Diagnosis
of API memory writes or register side effects must account for the exact linked
archive, matching public structures, active RX mode and transaction sequence.
Nearby COSIC SDK source is useful reference material, but a different revision
does not prove this binary's internal behavior. Historical claims that a read
must corrupt double buffering were not uniquely demonstrated.

The current corrected RSSI estimate uses raw C/N/D with the DW3000-specific
2^21 normalization and the reference vendor-model +6*D term. Do not substitute
another chip family's normalization or treat these estimates as an absolute
power calibration. See [the checked combined guide](../../samples/twr_checked_combined_common/README.md).
