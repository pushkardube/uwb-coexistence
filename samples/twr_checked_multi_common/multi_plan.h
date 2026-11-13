#ifndef CHECKED_MULTI_PLAN_H
#define CHECKED_MULTI_PLAN_H
#include <stdint.h>
#ifndef CHECKED_N_RESPONDERS
#define CHECKED_N_RESPONDERS 2
#endif
#if CHECKED_N_RESPONDERS < 1 || CHECKED_N_RESPONDERS > 16
#error "CHECKED_N_RESPONDERS must be 1..16"
#endif
static inline uint8_t multi_peer(uint32_t zero_based_attempt)
{
    return (uint8_t)(zero_based_attempt%CHECKED_N_RESPONDERS);
}
#endif
