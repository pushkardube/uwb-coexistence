#ifndef CHECKED_FIXED01_PLAN_H
#define CHECKED_FIXED01_PLAN_H
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

#ifndef CHECKED_N_RESPONDERS
#define CHECKED_N_RESPONDERS 2
#endif
#ifndef SWEEP_ATTEMPTS
#define SWEEP_ATTEMPTS 20
#endif
#if CHECKED_N_RESPONDERS != 2
#error "This fixed01 experiment requires exactly two responders"
#endif
#if SWEEP_ATTEMPTS < 1 || SWEEP_ATTEMPTS > 10000
#error "Reporting window must be 1..10000 attempts per responder"
#endif

/* One power forever. A cycle is only a reporting window, never a power change. */
#define FIXED_TX_OCTET 0x01u
#define SWEEP_LEVELS 1u
#define RESPONDER_TX_OCTET FIXED_TX_OCTET
#define SWEEP_LEVEL_ATTEMPTS (CHECKED_N_RESPONDERS * SWEEP_ATTEMPTS)
static inline uint8_t combined_octet(unsigned level)
{
    (void)level;
    return FIXED_TX_OCTET;
}
static inline uint8_t combined_peer(uint32_t attempt)
{
    return (uint8_t)(attempt % CHECKED_N_RESPONDERS);
}
static inline unsigned combined_level(uint32_t attempt)
{
    (void)attempt;
    return 0;
}
static inline uint32_t combined_cycle(uint32_t attempt)
{
    return attempt / SWEEP_LEVEL_ATTEMPTS;
}
static inline uint32_t repeated_octet(uint8_t value)
{
    return (uint32_t)value * UINT32_C(0x01010101);
}
static inline int32_t rssi_dgc_corrected(int32_t legacy_mdB, uint8_t dgc, bool valid)
{
    return valid && dgc <= 7 ? legacy_mdB + 6000 * (int32_t)dgc : INT32_MIN;
}
#endif
