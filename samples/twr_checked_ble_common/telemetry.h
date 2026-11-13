#ifndef CHECKED_BLE_TELEMETRY_H
#define CHECKED_BLE_TELEMETRY_H

/* Called by the initiator main thread outside the UWB exchange. */
int telemetry_init(void);
void telemetry_line(const char *format, ...);
void telemetry_wait_for_run(void);
int telemetry_take_restart(void);

#endif
