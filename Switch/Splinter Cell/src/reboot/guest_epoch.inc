volatile LONG g_guest_epoch = 1;
static RECOMP_TLS LONG t_guest_epoch;
static RECOMP_TLS jmp_buf *t_reboot_jmp;    /* set on the main guest thread */
static int s_reboot_pending;
static uint8_t s_reboot_page[0x1000];

int xbox_is_guest_thread(void) { return t_guest_epoch != 0; }
int xbox_guest_doomed(void)
{
    return t_guest_epoch && t_guest_epoch != g_guest_epoch;
}

/* The boot thread, just before the entry point: where a reboot comes back. */
void xbox_soft_reboot_arm(jmp_buf *jb)
{
    t_reboot_jmp = jb;
    t_guest_epoch = g_guest_epoch;
}

static void guest_thread_forget(void);

static void guest_doom_check(void)
{
    if (!xbox_guest_doomed())
        return;
    /* A thread at DISPATCH holds the dispatch lock, and every ISR and DPC
     * needs it. */
    if (xbox_thread_holds_dispatch())
        xbox_KfLowerIrql(PASSIVE_LEVEL);
    t_gil_nopreempt = 0;
    if (t_reboot_jmp) {
        t_gil_depth = 1;                    /* keeps the guest lock */
        sc1_eh_reset();
        longjmp(*t_reboot_jmp, 1);
    }
    t_gil_depth = 0;
    gil_unlock();
    fprintf(stderr, "  [REBOOT] guest thread %lu of the old image ends\n",
            (unsigned long)GetCurrentThreadId());
    /* Not xbox_FreeThreadStack: the heap is the new image's now. */
    guest_thread_forget();
    ExitThread(0);
}

