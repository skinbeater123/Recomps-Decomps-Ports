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

void sc1_trace_xid_callback(uint32_t target, uint32_t object)
{
    static int enabled = -1;
    static uint32_t last_target, last_object;
    if (enabled < 0) enabled = getenv("SC1_TRACE_GUEST_PAD") != NULL;
    if (enabled && (target != last_target || object != last_object)) {
        last_target = target; last_object = object;
        fprintf(stderr, "[SC1-PAD] original callback target=%08X object=%08X call=0025C9D3\n", target, object);
    }
}

void sc1_trace_axis_stage(uint32_t key, uint32_t value, uint32_t stage, uint32_t detail, uint32_t object)
{
    static int enabled = -1;
    static uint32_t seen;
    unsigned bit;
    if (enabled < 0) enabled = getenv("SC1_TRACE_GUEST_PAD") != NULL;
    if (!enabled || key != 0xe1u || (value & 0x7fffffffu) == 0) return;
    bit = stage == 0x85a92u ? 1u : stage == 0x85aa7u ? 2u : stage == 0x85b6fu ? 4u : 8u;
    if (seen & bit) return;
    seen |= bit;
    fprintf(stderr, "[SC1-AXIS] key=%02X value=%08X stage=%08X detail=%08X input=%08X\n", key, value, stage, detail, object);
}

void sc1_trace_axis_exec(uint32_t target, uint32_t object, uint32_t command)
{
    static int enabled = -1;
    static unsigned seen;
    if (enabled < 0) enabled = getenv("SC1_TRACE_GUEST_PAD") != NULL;
    if (!enabled || seen >= 15 || object < 0x10000u || object > 0x03fff000u ||
        command < 0x10000u || command > 0x03ffff00u) return;
    const uint8_t *mem = (const uint8_t *)xbox_GetMemoryOffset();
    uint32_t state = *(const uint32_t *)(mem + object + 0xec8u);
    uint32_t value = *(const uint32_t *)(mem + object + 0xeccu);
    if (state != 2u || (value & 0x7fffffffu) == 0) return;
    const uint16_t *text = (const uint16_t *)(mem + command);
    char ascii[80]; unsigned i;
    for (i = 0; i < sizeof ascii - 1 && text[i] && text[i] < 128; ++i) ascii[i] = (char)text[i];
    ascii[i] = 0; ++seen;
    uint32_t viewport = *(const uint32_t *)(mem + object + 0xea4u), controller = 0;
    unsigned flags = 0xffffffffu;
    if (viewport >= 0x10000u && viewport < 0x03ffffc0u) {
        controller = *(const uint32_t *)(mem + viewport + 0x34u);
        if (controller >= 0x10000u && controller < 0x03fffc00u)
            flags = mem[controller + 0x380u];
    }
    fprintf(stderr, "[SC1-AXIS-EXEC] target=%08X state=%u value=%08X viewport=%08X controller=%08X flags380=%X command=%s\n", target, state, value, viewport, controller, flags, ascii);
}
