/* Independent DS-TWR protocol. Old marker-only samples are not compatible.
 * No float printf, no logging in RX-to-delayed-TX windows, no alternating sessions.
 * Final RSSI is captured at the responder AFTER the last required RX timestamp.
 */
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <string.h>
#include <limits.h>
#include "deca_device_api.h"
#include "deca_probe_interface.h"
#include "dw3000_hw.h"
#include "port.h"
#include "checked.h"
#include "multi_plan.h"

#define CANARY 0x83A759C1u
#define HEADER 9u
#define POLL_LEN HEADER
#define RESP_LEN (HEADER + 10u)
#define FINAL_LEN (HEADER + 10u)
#define RESULT_LEN (HEADER + 5u + 4u + 1u + 4u + 2u + 1u)
#define ANT_DELAY 16385u
#define REPLY_DTU UINT64_C(159744000) /* 2500 SI us, explicit DTU */
#define RX_MASK (DWT_INT_RXFCG_BIT_MASK | SYS_STATUS_ALL_RX_ERR | SYS_STATUS_ALL_RX_TO)
#define CLEAR_MASK (RX_MASK | DWT_INT_CIADONE_BIT_MASK | DWT_INT_CIAERR_BIT_MASK | DWT_INT_TXFRS_BIT_MASK)
#define NO_RSSI INT32_MIN

#if CHECKED_RESP_ID < 0 || CHECKED_RESP_ID > 255
#error "CHECKED_RESP_ID must fit the on-air identifier"
#endif
#if CHECKED_RSSI != 0 && CHECKED_RSSI != 1
#error "CHECKED_RSSI must be 0 or 1"
#endif

enum { POLL = 1, RESPONSE, FINAL, RESULT };
enum { OK, TIMEOUT, RADIO_ERROR, BAD_LENGTH, BAD_HEADER, BAD_SEQUENCE,
       CIA_TIMEOUT, TX_LATE, BAD_INTERVAL, MEMORY_ERROR, BAD_RANGE };

static struct {
    uint32_t before;
    uint8_t rx[64];
    uint8_t tx[64];
    uint8_t ts[5];
    uint8_t pad[3];
    uint32_t after;
} buffers;
static struct {
    uint32_t before;
    dwt_nlos_alldiag_t data;
    uint32_t after;
} diagnostics;
static struct {
    uint32_t before, seq, seq_inv, attempts, success;
    uint32_t peer, peer_inv;
    uint64_t t[6];
    int32_t rssi_mdB;
    uint32_t power;
    uint16_t accum;
    uint8_t dgc, diag_ok;
    uint32_t status, after;
} state;

static dwt_config_t config = {
    .chan=9, .txPreambLength=DWT_PLEN_128, .rxPAC=DWT_PAC8,
    .txCode=9, .rxCode=9, .sfdType=DWT_SFD_DW_8,
    .dataRate=DWT_BR_6M8, .phrMode=DWT_PHRMODE_STD,
    .phrRate=DWT_PHRRATE_STD, .sfdTO=129,
    .stsMode=DWT_STS_MODE_OFF, .stsLength=DWT_STS_LEN_64,
    .pdoaMode=DWT_PDOA_M0,
};

#if CHECKED_INITIATOR
static struct { uint32_t attempts, success; } peers[CHECKED_N_RESPONDERS];
#endif
static void select_peer(uint32_t peer)
{
    state.peer=peer;
    state.peer_inv=~peer;
}
static bool intact(void)
{
    return buffers.before == CANARY && buffers.after == CANARY &&
           state.before == CANARY && state.after == CANARY &&
           state.seq_inv == ~state.seq && state.peer_inv == ~state.peer &&
           state.peer<=255 && diagnostics.before == CANARY &&
           diagnostics.after == CANARY;
}
static void sequence(uint32_t seq)
{
    state.seq = seq;
    state.seq_inv = ~seq;
}
static int clean(int result)
{
    dwt_forcetrxoff();
    dwt_writesysstatuslo(CLEAR_MASK);
    return intact() ? result : MEMORY_ERROR;
}
static void header(unsigned type)
{
    memset(buffers.tx, 0, sizeof(buffers.tx));
    buffers.tx[0]=0xC7; buffers.tx[1]=0x51; buffers.tx[2]=3;
    buffers.tx[3]=(uint8_t)type; buffers.tx[4]=(uint8_t)state.peer;
    put_le(&buffers.tx[5], state.seq, 4);
}
static int timestamp(bool tx, uint64_t *out)
{
    memset(buffers.ts, 0xA5, sizeof(buffers.ts));
    if (tx) dwt_readtxtimestamp(buffers.ts);
    else dwt_readrxtimestamp(buffers.ts);
    *out = get_le(buffers.ts, 5);
    return intact() ? OK : MEMORY_ERROR;
}
static int wait_bits(uint32_t success, uint32_t errors, unsigned timeout_ms)
{
    int64_t deadline = k_uptime_get() + timeout_ms;
    do {
        state.status = dwt_readsysstatuslo();
        if (!intact()) return MEMORY_ERROR;
        if (state.status & errors) return RADIO_ERROR;
        if (state.status & success) return OK;
        k_busy_wait(20);
    } while (k_uptime_get() < deadline);
    return TIMEOUT;
}
/* Expected payload size is checked BEFORE subtracting FCS or copying any bytes. */
static int receive(unsigned type, unsigned payload, bool accept_poll)
{
    int rc = wait_bits(DWT_INT_RXFCG_BIT_MASK,
                      SYS_STATUS_ALL_RX_ERR | SYS_STATUS_ALL_RX_TO, 80);
    if (rc != OK) return rc;
    uint16_t wire_len = dwt_getframelength();
    if (wire_len != payload + FCS_LEN || payload > sizeof(buffers.rx)) return BAD_LENGTH;
    memset(buffers.rx, 0, sizeof(buffers.rx));
    dwt_readrxdata(buffers.rx, (uint16_t)payload, 0);
    if (!intact()) return MEMORY_ERROR;
    if (buffers.rx[0]!=0xC7 || buffers.rx[1]!=0x51 || buffers.rx[2]!=3 ||
        buffers.rx[3]!=type || buffers.rx[4]!=state.peer) return BAD_HEADER;
    uint32_t seq = (uint32_t)get_le(&buffers.rx[5], 4);
    if (accept_poll) sequence(seq);
    else if (seq != state.seq) return BAD_SEQUENCE;
    return OK;
}
static int precise_rx(uint64_t *out)
{
    int rc = wait_bits(DWT_INT_CIADONE_BIT_MASK, DWT_INT_CIAERR_BIT_MASK, 10);
    if (rc != OK) return rc == MEMORY_ERROR ? rc : CIA_TIMEOUT;
    return timestamp(false, out);
}
static int arm_rx(void)
{
    dwt_writesysstatuslo(CLEAR_MASK);
    dwt_setrxtimeout(50000); /* Qorvo UUS, ~51 ms */
    return dwt_rxenable(DWT_START_RX_IMMEDIATE)==DWT_SUCCESS ? OK : RADIO_ERROR;
}
static int send(unsigned length, bool delayed)
{
    if (!intact()) return MEMORY_ERROR;
    dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK);
    dwt_writetxdata((uint16_t)length, buffers.tx, 0);
    dwt_writetxfctrl((uint16_t)(length+FCS_LEN), 0, 0);
    if (dwt_starttx(delayed ? DWT_START_TX_DELAYED : DWT_START_TX_IMMEDIATE)!=DWT_SUCCESS)
        return delayed ? TX_LATE : RADIO_ERROR;
    int rc = wait_bits(DWT_INT_TXFRS_BIT_MASK, 0, 30);
    if (rc == OK) dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK);
    return rc;
}
static uint64_t schedule_after(uint64_t rx)
{
    uint32_t programmed=(uint32_t)(((rx+REPLY_DTU)&TS40_MASK)>>8);
    dwt_setdelayedtrxtime(programmed);
    return ((((uint64_t)(programmed & 0xFFFFFFFEu))<<8)+ANT_DELAY)&TS40_MASK;
}
#if !CHECKED_INITIATOR
static void capture_rssi(void)
{
    state.rssi_mdB=NO_RSSI; state.diag_ok=0;
    state.power=0; state.accum=0; state.dgc=0;
#if CHECKED_RSSI
    memset(&diagnostics.data, 0, sizeof(diagnostics.data));
    diagnostics.data.diag_type=IPATOV;
    uint8_t rc=dwt_nlos_alldiag(&diagnostics.data);
    if (!intact() || rc!=DWT_SUCCESS) return;
    state.power=diagnostics.data.cir_power;
    state.accum=(uint16_t)diagnostics.data.accumCount;
    state.dgc=diagnostics.data.D;
    if (state.power && state.accum) {
        /* Legacy estimator retained as an uncalibrated relative metric.
         * Return C,N,D too, so host calibration can use the exact driver model. */
        double value=10.0*log10(((double)state.power*2097152.0)/
                              ((double)state.accum*state.accum))-121.7;
        if (isfinite(value) && value>-250 && value<100) {
            state.rssi_mdB=(int32_t)lround(value*1000.0);
            state.diag_ok=1;
        }
    }
#endif
}
#endif

#if CHECKED_INITIATOR
static int exchange(void)
{
    int rc;
    header(POLL);
    if ((rc=send(POLL_LEN,false))) return rc;
    if ((rc=timestamp(true,&state.t[0]))) return rc;
    if ((rc=arm_rx())) return rc;
    if ((rc=receive(RESPONSE,RESP_LEN,false))) return rc;
    if ((rc=precise_rx(&state.t[3]))) return rc;
    state.t[1]=get_le(&buffers.rx[HEADER],5);
    state.t[2]=get_le(&buffers.rx[HEADER+5],5);
    dwt_writesysstatuslo(CLEAR_MASK);
    uint64_t predicted=schedule_after(state.t[3]);
    header(FINAL);
    put_le(&buffers.tx[HEADER],state.t[3],5);
    put_le(&buffers.tx[HEADER+5],predicted,5);
    if ((rc=send(FINAL_LEN,true))) return rc;
    if ((rc=timestamp(true,&state.t[4]))) return rc;
    if ((rc=arm_rx())) return rc;
    if ((rc=receive(RESULT,RESULT_LEN,false))) return rc;
    state.t[5]=get_le(&buffers.rx[HEADER],5);
    uint32_t raw=(uint32_t)get_le(&buffers.rx[HEADER+5],4);
    state.rssi_mdB=(raw & 0x80000000u) ? (int32_t)((int64_t)raw-INT64_C(4294967296)) : (int32_t)raw;
    state.diag_ok=buffers.rx[HEADER+9];
    state.power=(uint32_t)get_le(&buffers.rx[HEADER+10],4);
    state.accum=(uint16_t)get_le(&buffers.rx[HEADER+14],2);
    state.dgc=buffers.rx[HEADER+16];
    return intact() ? OK : MEMORY_ERROR;
}
#else
static int exchange(void)
{
    int rc;
    if ((rc=arm_rx())) return rc;
    if ((rc=receive(POLL,POLL_LEN,true))) return rc;
    if ((rc=precise_rx(&state.t[1]))) return rc;
    dwt_writesysstatuslo(CLEAR_MASK);
    state.t[2]=schedule_after(state.t[1]);
    header(RESPONSE);
    put_le(&buffers.tx[HEADER],state.t[1],5);
    put_le(&buffers.tx[HEADER+5],state.t[2],5);
    if ((rc=send(RESP_LEN,true))) return rc;
    if ((rc=arm_rx())) return rc;
    if ((rc=receive(FINAL,FINAL_LEN,false))) return rc;
    if ((rc=precise_rx(&state.t[5]))) return rc;
    /* No future ranging timestamp is read after this diagnostic call. */
    capture_rssi();
    if (!intact()) return MEMORY_ERROR;
    dwt_writesysstatuslo(CLEAR_MASK);
    /* Leave initiator time to arm its Result receiver, even with RSSI disabled. */
    k_msleep(3);
    header(RESULT);
    put_le(&buffers.tx[HEADER],state.t[5],5);
    put_le(&buffers.tx[HEADER+5],(uint32_t)state.rssi_mdB,4);
    buffers.tx[HEADER+9]=state.diag_ok;
    put_le(&buffers.tx[HEADER+10],state.power,4);
    put_le(&buffers.tx[HEADER+14],state.accum,2);
    buffers.tx[HEADER+16]=state.dgc;
    return send(RESULT_LEN,false);
}
#endif

int checked_run(void)
{
    buffers.before=buffers.after=CANARY;
    diagnostics.before=diagnostics.after=CANARY;
    state.before=state.after=CANARY;
    sequence(0);
    select_peer(CHECKED_RESP_ID);
    printk("MULTI role=%s id=%u rssi=%u protocol=3\n",
           CHECKED_INITIATOR ? "INIT" : "RESP", CHECKED_RESP_ID,CHECKED_RSSI);
    dw_device_init(); dw3000_hw_wakeup_pin_low(); Sleep(5);
    port_set_dw_ic_spi_slowrate();
    if (dwt_probe((struct dwt_probe_s *)&dw3000_probe_interf)!=DWT_SUCCESS) return -1;
    port_set_dw_ic_spi_fastrate();
    if (dwt_initialise(DWT_DW_INIT)!=DWT_SUCCESS || dwt_configure(&config)!=DWT_SUCCESS) return -2;
    dwt_setrxantennadelay(ANT_DELAY); dwt_settxantennadelay(ANT_DELAY);
#if !CHECKED_INITIATOR && CHECKED_RSSI
    dwt_configciadiag(DW_CIA_DIAG_LOG_ALL);
#endif
    printk("MULTI ready: ch9 DS reply_us=2500 configured_id=%u targets=%u; fixed power, Final RSSI\n",
           CHECKED_RESP_ID,CHECKED_N_RESPONDERS);
    for (;;) {
        clean(OK);
#if CHECKED_INITIATOR
        select_peer(multi_peer(state.attempts));
        peers[state.peer].attempts++;
        sequence(state.seq+1);
#endif
        state.attempts++;
        int rc=exchange();
        rc=clean(rc);
        if (rc==MEMORY_ERROR) {
            printk("MULTI FATAL memory guard/sequence corruption seq=%u\n",state.seq);
            return -3;
        }
#if CHECKED_INITIATOR
        double meters=0;
        if (rc==OK && !checked_distance(state.t,&meters)) rc=BAD_INTERVAL;
        /* Do not clip invalid ranges into a seemingly plausible value. */
        if (rc==OK && (meters < -2.0 || meters > 100.0)) rc=BAD_RANGE;
        if (rc==OK) {
            state.success++;
            peers[state.peer].success++;
            printk("MULTI seq=%u peer=%u dist_mm=%d final_rssi_mdB=%d diag=%u C=%u N=%u D=%u ok=%u/%u peer_ok=%u/%u\n",
                   state.seq,state.peer,(int)lround(meters*1000.0),state.rssi_mdB,
                   state.diag_ok,state.power,state.accum,state.dgc,state.success,state.attempts,
                   peers[state.peer].success,peers[state.peer].attempts);
        } else {
            printk("MULTI seq=%u peer=%u error=%d status=%08x ok=%u/%u peer_ok=%u/%u\n",
                   state.seq,state.peer,rc,state.status,state.success,state.attempts,
                   peers[state.peer].success,peers[state.peer].attempts);
            if (rc==BAD_RANGE || rc==BAD_INTERVAL) {
                printk("INTERVAL r1=%llu d1=%llu r2=%llu d2=%llu\n",
                       (unsigned long long)elapsed40(state.t[3],state.t[0]),
                       (unsigned long long)elapsed40(state.t[2],state.t[1]),
                       (unsigned long long)elapsed40(state.t[5],state.t[2]),
                       (unsigned long long)elapsed40(state.t[4],state.t[3]));
            }
        }
        k_msleep(150);
#else
        if (rc==OK) {
            state.success++;
            printk("MULTI served seq=%u id=%u diag=%u total=%u\n",
                   state.seq,CHECKED_RESP_ID,state.diag_ok,state.success);
        } else if (rc!=TIMEOUT && rc!=RADIO_ERROR && rc!=BAD_HEADER && rc!=BAD_LENGTH) {
            printk("MULTI responder error=%d status=%08x seq=%u\n",rc,state.status,state.seq);
        }
#endif
    }
}
