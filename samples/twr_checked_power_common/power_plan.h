#ifndef CHECKED_POWER_PLAN_H
#define CHECKED_POWER_PLAN_H
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>
#ifndef SWEEP_ATTEMPTS
#define SWEEP_ATTEMPTS 20
#endif
#if SWEEP_ATTEMPTS < 1 || SWEEP_ATTEMPTS > 10000
#error "SWEEP_ATTEMPTS must be 1..10000"
#endif
/* Constant coarse=2; descending fine=63,55,47,39,31,23,15,7,0.
 * Do not interpret register differences as calibrated dB or dBm. */
static const uint8_t sweep_octets[] = {0xFE,0xDE,0xBE,0x9E,0x7E,0x5E,0x3E,0x1E,0x02};
#define SWEEP_LEVELS ((unsigned)(sizeof(sweep_octets)/sizeof(sweep_octets[0])))
static inline unsigned sweep_level(uint32_t zero_based_attempt)
{
    return (zero_based_attempt/SWEEP_ATTEMPTS)%SWEEP_LEVELS;
}
static inline uint32_t sweep_cycle(uint32_t zero_based_attempt)
{
    return zero_based_attempt/(SWEEP_ATTEMPTS*SWEEP_LEVELS);
}
static inline uint32_t repeated_octet(uint8_t value)
{
    return (uint32_t)value*UINT32_C(0x01010101);
}
static inline int32_t rssi_dgc_corrected(int32_t legacy_mdB, uint8_t dgc, bool valid)
{
    return valid && dgc<=7 ? legacy_mdB+6000*(int32_t)dgc : INT32_MIN;
}
#endif
