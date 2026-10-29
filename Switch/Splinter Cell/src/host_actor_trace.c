/* Opt-in observation of the original script Move entry, with no guest changes. */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
extern ptrdiff_t xbox_GetMemoryOffset(void);
static uint32_t observed[32];
static unsigned observed_count;
void sc1_trace_exec_move(uint32_t actor)
{
    static int enabled = -1;
    static unsigned count;
    if (enabled < 0) enabled = getenv("SC1_TRACE_EXEC_MOVE") != NULL;
    if (!enabled) return;
    if (++count > 200 && (count % 1000)) return;
    if (actor < 0x10000u || actor > 0x03fffe00u) {
        fprintf(stderr, "[ACTOR] execMove #%u t=%llu actor=%08X (unmapped)\n", count, (unsigned long long)GetTickCount64(), actor);
        return;
    }
    unsigned i;
    for (i = 0; i < observed_count && observed[i] != actor; ++i) {}
    if (i == observed_count && observed_count < 32) observed[observed_count++] = actor;
    const uint32_t *object = (const uint32_t *)((const uint8_t *)xbox_GetMemoryOffset() + actor);
    fprintf(stderr, "[ACTOR] execMove #%u t=%llu actor=%08X words", count, (unsigned long long)GetTickCount64(), actor);
    for (unsigned i = 0; i < 64; ++i) fprintf(stderr, " %08X", object[i]);
    fputc('\n', stderr);
}

void sc1_trace_actor_snapshot(void)
{
    if (!getenv("SC1_TRACE_EXEC_MOVE")) return;
    for (unsigned n = 0; n < observed_count; ++n) {
        uint32_t actor = observed[n];
        const uint32_t *object = (const uint32_t *)((const uint8_t *)xbox_GetMemoryOffset() + actor);
        fprintf(stderr, "[ACTOR-SNAPSHOT] t=%llu actor=%08X words", (unsigned long long)GetTickCount64(), actor);
        for (unsigned i = 0; i < 64; ++i) fprintf(stderr, " %08X", object[i]);
        fputc('\n', stderr);
    }
}
