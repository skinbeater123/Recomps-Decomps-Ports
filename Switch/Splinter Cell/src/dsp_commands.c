/* The existing passthrough DSP does not run the guest effects program.  Like
 * the approved upstream integration, acknowledge its DirectSound command
 * word, using the scratch pointer computed by the original guest routine. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern int xbox_ApuDspAckWord(uint32_t va);

void sc1_register_dsp_scratch(uint32_t scratch)
{
    if (!scratch || scratch > UINT32_MAX - 0x810u ||
            xbox_ApuDspAckWord(scratch + 0x810u) != 0) {
        fprintf(stderr, "[SC1] Cannot register guest DSP command scratch %08X\n", scratch);
        abort();
    }
}
