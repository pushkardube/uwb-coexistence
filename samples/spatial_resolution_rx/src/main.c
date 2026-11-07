/*
 * spatial_resolution_rx — receiver for the UWB reception-cliff experiment.
 *
 * Counts how many of each TX burst's N packets this board heard (PRR) and
 * estimates mean receive power (RSSI). At the end of every burst it both
 *   - logs a summary line over UART, and
 *   - pushes the same line to a laptop over BLE (Nordic UART Service / NUS).
 *
 * BLE line format (UTF-8, newline-terminated), all integers:
 *     <epoch>,<pos>,<recv>,<N>,<prr_hundredths>,<rssi_millidb>\n
 *   where PRR[%]   = prr_hundredths / 100
 *         RSSI[dB] = rssi_millidb   / 1000
 *
 * Pair with samples/spatial_resolution_tx on the transmitting board and
 * tools/collect_spatial.py on the laptop. PHY config MUST match the TX app.
 *
 * Set RX_POSITION_ID distinctly on each receiver before flashing.
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include "deca_device_api.h"
#include "deca_probe_interface.h"
#include "dw3000_hw.h"
#include "port.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

/* ------------------------- experiment config ------------------------- */
#define RX_POSITION_ID      1      /* per-board label (set per receiver)   */
#define BURST_LEN           500    /* must match the TX app's N            */
#define RX_GAP_TIMEOUT_MS   300    /* RX silence that ends a burst (>> TX interval) */
#define LOG_RSSI            1      /* 1 = compute/send mean RSSI estimate  */
#define MAX_BURST_LEN       2000   /* upper bound for the per-epoch bitmap */
#define RSSI_CONST_A        121.7f /* DW3000 CIR-power RSSI constant (approx) */

/* --------------------------- packet format --------------------------- */
#define PKT_MAGIC           0x55
#define PKT_LEN             6

/* ============================ BLE / NUS ============================== */
#define BT_UUID_NUS_VAL \
    BT_UUID_128_ENCODE(0x6E400001, 0xB5A3, 0xF393, 0xE0A9, 0xE50E24DCCA9EULL)
#define BT_UUID_NUS_RX_VAL \
    BT_UUID_128_ENCODE(0x6E400002, 0xB5A3, 0xF393, 0xE0A9, 0xE50E24DCCA9EULL)
#define BT_UUID_NUS_TX_VAL \
    BT_UUID_128_ENCODE(0x6E400003, 0xB5A3, 0xF393, 0xE0A9, 0xE50E24DCCA9EULL)

static struct bt_uuid_128 nus_uuid    = BT_UUID_INIT_128(BT_UUID_NUS_VAL);
static struct bt_uuid_128 nus_rx_uuid = BT_UUID_INIT_128(BT_UUID_NUS_RX_VAL);
static struct bt_uuid_128 nus_tx_uuid = BT_UUID_INIT_128(BT_UUID_NUS_TX_VAL);

static bool notifications_enabled;
static struct bt_conn *current_conn;

static void tx_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    ARG_UNUSED(attr);
    notifications_enabled = (value == BT_GATT_CCC_NOTIFY);
    LOG_INF("BLE notifications %s", notifications_enabled ? "enabled" : "disabled");
}

/* laptop → chip: unused here, accept and ignore so the char is writable */
static ssize_t rx_write(struct bt_conn *conn, const struct bt_gatt_attr *attr,
                        const void *buf, uint16_t len, uint16_t offset, uint8_t flags)
{
    ARG_UNUSED(conn); ARG_UNUSED(attr); ARG_UNUSED(buf);
    ARG_UNUSED(offset); ARG_UNUSED(flags);
    return len;
}

BT_GATT_SERVICE_DEFINE(nus_svc,
    BT_GATT_PRIMARY_SERVICE(&nus_uuid),
    BT_GATT_CHARACTERISTIC(&nus_rx_uuid.uuid,
        BT_GATT_CHRC_WRITE | BT_GATT_CHRC_WRITE_WITHOUT_RESP,
        BT_GATT_PERM_WRITE, NULL, rx_write, NULL),
    BT_GATT_CHARACTERISTIC(&nus_tx_uuid.uuid,
        BT_GATT_CHRC_NOTIFY, BT_GATT_PERM_NONE, NULL, NULL, NULL),
    BT_GATT_CCC(tx_ccc_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);

static const struct bt_le_adv_param adv_param =
    BT_LE_ADV_PARAM_INIT(BT_LE_ADV_OPT_CONN,
                         BT_GAP_ADV_FAST_INT_MIN_2, BT_GAP_ADV_FAST_INT_MAX_2, NULL);

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, BT_UUID_NUS_VAL),
};
static const struct bt_data sd[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
            sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static void mtu_exchange_cb(struct bt_conn *conn, uint8_t err,
                            struct bt_gatt_exchange_params *params)
{
    ARG_UNUSED(params);
    if (err) {
        LOG_WRN("MTU exchange failed (err %u)", err);
    } else {
        LOG_INF("MTU exchanged: %u", bt_gatt_get_mtu(conn));
    }
}
static struct bt_gatt_exchange_params mtu_params = { .func = mtu_exchange_cb };

static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        LOG_ERR("Connection failed (err %u)", err);
        return;
    }
    current_conn = bt_conn_ref(conn);
    LOG_INF("Connected");
    bt_gatt_exchange_mtu(conn, &mtu_params);
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    ARG_UNUSED(conn);
    LOG_INF("Disconnected (reason %u)", reason);
    if (current_conn) {
        bt_conn_unref(current_conn);
        current_conn = NULL;
    }
    notifications_enabled = false;
    int err = bt_le_adv_start(&adv_param, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (err) {
        LOG_ERR("Advertising restart failed (err %d)", err);
    }
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected    = connected,
    .disconnected = disconnected,
};

/* send one line to the laptop (TX char is attrs[3] in the table above) */
static void nus_send(const char *text, uint16_t len)
{
    if (!notifications_enabled || !current_conn) {
        return;
    }
    bt_gatt_notify(current_conn, &nus_svc.attrs[3], text, len);
}

/* ============================ UWB PHY ================================= */
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

#if LOG_RSSI
    dwt_configciadiag(DW_CIA_DIAG_LOG_ALL);
#endif
    return 0;
}

/* ============================ RX counting ============================= */
static uint8_t seen[(MAX_BURST_LEN + 7) / 8];

static int      cur_epoch = -1;
static uint16_t cur_n     = 0;
static uint32_t received  = 0;
#if LOG_RSSI
static double   rssi_sum  = 0.0;
#endif

static inline void seen_clear(void) { memset(seen, 0, sizeof(seen)); }

static inline int seen_mark(uint16_t seq)
{
    if (seq >= MAX_BURST_LEN) {
        return 0;
    }
    uint8_t  bit = 1u << (seq & 7);
    uint16_t idx = seq >> 3;
    if (seen[idx] & bit) {
        return 0;
    }
    seen[idx] |= bit;
    return 1;
}

#if LOG_RSSI
static double estimate_rssi_db(void)
{
    dwt_rxdiag_t diag;
    dwt_readdiagnostics(&diag);
    double c = (double)diag.ipatovPower;
    double nacc = (double)diag.ipatovAccumCount;
    if (nacc <= 0.0 || c <= 0.0) {
        return -200.0;        /* sentinel: diagnostics unavailable */
    }
    return 10.0 * log10((c * 2097152.0) / (nacc * nacc)) - (double)RSSI_CONST_A;
}
#endif

static void start_burst(uint8_t epoch, uint16_t n)
{
    cur_epoch = epoch;
    cur_n     = n;
    received  = 0;
#if LOG_RSSI
    rssi_sum  = 0.0;
#endif
    seen_clear();
}

static void finalize_burst(void)
{
    if (cur_epoch < 0 || received == 0) {
        return;
    }
    uint16_t n = cur_n ? cur_n : BURST_LEN;
    uint32_t prr_cc = (uint32_t)((received * 10000ULL) / n);

    char line[96];
    int len;
#if LOG_RSSI
    int rssi_milli = (int)((rssi_sum / (double)received) * 1000.0);
    len = snprintf(line, sizeof(line), "%d,%d,%u,%u,%u,%d\n",
                   cur_epoch, RX_POSITION_ID, received, n, prr_cc, rssi_milli);
    LOG_INF("epoch=%d pos=%d recv=%u N=%u PRR=%u.%02u%% rssi=%d.%03ddB",
            cur_epoch, RX_POSITION_ID, received, n, prr_cc / 100, prr_cc % 100,
            rssi_milli / 1000, (rssi_milli < 0 ? -rssi_milli : rssi_milli) % 1000);
#else
    len = snprintf(line, sizeof(line), "%d,%d,%u,%u,%u,0\n",
                   cur_epoch, RX_POSITION_ID, received, n, prr_cc);
    LOG_INF("epoch=%d pos=%d recv=%u N=%u PRR=%u.%02u%%",
            cur_epoch, RX_POSITION_ID, received, n, prr_cc / 100, prr_cc % 100);
#endif
    if (len > 0 && len < (int)sizeof(line)) {
        nus_send(line, (uint16_t)len);
    }
}

static void rx_loop(void)
{
    uint8_t rx_buffer[128];

    while (1) {
        dwt_rxenable(DWT_START_RX_IMMEDIATE);

        int64_t deadline = k_uptime_get() + RX_GAP_TIMEOUT_MS;
        uint32_t status  = 0;
        int got = 0;

        while (k_uptime_get() < deadline) {
            status = dwt_readsysstatuslo();
            if (status & DWT_INT_RXFCG_BIT_MASK) {
                got = 1;
                break;
            }
            if (status & SYS_STATUS_ALL_RX_ERR) {
                dwt_writesysstatuslo(SYS_STATUS_ALL_RX_ERR);
                dwt_rxenable(DWT_START_RX_IMMEDIATE);
            }
            k_yield();        /* let the BLE stack run */
        }

        if (!got) {
            finalize_burst();
            cur_epoch = -1;
            continue;
        }

        uint16_t len = dwt_getframelength();
        if (len >= PKT_LEN + FCS_LEN) {
            dwt_readrxdata(rx_buffer, len - FCS_LEN, 0);
            if (rx_buffer[0] == PKT_MAGIC) {
                uint8_t  epoch = rx_buffer[1];
                uint16_t seq   = (uint16_t)rx_buffer[2] | ((uint16_t)rx_buffer[3] << 8);
                uint16_t n     = (uint16_t)rx_buffer[4] | ((uint16_t)rx_buffer[5] << 8);

                if (cur_epoch < 0) {
                    start_burst(epoch, n);
                } else if ((uint8_t)cur_epoch != epoch) {
                    finalize_burst();
                    start_burst(epoch, n);
                }
                if (seen_mark(seq)) {
                    received++;
#if LOG_RSSI
                    rssi_sum += estimate_rssi_db();
#endif
                }
            }
        }

        dwt_writesysstatuslo(DWT_INT_RXFCG_BIT_MASK |
                             SYS_STATUS_ALL_RX_ERR |
                             SYS_STATUS_ALL_RX_TO);
    }
}

int main(void)
{
    LOG_INF("spatial_resolution_rx starting, pos=%d", RX_POSITION_ID);

    int err = bt_enable(NULL);
    if (err) {
        LOG_ERR("BLE enable failed (err %d)", err);
        return err;
    }
    LOG_INF("BLE ready");

    err = bt_le_adv_start(&adv_param, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (err) {
        LOG_ERR("Advertising start failed (err %d)", err);
        return err;
    }
    LOG_INF("Advertising as \"%s\"", CONFIG_BT_DEVICE_NAME);

    if (uwb_init() != 0) {
        LOG_ERR("UWB STARTUP FAILED");
        return -1;
    }
    LOG_INF("STARTUP SUCCESS");

    rx_loop();
    return 0;
}
