/* Original XDK D3D handler synchronization and opt-in flip diagnostics. */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

/* Match the runtime's existing D3D handler protocol: a guest busy-wait can
 * service PGRAPH too, but must not interleave with the vblank DPC. */
extern uint8_t xbox_KfRaiseIrql(uint8_t);
extern void xbox_KfLowerIrql(uint8_t);
extern uint8_t xbox_CurrentIrql(void);
extern int xbox_gil_suspend(void);
extern void xbox_gil_resume(int);
extern ptrdiff_t xbox_GetMemoryOffset(void);
extern void xbox_Nv2aVblankTaken(void);
extern void nv2a_pb_trap_lock(void), nv2a_pb_trap_unlock(void), nv2a_pb_trap_taken(void);

uint8_t sc1_d3d_enter(void)
{
    uint8_t old = xbox_CurrentIrql();
    if (old < 2) {
        int depth = xbox_gil_suspend();
        old = xbox_KfRaiseIrql(2);
        xbox_gil_resume(depth);
    }
    return old;
}

void sc1_d3d_leave(uint8_t old)
{
    if (old < 2) xbox_KfLowerIrql(old);
}

uint32_t sc1_pgraph_enter(void)
{
    nv2a_pb_trap_lock();
    return *(volatile uint32_t *)((uintptr_t)xbox_GetMemoryOffset() + 0xFD400108u);
}

void sc1_pgraph_leave(uint32_t source)
{
    if (source) nv2a_pb_trap_taken();
    nv2a_pb_trap_unlock();
}

static struct { uint32_t target, current; } flip_history[32];
static unsigned flip_history_next;
static int flip_trace_reported;
void sc1_trace_flip_queue(uint32_t target, uint32_t current)
{
    if (!getenv("SC1_TRACE_FLIP_QUEUE")) return;
    flip_history[flip_history_next & 31u].target = target;
    flip_history[flip_history_next & 31u].current = current;
    ++flip_history_next;
}

void sc1_trace_flip_retire(uint32_t target, uint32_t current)
{
    if (flip_trace_reported || !getenv("SC1_TRACE_FLIP_QUEUE") ||
            (int32_t)(target - current) >= 0) return;
    flip_trace_reported = 1;
    fprintf(stderr, "[SC1 GPU] stale flip on retirement target=%08X vblank=%08X\n", target, current);
    unsigned start = flip_history_next > 32 ? flip_history_next - 32 : 0;
    for (unsigned i = start; i < flip_history_next; ++i)
        fprintf(stderr, "  enqueue target=%08X vblank=%08X\n",
                flip_history[i & 31u].target, flip_history[i & 31u].current);
    fflush(stderr);
}

