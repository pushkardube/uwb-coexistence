/* BLE carries post-exchange text only; this module never accesses the DW3000. */
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/printk.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/random/random.h>
#include <bluetooth/services/nus.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include "telemetry.h"

#define LINE_MAX 384
#define QUEUE_RECORDS 32
struct record { uint32_t id; uint16_t length; char data[LINE_MAX]; };
K_MSGQ_DEFINE(records, sizeof(struct record), QUEUE_RECORDS, 4);
K_MUTEX_DEFINE(connection_lock);
K_SEM_DEFINE(sent_done, 0, 1);
K_SEM_DEFINE(record_acknowledged, 0, 1);
static struct bt_conn *connection, *inflight;
static atomic_t connected_flag, notifications, running, restart_requested;
static atomic_t status_requested, link_epoch, queue_drops, records_sent, retries, bad_commands;
static atomic_t next_record_id, expected_ack;
static uint32_t boot_id;
static char command[48];
static size_t command_length;
static bool command_overflow;

static const struct bt_data advertisement[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, BT_UUID_NUS_VAL),
};
static const struct bt_data scan_response[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME, sizeof(CONFIG_BT_DEVICE_NAME)-1),
};
static void advertise(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(advertising_work, advertise);

static void advertise(struct k_work *work)
{
    ARG_UNUSED(work);
    if (atomic_get(&connected_flag)) return;
    int rc=bt_le_adv_start(BT_LE_ADV_CONN_FAST_2, advertisement, ARRAY_SIZE(advertisement),
                           scan_response, ARRAY_SIZE(scan_response));
    if (rc && rc!=-EALREADY) {
        printk("BLE advertising retry rc=%d\n",rc);
        k_work_reschedule(&advertising_work,K_SECONDS(1));
    } else {
        printk("BLE advertising name=%s; waiting for NUS client and START\n",CONFIG_BT_DEVICE_NAME);
    }
}

static void connected(struct bt_conn *conn, uint8_t error)
{
    if (error) {
        printk("BLE connection failed error=%u\n",error);
        k_work_reschedule(&advertising_work,K_MSEC(250));
        return;
    }
    k_mutex_lock(&connection_lock,K_FOREVER);
    connection=bt_conn_ref(conn);
    k_mutex_unlock(&connection_lock);
    command_length=0; command_overflow=false;
    atomic_set(&connected_flag,1);
    atomic_clear(&notifications);
    atomic_clear(&running);
    atomic_inc(&link_epoch);
    printk("BLE connected; subscribe then START or RESUME\n");
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    ARG_UNUSED(conn);
    atomic_clear(&connected_flag);
    atomic_clear(&notifications);
    atomic_clear(&running);
    atomic_inc(&link_epoch);
    k_mutex_lock(&connection_lock,K_FOREVER);
    if (connection) { bt_conn_unref(connection); connection=NULL; }
    k_mutex_unlock(&connection_lock);
    printk("BLE disconnected reason=%u; sweep pauses at next exchange boundary\n",reason);
    k_work_reschedule(&advertising_work,K_MSEC(250));
}

static void recycled(void)
{
    k_work_reschedule(&advertising_work,K_NO_WAIT);
}
BT_CONN_CB_DEFINE(connection_callbacks) = {
    .connected=connected, .disconnected=disconnected, .recycled=recycled,
};

static void send_enabled(enum bt_nus_send_status status)
{
    atomic_set(&notifications,status==BT_NUS_SEND_STATUS_ENABLED);
    if (status!=BT_NUS_SEND_STATUS_ENABLED) atomic_clear(&running);
    atomic_set(&status_requested,1);
}

static void sent(struct bt_conn *conn)
{
    k_mutex_lock(&connection_lock,K_FOREVER);
    if (inflight==conn) k_sem_give(&sent_done);
    k_mutex_unlock(&connection_lock);
}

static void execute_command(void)
{
    command[command_length]='\0';
    if (!strncmp(command,"ACK ",4)) {
        char *end;
        unsigned long boot=strtoul(command+4,&end,16);
        if (*end==' ') {
            char *last;
            unsigned long id=strtoul(end+1,&last,10);
            if (*last=='\0' && boot==boot_id && (uint32_t)id==(uint32_t)atomic_get(&expected_ack)) {
                k_sem_give(&record_acknowledged);
                return;
            }
        }
        /* Old/replayed ACKs are harmless and do not generate status floods. */
        return;
    }
    if (!strcmp(command,"START")) {
        atomic_set(&restart_requested,1);
        atomic_set(&running,1);
    } else if (!strcmp(command,"PAUSE")) {
        atomic_clear(&running);
    } else if (!strcmp(command,"RESUME")) {
        atomic_set(&running,1);
    } else if (strcmp(command,"STATUS")) {
        atomic_inc(&bad_commands);
    }
    atomic_set(&status_requested,1);
}

static void received(struct bt_conn *conn, const uint8_t *const data, uint16_t length)
{
    ARG_UNUSED(conn);
    for (unsigned i=0;i<length;++i) {
        if (data[i]=='\r') continue;
        if (data[i]=='\n') {
            if (command_overflow) {
                atomic_inc(&bad_commands);
                atomic_set(&status_requested,1);
            } else if (command_length) execute_command();
            command_length=0; command_overflow=false;
        } else if (command_length<sizeof(command)-1 && !command_overflow) {
            command[command_length++]=(char)data[i];
        } else command_overflow=true;
    }
}
static struct bt_nus_cb nus_callbacks = {
    .received=received, .sent=sent, .send_enabled=send_enabled,
};

void telemetry_line(const char *format, ...)
{
    struct record line={0};
    va_list arguments;
    va_start(arguments,format);
    int length=vsnprintk(line.data,sizeof(line.data),format,arguments);
    va_end(arguments);
    if (length<0 || length>=sizeof(line.data)) {
        atomic_inc(&queue_drops);
        printk("BLE_DROP reason=oversize dropped=%u\n",(unsigned)atomic_get(&queue_drops));
        return;
    }
    line.length=(uint16_t)length;
    line.id=(uint32_t)atomic_inc(&next_record_id)+1u;
    printk("%s",line.data);
    if (k_msgq_put(&records,&line,K_NO_WAIT)) {
        atomic_inc(&queue_drops);
        printk("BLE_DROP reason=queue_full dropped=%u\n",(unsigned)atomic_get(&queue_drops));
    }
}

static void status_if_requested(void)
{
    if (atomic_cas(&status_requested,1,0)) {
        telemetry_line("BLE_STATUS connected=%u notify=%u running=%u queue=%u dropped=%u sent=%u retries=%u bad_commands=%u\n",
            (unsigned)atomic_get(&connected_flag),(unsigned)atomic_get(&notifications),
            (unsigned)atomic_get(&running),k_msgq_num_used_get(&records),
            (unsigned)atomic_get(&queue_drops),(unsigned)atomic_get(&records_sent),
            (unsigned)atomic_get(&retries),(unsigned)atomic_get(&bad_commands));
    }
}

void telemetry_wait_for_run(void)
{
    for (;;) {
        status_if_requested();
        if (atomic_get(&connected_flag) && atomic_get(&notifications) && atomic_get(&running) &&
            k_msgq_num_free_get(&records)>=CHECKED_N_RESPONDERS+3u) return;
        k_msleep(20);
    }
}

int telemetry_take_restart(void)
{
    return atomic_cas(&restart_requested,1,0);
}

static void sender(void *a, void *b, void *c)
{
    ARG_UNUSED(a); ARG_UNUSED(b); ARG_UNUSED(c);
    struct record line;
    for (;;) {
        k_msgq_get(&records,&line,K_FOREVER);
        char wire[LINE_MAX+64];
        int header=snprintk(wire,sizeof(wire),"BLE_RECORD boot=%08x id=%u\n",boot_id,line.id);
        memcpy(wire+header,line.data,line.length);
        unsigned wire_length=(unsigned)header+line.length;
        atomic_set(&expected_ack,(atomic_val_t)line.id);
        k_sem_reset(&record_acknowledged);
        atomic_val_t epoch=atomic_get(&link_epoch);
        bool acknowledged=false;
        while (!acknowledged) {
          unsigned offset=0;
          while (offset<wire_length) {
            if (atomic_get(&link_epoch)!=epoch) {
                offset=0; epoch=atomic_get(&link_epoch);
            }
            k_mutex_lock(&connection_lock,K_FOREVER);
            struct bt_conn *conn=(connection && atomic_get(&notifications)) ? bt_conn_ref(connection) : NULL;
            k_mutex_unlock(&connection_lock);
            if (!conn) { k_msleep(20); continue; }
            unsigned chunk=MIN((unsigned)bt_nus_get_mtu(conn),wire_length-offset);
            k_sem_reset(&sent_done);
            k_mutex_lock(&connection_lock,K_FOREVER);
            inflight=conn;
            k_mutex_unlock(&connection_lock);
            int rc=chunk ? bt_nus_send(conn,(uint8_t *)&wire[offset],(uint16_t)chunk) : -ENOTCONN;
            if (!rc) {
                rc=k_sem_take(&sent_done,K_SECONDS(1));
                if (rc) {
                    /* Avoid duplicating a late chunk into the same text stream. */
                    bt_conn_disconnect(conn,BT_HCI_ERR_REMOTE_USER_TERM_CONN);
                }
            }
            k_mutex_lock(&connection_lock,K_FOREVER);
            inflight=NULL;
            k_mutex_unlock(&connection_lock);
            if (!rc && epoch==atomic_get(&link_epoch)) offset+=chunk;
            else { atomic_inc(&retries); k_msleep(20); }
            bt_conn_unref(conn);
          }
          acknowledged=k_sem_take(&record_acknowledged,K_SECONDS(1))==0;
          if (!acknowledged) atomic_inc(&retries);
        }
        atomic_inc(&records_sent);
    }
}
K_THREAD_DEFINE(sender_thread,3072,sender,NULL,NULL,NULL,7,0,0);

int telemetry_init(void)
{
    int rc=bt_enable(NULL);
    if (rc) return rc;
    rc=bt_nus_init(&nus_callbacks);
    if (rc) return rc;
    boot_id=sys_rand32_get();
    k_work_reschedule(&advertising_work,K_NO_WAIT);
    return 0;
}
