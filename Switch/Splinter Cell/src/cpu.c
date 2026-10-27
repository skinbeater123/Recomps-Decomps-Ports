/* CPUID implementation from sp00nznet/xboxrecomp f0f8a461, MIT license.
 * Copyright xboxrecomp contributors. See docs/SC1-REUSE-SOURCES.md.
 * Guest CPU identity is a Coppermine Pentium III on every host architecture.
 */
#include "recomp_types.h"
#ifdef _MSC_VER
#include <intrin.h>
#endif
RECOMP_TLS uint32_t g_eflags = 0x202u;

/* WBINVD publishes CPU writes. Guest RAM is coherent host memory and the
 * software device models/staging uploads read that backing, so order its
 * accesses here. GPU submission/completion still belongs to the renderer. */
void sc1_guest_cache_sync(void)
{
#ifdef _MSC_VER
    _ReadWriteBarrier();
    _mm_mfence();
#else
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
#endif
}

void xbox_Cpuid(uint32_t leaf, uint32_t subleaf, uint32_t out[4])
{
    (void)subleaf;
    out[0] = out[1] = out[2] = out[3] = 0;
    if (leaf > 2) leaf = 2;
    switch (leaf) {
    case 0:
        out[0] = 2;
        out[1] = 0x756E6547u;
        out[3] = 0x49656E69u;
        out[2] = 0x6C65746Eu;
        break;
    case 1:
        out[0] = 0x683u;
        out[3] = 0x0383F9FFu;
        break;
    default:
        out[0] = 0x03020101u;
        out[3] = 0x0C040800u;
        break;
    }
}
