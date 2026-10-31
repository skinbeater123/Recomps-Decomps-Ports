#define CKPT_CHUNK (64u * 1024u)

typedef struct {
    uint8_t  *mapped;
    size_t    size;
    uint8_t **chunks;       /* NULL = the chunk was all zero */
} CkptWindow;

static struct {
    int        taken;
    CkptWindow win[4];
    uint32_t   heap_next, reserve_next;
    int        heap_alloc_count, heap_block_count, thread_stacks_used;
    void      *heap_blocks;
    uint32_t   contig_next, contig_hwm, contig_start;
    int        contig_count;
    void      *contig_blocks;
    int        dsp_ack_count, fence_count, counter_count, frame_count;
    uint32_t   fb_va, fb_pitch, fb_height;
} s_ckpt;

static int ckpt_window(CkptWindow *w, void *mapped, size_t size)
{
    size_t n = size / CKPT_CHUNK, i, kept = 0;

    w->mapped = (uint8_t *)mapped;
    w->size = size;
    w->chunks = mapped ? (uint8_t **)calloc(n ? n : 1, sizeof(uint8_t *)) : NULL;
    if (!mapped)
        return 0;
    if (!w->chunks)
        return -1;
    for (i = 0; i < n; i++) {
        const uint64_t *p = (const uint64_t *)(w->mapped + i * CKPT_CHUNK);
        /* OHCI registers are device state, protected by the Windows MMIO
         * handler. Reset them through xbox_OhciSoftReset, never memcpy. */
        uintptr_t guest = (uintptr_t)p - (uintptr_t)g_xbox_mem_offset;
        if (guest == 0xFED00000u)
            continue;
        size_t k;
        for (k = 0; k < CKPT_CHUNK / 8 && !p[k]; k++)
            ;
        if (k == CKPT_CHUNK / 8)
            continue;
        w->chunks[i] = (uint8_t *)malloc(CKPT_CHUNK);
        if (!w->chunks[i])
            return -1;
        memcpy(w->chunks[i], p, CKPT_CHUNK);
        kept++;
    }
    return (int)kept;
}

void xbox_MemoryCheckpoint(void)
{
    int kept = 0, k, i;
    void  *maps[4] = { g_memory_base, g_contig_memory, g_nv2a_memory, g_mcpx_memory };
    size_t sizes[4] = { g_xbox_total_ram, XBOX_CONTIG_SIZE, XBOX_NV2A_SIZE, XBOX_MCPX_SIZE };

    if (s_ckpt.taken)
        return;
    for (i = 0; i < 4; i++) {
        k = ckpt_window(&s_ckpt.win[i], maps[i], sizes[i]);
        if (k < 0) {
            fprintf(stderr, "  [REBOOT] checkpoint: out of memory; soft reboot off\n");
            return;
        }
        kept += k;
    }

    AcquireSRWLockExclusive(&g_heap_lock);
    s_ckpt.heap_next = g_heap_next;
    s_ckpt.heap_alloc_count = g_heap_alloc_count;
    s_ckpt.heap_block_count = g_heap_block_count;
    s_ckpt.heap_blocks = malloc(sizeof(g_heap_blocks[0]) * (g_heap_block_count + 1));
    if (s_ckpt.heap_blocks)
        memcpy(s_ckpt.heap_blocks, g_heap_blocks, sizeof(g_heap_blocks[0]) * g_heap_block_count);
    ReleaseSRWLockExclusive(&g_heap_lock);
    AcquireSRWLockExclusive(&g_contig_lock);
    s_ckpt.contig_next = g_contig_next;
    s_ckpt.contig_hwm = g_contig_hwm;
    s_ckpt.contig_start = g_contig_start;
    s_ckpt.contig_count = g_contig_count;
    s_ckpt.contig_blocks = malloc(sizeof(g_contig_blocks[0]) * (g_contig_count + 1));
    if (s_ckpt.contig_blocks)
        memcpy(s_ckpt.contig_blocks, g_contig_blocks, sizeof(g_contig_blocks[0]) * g_contig_count);
    ReleaseSRWLockExclusive(&g_contig_lock);
    if (!s_ckpt.heap_blocks || !s_ckpt.contig_blocks) {
        fprintf(stderr, "  [REBOOT] checkpoint: out of memory; soft reboot off\n");
        return;
    }
    s_ckpt.reserve_next = g_reserve_next;
    s_ckpt.thread_stacks_used = g_thread_stacks_used;
    s_ckpt.dsp_ack_count = g_dsp_ack_count;
    s_ckpt.fence_count = g_fence_mirror_count;
    s_ckpt.counter_count = g_counter_mirror_count;
    s_ckpt.frame_count = g_frame_counter_count;
    s_ckpt.fb_va = s_fb_va;
    s_ckpt.fb_pitch = s_fb_pitch;
    s_ckpt.fb_height = s_fb_height;
    s_ckpt.taken = 1;
    fprintf(stderr, "  [REBOOT] checkpoint at the entry point: %d non-zero 64 KB chunks kept\n",
            kept);
}

int xbox_MemoryCheckpointTaken(void) { return s_ckpt.taken; }

/* Every guest window back to the checkpoint, and the allocators with it.
 * No guest code may run meanwhile: the caller holds the guest lock and has
 * seen the image's own threads end. */
int xbox_MemoryRestore(void)
{
    int i;
    size_t c;

    if (!s_ckpt.taken)
        return 0;
    for (i = 0; i < 4; i++) {
        CkptWindow *w = &s_ckpt.win[i];
        if (!w->mapped)
            continue;
        for (c = 0; c < w->size / CKPT_CHUNK; c++) {
            uint8_t *dst = w->mapped + c * CKPT_CHUNK;
            if ((uintptr_t)dst - (uintptr_t)g_xbox_mem_offset == 0xFED00000u)
                continue;
            if (w->chunks[c])
                memcpy(dst, w->chunks[c], CKPT_CHUNK);
            else
                memset(dst, 0, CKPT_CHUNK);
        }
    }

    AcquireSRWLockExclusive(&g_heap_lock);
    g_heap_next = s_ckpt.heap_next;
    g_heap_alloc_count = s_ckpt.heap_alloc_count;
    g_heap_block_count = s_ckpt.heap_block_count;
    memcpy(g_heap_blocks, s_ckpt.heap_blocks, sizeof(g_heap_blocks[0]) * g_heap_block_count);
    ReleaseSRWLockExclusive(&g_heap_lock);
    AcquireSRWLockExclusive(&g_contig_lock);
    g_contig_next = s_ckpt.contig_next;
    g_contig_hwm = s_ckpt.contig_hwm;
    g_contig_start = s_ckpt.contig_start;
    g_contig_count = s_ckpt.contig_count;
    memcpy(g_contig_blocks, s_ckpt.contig_blocks, sizeof(g_contig_blocks[0]) * g_contig_count);
    /* The published physical range goes back too. Left at the old image's
     * high-water mark, it claimed low-RAM addresses the new image uses as
     * plain VAs: Buffy's pad report buffer (0x012B223F after a level load)
     * was taken for contiguous memory, the OHCI wrote each report to
     * 0x812B223F, and the game read zeros -- no input in any level. */
    xbox_ContiguousSetPhysicalRange(g_contig_start - XBOX_CONTIG_BASE,
                                    g_contig_hwm - XBOX_CONTIG_BASE);
    ReleaseSRWLockExclusive(&g_contig_lock);
    g_reserve_next = s_ckpt.reserve_next;
    g_thread_stacks_used = s_ckpt.thread_stacks_used;
    g_dsp_ack_count = s_ckpt.dsp_ack_count;
    g_fence_mirror_count = s_ckpt.fence_count;
    g_counter_mirror_count = s_ckpt.counter_count;
    g_frame_counter_count = s_ckpt.frame_count;
    s_fb_va = s_ckpt.fb_va;
    s_fb_pitch = s_ckpt.fb_pitch;
    s_fb_height = s_ckpt.fb_height;
    s_jmp_used = 0;                     /* this thread's guest setjmp slots */
    return 1;
}
