#ifndef CHECKED_COMBINED_PLAN_H
#define CHECKED_COMBINED_PLAN_H
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

#ifndef CHECKED_N_RESPONDERS
#define CHECKED_N_RESPONDERS 2
#endif
#ifndef SWEEP_ATTEMPTS
#define SWEEP_ATTEMPTS 10
#endif
#if CHECKED_N_RESPONDERS < 1 || CHECKED_N_RESPONDERS > 16
#error "CHECKED_N_RESPONDERS must be 1..16"
#endif
#if SWEEP_ATTEMPTS < 1 || SWEEP_ATTEMPTS > 10000
#error "SWEEP_ATTEMPTS must be 1..10000 per responder per level"
#endif

/* First probe 0x01010101 (coarse=1, fine=0), then all 64 fine-gain codes
 * at coarse=2. The initial probe is separate from the descending gain ladder.
 * Register settings are not calibrated/equally spaced dB or dBm steps. */
#define SWEEP_LEVELS 65u
#define RESPONDER_TX_OCTET 0xFEu
#define SWEEP_LEVEL_ATTEMPTS (CHECKED_N_RESPONDERS * SWEEP_ATTEMPTS)
static inline uint8_t combined_octet(unsigned level)
{
    return level==0 ? 0x01u : (uint8_t)(((64u-level)<<2)|2u);
}
static inline uint8_t combined_peer(uint32_t zero_based_attempt)
{
    return (uint8_t)(zero_based_attempt%CHECKED_N_RESPONDERS);
}
static inline unsigned combined_level(uint32_t zero_based_attempt)
{
    return (zero_based_attempt/SWEEP_LEVEL_ATTEMPTS)%SWEEP_LEVELS;
}
static inline uint32_t combined_cycle(uint32_t zero_based_attempt)
{
    return zero_based_attempt/(SWEEP_LEVEL_ATTEMPTS*SWEEP_LEVELS);
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
