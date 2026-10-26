/*
 * Buffy (XDK 4432) replacement for D3D::BlockOnTime (guest 0x00596E60).
 *
 * The stock XDK fence wait spins on the GPU semaphore. With RECOMP_PB_EXEC the
 * executor only writes that semaphore if it is told where it is, so the
 * original spins forever (observed: main -> TLogo::ExecuteMovies -> ... ->
 * D3DDevice_Swap -> KickOffAndWaitForIdle -> BlockOnTime). This keeps the real
 * semaphore, as docs/technical/d3d8ltcg-device-context.md prescribes, with the
 * XDK 4432 layout read from Buffy's own BlockOnTime:
 *
 *   device      = [0x005A29A0]
 *   newest time = [device + 0x30]     (5849: +0x2C)
 *   semaphore   = [device + 0x34]     (5849: +0x30) -> GPU-completed time
 *   done(t)    <=> (newest - t) >= (newest - *semaphore)
 *   t == newest -> SetFence(0) first, which kicks off the pushbuffer holding
 *                  the release (guest 0x00596DB0, stdcall, 1 arg)
 *
 * stdcall, 2 args (time, flags): returns with esp += 12.
 */
#include <stdio.h>
#include <stdint.h>
#include <windows.h>
/* register names (esp, esi, ...) alias the guest globals, as in generated chunks */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

void nv2a_pb_set_semaphore_target(uint32_t guest_va);

#define BUFFY_D3D_DEVICE_PTR 0x005A29A0u
#define FENCE_WAIT_BOUND_MS  250

void Buffy_D3D_BlockOnTime_00596E60(void)
{
    static uint32_t told_sem;
    static unsigned timeouts;
    uint32_t t = MEM32(esp + 4);
    uint32_t dev = MEM32(BUFFY_D3D_DEVICE_PTR);

    if (dev) {
        uint32_t sem = MEM32(dev + 0x34);
        uint32_t newest = MEM32(dev + 0x30);

        if (sem && sem != told_sem) {
            nv2a_pb_set_semaphore_target(sem);
            fprintf(stderr, "[D3D] GPU semaphore at 0x%08X (device 0x%08X, XDK 4432 layout)\n", sem, dev);
            told_sem = sem;
        }
        if (sem && (uint32_t)(newest - t) < (uint32_t)(newest - MEM32(sem))) {
            DWORD start;
            if (t == newest) {
                /* SetFence(0): push the arg and a return address, as a call does. */
                uint32_t sv_esi = esi, sv_edi = edi, sv_ebx = ebx;
                PUSH32(esp, 0);
                PUSH32(esp, 0x00596E8Fu);
                SetFence_D3D_YGKK_Z_00596DB0();
                esi = sv_esi; edi = sv_edi; ebx = sv_ebx;
                newest = MEM32(dev + 0x30);
            }
            start = GetTickCount();
            while ((uint32_t)(newest - t) < (uint32_t)(newest - MEM32(sem))) {
                if (GetTickCount() - start > FENCE_WAIT_BOUND_MS) {
                    if (++timeouts <= 10 || (timeouts % 100) == 0)
                        fprintf(stderr, "[D3D] fence 0x%08X not reached in %d ms (semaphore 0x%08X, newest 0x%08X, timeout #%u)\n",
                                t, FENCE_WAIT_BOUND_MS, MEM32(sem), newest, timeouts);
                    break;
                }
                Sleep(0);
            }
        }
    }
    esp += 12;   /* ret 8 */
}
