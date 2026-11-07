/*
 * spatial_resolution_tx — transmitter for the UWB reception-cliff experiment.
 *
 * Blasts bursts of N tagged packets down a line of receivers. Each packet
 * carries an epoch (burst counter) and a sequence number so each receiver
 * can compute its packet-reception ratio (PRR) for the burst.
 *
 * Pair with samples/spatial_resolution_rx on the receiving boards.
 * See experiments/spatial_resolution.md for the method.
 *
 * PHY config below MUST be identical to the RX app.
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include "deca_device_api.h"
#include "deca_probe_interface.h"
#include "dw3000_hw.h"
#include "port.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

/* ------------------------- experiment config ------------------------- */
#define BURST_LEN       500    /* packets per burst (N, the PRR denominator) */
#define TX_INTERVAL_MS  10     /* gap between packets within a burst         */
#define INTER_BURST_MS  1500   /* pause between bursts                       */

/* --------------------------- packet format --------------------------- */
/* [0]=magic [1]=epoch [2..3]=seq(LE) [4..5]=N(LE) */
#define PKT_MAGIC       0x55
#define PKT_LEN         6

/* ----------------------------- PHY config ---------------------------- */
static dwt_config_t uwb_cfg = {
    .chan           = 9,
    .txPreambLength = DWT_PLEN_128,
    .rxPAC          = DWT_PAC8,
    .txCode         = 9,
    .rxCode         = 9,
    .sfdType        = DWT_SFD_DW_8,
    .dataRate       = DWT_BR_6M8,
    .phrMode        = DWT_PHRMODE_STD,
    .phrRate        = DWT_PHRRATE_STD,
    .sfdTO          = (129 + 8 - 8),
    .stsMode        = DWT_STS_MODE_OFF,
    .stsLength      = DWT_STS_LEN_64,
    .pdoaMode       = DWT_PDOA_M0,
};

static int uwb_init(void)
{
    dw_device_init();

    dw3000_hw_wakeup_pin_low();
    Sleep(5);

    port_set_dw_ic_spi_slowrate();

    if (dwt_probe((struct dwt_probe_s *)&dw3000_probe_interf) != DWT_SUCCESS) {
        LOG_ERR("CAN NOT FIND CHIP DRIVER");
        return -1;
    }

    port_set_dw_ic_spi_fastrate();

    if (dwt_initialise(DWT_DW_INIT) != DWT_SUCCESS) {
        LOG_ERR("INITIALISATION FAILED");
        return -1;
    }

    if (dwt_configure(&uwb_cfg) != DWT_SUCCESS) {
        LOG_ERR("RADIO CONFIG FAILED");
        return -1;
    }

    dwt_setrxantennadelay(16385);
    dwt_settxantennadelay(16385);

    return 0;
}

static uint8_t tx_msg[PKT_LEN] = { PKT_MAGIC, 0, 0, 0, 0, 0 };

static void tx_loop(void)
{
    uint8_t epoch = 0;
    const uint16_t n = BURST_LEN;

    tx_msg[4] = (uint8_t)(n & 0xFF);
    tx_msg[5] = (uint8_t)(n >> 8);

    while (1) {
        LOG_INF("TX burst epoch=%u N=%u interval=%ums", epoch, n, TX_INTERVAL_MS);

        for (uint16_t seq = 0; seq < n; seq++) {
            tx_msg[1] = epoch;
            tx_msg[2] = (uint8_t)(seq & 0xFF);
            tx_msg[3] = (uint8_t)(seq >> 8);

            dwt_writetxdata(sizeof(tx_msg), tx_msg, 0);
            dwt_writetxfctrl(sizeof(tx_msg) + FCS_LEN, 0, 0);
            dwt_starttx(DWT_START_TX_IMMEDIATE);

            while (!(dwt_readsysstatuslo() & DWT_INT_TXFRS_BIT_MASK)) {
                /* wait for frame-sent */
            }
            dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK);

            Sleep(TX_INTERVAL_MS);
        }

        LOG_INF("TX burst epoch=%u done", epoch);
        epoch++;              /* wraps at 256 */
        Sleep(INTER_BURST_MS);
    }
}

int main(void)
{
    LOG_INF("spatial_resolution_tx starting");

    if (uwb_init() != 0) {
        LOG_ERR("UWB STARTUP FAILED");
        return -1;
    }
    LOG_INF("STARTUP SUCCESS");

    tx_loop();
    return 0;
}
