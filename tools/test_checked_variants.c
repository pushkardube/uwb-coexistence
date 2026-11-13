#include <assert.h>
#include <stdio.h>
#include "power_plan.h"
#include "multi_plan.h"
int main(void) {
    for (unsigned i=0;i<SWEEP_LEVELS*SWEEP_ATTEMPTS*2;++i) {
        assert(sweep_level(i)==(i/SWEEP_ATTEMPTS)%SWEEP_LEVELS);
        assert(sweep_cycle(i)==i/(SWEEP_ATTEMPTS*SWEEP_LEVELS));
    }
    for(unsigned i=0;i<SWEEP_LEVELS;++i) {
        assert((sweep_octets[i]&3)==2);
        assert((repeated_octet(sweep_octets[i])&255)==sweep_octets[i]);
        if(i)assert((sweep_octets[i]>>2)<(sweep_octets[i-1]>>2));
    }
    assert(rssi_dgc_corrected(-81000,2,true)==-69000);
    assert(rssi_dgc_corrected(-81000,8,true)==INT32_MIN);
    assert(rssi_dgc_corrected(INT32_MIN,0,false)==INT32_MIN);
    for(unsigned i=0;i<1000;++i)assert(multi_peer(i)==i%CHECKED_N_RESPONDERS);
    puts("PASS: attempt-based sweep, valid gain ladder, DGC correction, peer rotation");
}
