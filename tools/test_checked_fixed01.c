#include <assert.h>
#include <stdio.h>
#include "combined_plan.h"

int main(void)
{
    unsigned visits[2] = {0};
    for (uint32_t attempt=0; attempt<10000; ++attempt) {
        unsigned level=combined_level(attempt);
        assert(level == 0);
        assert(repeated_octet(combined_octet(level)) == UINT32_C(0x01010101));
        assert(combined_peer(attempt) == attempt%2);
        assert(combined_cycle(attempt) == attempt/40);
        visits[combined_peer(attempt)]++;
    }
    assert(visits[0] == 5000 && visits[1] == 5000);
    assert(combined_level(UINT32_MAX) == 0);
    assert(combined_octet(UINT32_MAX) == 1);
    assert(repeated_octet(RESPONDER_TX_OCTET) == UINT32_C(0x01010101));
    assert(rssi_dgc_corrected(-90000,2,true) == -78000);
    assert(rssi_dgc_corrected(-90000,8,true) == INT32_MIN);
    puts("PASS: fixed 01010101 over 10000 attempts; two peers; reporting windows; 01010101 replies");
}
