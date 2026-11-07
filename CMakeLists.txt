cmake_minimum_required(VERSION 3.20)

set(BOARD decawave_dwm3001cdk)
set(DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(dwm3001cdk_app)

target_sources(app PRIVATE
    src/main.c
)
