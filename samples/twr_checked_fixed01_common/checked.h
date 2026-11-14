#ifndef CHECKED_TWR_H
#define CHECKED_TWR_H
#include <stdint.h>
#include <stdbool.h>
#include <math.h>
#define TS40_MASK ((UINT64_C(1) << 40) - 1)
#define CHECKED_METERS_PER_TICK (299702547.0 / (499.2e6 * 128.0))
static inline uint64_t elapsed40(uint64_t end, uint64_t start)
{
    return (end - start) & TS40_MASK;
}
static inline uint64_t get_le(const uint8_t *p, unsigned n)
{
    uint64_t v = 0;
    for (unsigned i = 0; i < n; ++i) v |= (uint64_t)p[i] << (8 * i);
    return v;
}
static inline void put_le(uint8_t *p, uint64_t v, unsigned n)
{
    for (unsigned i = 0; i < n; ++i) p[i] = (uint8_t)(v >> (8 * i));
}
/* Intervals are positive, bounded to 50 ms; no mixed-radio absolute subtraction. */
static inline bool checked_distance(const uint64_t t[6], double *meters)
{
    uint64_t r1 = elapsed40(t[3], t[0]), d1 = elapsed40(t[2], t[1]);
    uint64_t r2 = elapsed40(t[5], t[2]), d2 = elapsed40(t[4], t[3]);
    const uint64_t limit = UINT64_C(3194880000);
    if (!r1 || !r2 || !d1 || !d2 || r1 > limit || r2 > limit ||
        d1 > limit || d2 > limit) return false;
    double den = (double)r1 + r2 + d1 + d2;
    *meters = (((double)r1 * r2 - (double)d1 * d2) / den) * CHECKED_METERS_PER_TICK;
    return isfinite(*meters);
}
int checked_run(void);
#endif
