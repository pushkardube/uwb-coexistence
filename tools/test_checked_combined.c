#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "combined_plan.h"

int main(void)
{
    unsigned seen[CHECKED_N_RESPONDERS];
    /* Count actual visits: every peer must get the entire budget at every
     * setting, including the wrap to a second cycle. Outcomes cannot affect it. */
    uint32_t attempt=0;
    for (unsigned cycle=0; cycle<2; ++cycle) {
        unsigned previous=256;
        for (unsigned level=0; level<SWEEP_LEVELS; ++level) {
            memset(seen,0,sizeof(seen));
            unsigned octet=combined_octet(level);
            if (level==0) {
                assert(octet==0x01);
            } else {
                assert((octet&3u)==2 && octet<previous);
                previous=octet;
            }
            for (unsigned byte=0; byte<4; ++byte)
                assert(((repeated_octet(octet)>>(8*byte))&255u)==octet);
            for (unsigned slot=0; slot<SWEEP_LEVEL_ATTEMPTS; ++slot,++attempt) {
                assert(combined_level(attempt)==level);
                assert(combined_cycle(attempt)==cycle);
                unsigned peer=combined_peer(attempt);
                assert(peer<CHECKED_N_RESPONDERS);
                seen[peer]++;
            }
            for (unsigned peer=0; peer<CHECKED_N_RESPONDERS; ++peer)
                assert(seen[peer]==SWEEP_ATTEMPTS);
        }
    }
    assert(combined_level(attempt)==0 && combined_cycle(attempt)==2);
    assert(combined_octet(0)==0x01 && combined_octet(1)==0xFE && combined_octet(64)==0x02);
    assert(repeated_octet(combined_octet(0))==UINT32_C(0x01010101));
    assert(RESPONDER_TX_OCTET==0xFE); /* New probe must not lower reply power. */
    assert(rssi_dgc_corrected(-81000,3,true)==-63000);
    assert(rssi_dgc_corrected(-81000,8,true)==INT32_MIN);
    assert(rssi_dgc_corrected(INT32_MIN,0,false)==INT32_MIN);
    puts("PASS: initial 01010101 probe + 64 descending settings; per-peer budgets; fixed reply power; wrap");
}
