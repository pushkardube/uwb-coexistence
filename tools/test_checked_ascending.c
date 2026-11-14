#include <assert.h>
#include <stdio.h>
#include "combined_plan.h"
int main(void)
{
    for (unsigned level=0;level<65;level++) {
        unsigned octet=combined_octet(level);
        assert(octet==(level ? ((level-1)<<2)|2 : 1));
        if (level) assert(octet>combined_octet(level-1));
        assert(repeated_octet(octet)==octet*UINT32_C(0x01010101));
    }
    unsigned visits[3]={0};
    for (unsigned a=0;a<7800;a++) {
        assert(combined_peer(a)==a%3);
        assert(combined_level(a)==(a/60)%65);
        assert(combined_cycle(a)==a/3900);
        visits[combined_peer(a)]++;
    }
    assert(visits[0]==2600 && visits[1]==2600 && visits[2]==2600);
    assert(combined_octet(0)==1 && combined_octet(1)==2 && combined_octet(64)==254);
    assert(RESPONDER_TX_OCTET==254);
    puts("PASS: 65 ascending gain settings; three equal peer budgets; two cycles; FE replies");
}
