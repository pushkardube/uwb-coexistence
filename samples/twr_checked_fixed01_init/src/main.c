#include <zephyr/sys/printk.h>
#include "checked.h"
#include "telemetry.h"

int main(void)
{
    int rc=telemetry_init();
    if (rc) {
        printk("BLE FATAL initialization rc=%d\n",rc);
        return rc;
    }
    return checked_run();
}
