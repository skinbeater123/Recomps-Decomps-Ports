void xbox_dir_forget(HANDLE h);
void xbox_rtl_soft_reset(void);
void xbox_io_soft_reset(void);
void xbox_OhciSoftReset(void);
void mcpx_apu_soft_reset(void);
KIRQL xbox_CurrentIrql(void);       /* kernel_hal.c */

void xbox_soft_reboot_run(void)
{
    DWORD self = GetCurrentThreadId();
    int i, live = 0, waited, gil, closed = 0;
    uint32_t page;

    t_guest_epoch = g_guest_epoch;          /* this thread runs the new image */
    if (xbox_CurrentIrql() != PASSIVE_LEVEL)
        xbox_KfLowerIrql(PASSIVE_LEVEL);

    /* The old image's threads: started if they never were, resumed if the
     * image suspended them, and each ends at its next guest lock. */
    gil = xbox_gil_suspend();
    AcquireSRWLockExclusive(&g_pending_lock);
    for (i = 0; i < PENDING_START_MAX; i++)
        if (g_pending_start[i].th) {
            ResumeThread(g_pending_start[i].th);
            g_pending_start[i].th = NULL;
        }
    g_pending_count = 0;
    ReleaseSRWLockExclusive(&g_pending_lock);
    AcquireSRWLockShared(&s_guest_threads_lock);
    for (i = 0; i < GUEST_THREADS_MAX; i++)
        if (s_guest_threads[i].tid && s_guest_threads[i].tid != self
                && s_guest_threads[i].h) {
            int k;
            for (k = 0; k < 8 && ResumeThread(s_guest_threads[i].h) > 1; k++)
                ;
        }
    ReleaseSRWLockShared(&s_guest_threads_lock);
    for (waited = 0; waited < 3000; waited += 10) {
        live = 0;
        AcquireSRWLockShared(&s_guest_threads_lock);
        for (i = 0; i < GUEST_THREADS_MAX; i++)
            if (s_guest_threads[i].tid && s_guest_threads[i].tid != self)
                live++;
        ReleaseSRWLockShared(&s_guest_threads_lock);
        if (!live)
            break;
        Sleep(10);
    }
    xbox_gil_resume(gil);
    fprintf(stderr, "  [REBOOT] old image stopped after %d ms (%d thread(s) still parked)\n",
            waited, live);

    /* Nothing of the old image may be called again. */
    memset(g_connected_isr, 0, sizeof(g_connected_isr));
    g_vblank_dpc = 0;
    dpc_lock();
    g_dpc_head = g_dpc_tail = 0;
    dpc_unlock();
    if (g_timer_started) {
        EnterCriticalSection(&g_timer_lock);
        memset(g_timers, 0, sizeof(g_timers));
        LeaveCriticalSection(&g_timer_lock);
    }

    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (i = 0; i < SC1_THREAD_OBJECT_MAX; ++i) {
        if (sc1_thread_objects[i].duplicate) CloseHandle(sc1_thread_objects[i].duplicate);
        memset(&sc1_thread_objects[i], 0, sizeof(sc1_thread_objects[i]));
    }
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
    if (!xbox_MemoryRestore())
        fprintf(stderr, "  [REBOOT] no checkpoint -- guest memory NOT reset\n");
    guest_vmem_reset();

    /* Handles: files close (and finish deferred renames), the rest go. */
    for (i = 1; i < BRIDGE_HANDLE_MAX; i++)
        if (s_handle_table[i]) {
            xbox_dir_forget(s_handle_table[i]);
            CloseHandle(s_handle_table[i]);
            s_handle_table[i] = NULL;
            closed++;
        }
    memset(g_async_handles, 0, sizeof(g_async_handles));
    if (g_try_cs_guard_ready) {
        EnterCriticalSection(&g_try_cs_guard);
        memset(g_try_cs, 0, sizeof(g_try_cs));
        LeaveCriticalSection(&g_try_cs_guard);
    }
    if (g_ke_shadow_init) {
        EnterCriticalSection(&g_ke_shadow_cs);
        memset(g_ke_shadow, 0, sizeof(g_ke_shadow));
        LeaveCriticalSection(&g_ke_shadow_cs);
    }
    xbox_rtl_soft_reset();
    xbox_io_soft_reset();
    AcquireSRWLockExclusive(&s_guest_threads_lock);
    for (i = 0; i < GUEST_THREADS_MAX; i++) {
        if (s_guest_threads[i].h)
            CloseHandle(s_guest_threads[i].h);
        memset(&s_guest_threads[i], 0, sizeof(s_guest_threads[i]));
    }
    ReleaseSRWLockExclusive(&s_guest_threads_lock);
    g_thread_call_count = 0;               /* the next thread is the main one */

    mcpx_apu_soft_reset();
    xbox_OhciSoftReset();

    page = xbox_HeapAlloc(0x1000, 4096);
    if (page) {
        memcpy((uint8_t *)g_xbox_mem_offset + page, s_reboot_page, sizeof(s_reboot_page));
        BRIDGE_MEM32(XBOX_KERNEL_DATA_BASE + KDATA_LAUNCH_DATA_PAGE) = page;
    }
    s_reboot_pending = 0;

    g_eax = g_ecx = g_edx = g_ebx = g_esi = g_edi = 0;
    g_ebp = 0;
    g_seh_ebp = 0;
    fprintf(stderr, "  [REBOOT] guest reset (%d handles closed); launch data at 0x%08X;"
                    " starting the image again\n", closed, page);
    fflush(stderr);
}
