/*
 * Minimal sanity-check app for the DWM3001CDK board.
 *
 * Blinks led0 (D9 green LED) and logs a heartbeat over the console UART.
 * Use this to confirm the toolchain, board files and flashing setup work
 * before building anything that touches the DW3000 radio.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

#define LED0_NODE DT_ALIAS(led0)

static const struct gpio_dt_spec led0 = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

int main(void)
{
    LOG_INF("DWM3001CDK app boot");

    if (!gpio_is_ready_dt(&led0)) {
        LOG_ERR("led0 device not ready");
        return -1;
    }

    int ret = gpio_pin_configure_dt(&led0, GPIO_OUTPUT_ACTIVE);
    if (ret < 0) {
        LOG_ERR("failed to configure led0 (%d)", ret);
        return ret;
    }

    while (1) {
        gpio_pin_toggle_dt(&led0);
        LOG_INF("heartbeat");
        k_sleep(K_MSEC(500));
    }

    return 0;
}
