/* Preserve the original launch page in the bridge; exit all Horizon threads
 * together. The next manual NRO launch consumes that original page. */
#include <switch.h>
#include <stdint.h>
#include <stdio.h>
extern void switch_shutdown(void);
void sc1_horizon_exit(uint32_t routine)
{
    fprintf(stderr, "[SC1] firmware request %u: stopping process; relaunch NRO to consume saved launch data\n", routine);
    fflush(NULL);
    switch_shutdown();
    svcExitProcess();
    for (;;) svcSleepThread(1000000000LL);
}
