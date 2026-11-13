cmake_minimum_required(VERSION 3.20)

set(BOARD decawave_dwm3001cdk)
set(DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../..)
list(APPEND EXTRA_DTC_OVERLAY_FILE ${CMAKE_CURRENT_SOURCE_DIR}/../twr_checked_combined_common/board.overlay)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(twr_checked_ble_init)

add_subdirectory(../../drivers/dw3000 dw3000)

target_include_directories(app PRIVATE
    ../../drivers/dw3000/inc
    ../../drivers/platform
)

target_sources(app PRIVATE
    src/main.c
    ../../drivers/platform/dw3000_spi.c
    ../../drivers/platform/dw3000_hw.c
    ../../drivers/platform/port.c
    ../../drivers/platform/deca_port.c
)

set(CHECKED_RESP_ID 0 CACHE STRING "Responder identifier")
set(CHECKED_RSSI 1 CACHE STRING "Read Final RSSI after timestamp capture")
zephyr_get(CHECKED_RESP_ID)
zephyr_get(CHECKED_RSSI)
target_sources(app PRIVATE ../twr_checked_combined_common/checked.c)
target_include_directories(app PRIVATE ../twr_checked_combined_common)
target_compile_definitions(app PRIVATE CHECKED_INITIATOR=1 CHECKED_RESP_ID=${CHECKED_RESP_ID} CHECKED_RSSI=${CHECKED_RSSI})

set(CHECKED_N_RESPONDERS 2 CACHE STRING "Number of addressed responders (1..16)")
zephyr_get(CHECKED_N_RESPONDERS)
target_compile_definitions(app PRIVATE CHECKED_N_RESPONDERS=${CHECKED_N_RESPONDERS})

set(SWEEP_ATTEMPTS 10 CACHE STRING "Attempts per peer per power level")
zephyr_get(SWEEP_ATTEMPTS)
target_compile_definitions(app PRIVATE SWEEP_ATTEMPTS=${SWEEP_ATTEMPTS})

target_sources(app PRIVATE ../twr_checked_ble_common/telemetry.c)
target_include_directories(app PRIVATE ../twr_checked_ble_common)
target_compile_definitions(app PRIVATE CHECKED_BLE=1)
