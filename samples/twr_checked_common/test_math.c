/* Host check: cc -std=c99 -Wall -Wextra test_math.c -lm -o /tmp/checked_math */
#include <assert.h>
#include <stdio.h>
#include "checked.h"

int main(void)
{
    const uint64_t delay = 159744000, tof = 107;
    const uint64_t starts[] = {0, 123456789, TS40_MASK-50,
                              TS40_MASK-delay, TS40_MASK-2*delay};
    for (unsigned a=0; a<sizeof(starts)/sizeof(starts[0]); ++a) {
        for (unsigned b=0; b<sizeof(starts)/sizeof(starts[0]); ++b) {
            uint64_t t[6] = {
                starts[a], starts[b]+tof, starts[b]+tof+delay,
                starts[a]+delay+2*tof, starts[a]+2*delay+2*tof,
                starts[b]+2*delay+3*tof,
            };
            for (unsigned i=0;i<6;++i) t[i] &= TS40_MASK;
            double meters;
            assert(checked_distance(t,&meters));
            assert(fabs(meters-tof*CHECKED_METERS_PER_TICK)<1e-6);
        }
    }
    uint64_t invalid[6]={0};
    double meters;
    assert(!checked_distance(invalid,&meters));
    uint64_t too_long[6]={0,1,2,UINT64_C(4000000000),3,4};
    assert(!checked_distance(too_long,&meters));
    uint8_t wire[5];
    const uint64_t values[]={0,1,255,256,UINT64_C(0x123456789a),TS40_MASK};
    for (unsigned i=0;i<sizeof(values)/sizeof(values[0]);++i) {
        put_le(wire,values[i],5);
        assert(get_le(wire,5)==values[i]);
    }
    assert(elapsed40(3,TS40_MASK-2)==6);
    puts("PASS: 25 independent-clock/wrap cases, invalid intervals, LE timestamps");
    return 0;
}
