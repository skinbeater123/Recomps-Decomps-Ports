"""Adapt Buffy's authored reboot lifecycle to the pinned SC1 runtime overlays."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'private/burnout3-sw/xboxrecomp/src'
OUT=ROOT/'private/host'

def replace(s,a,b):
    if s.count(a)!=1: raise RuntimeError(f'Reboot integration anchor changed: {a[:90]!r} ({s.count(a)})')
    return s.replace(a,b,1)

def prepare():
    p=OUT/'kernel_bridge.c';s=p.read_text(encoding='utf-8')
    s=replace(s,'void xbox_gil_enter(void)\n{','#include "../../src/reboot/guest_epoch.inc"\n\nvoid xbox_gil_enter(void)\n{')
    s=replace(s,'    if (t_gil_depth++ == 0)\n        gil_lock();','    if (t_gil_depth++ == 0) {\n        gil_lock();\n        guest_doom_check();\n    }')
    s=replace(s,'        t_gil_depth = depth;','        t_gil_depth = depth;\n        guest_doom_check();')
    s=replace(s,'    uint32_t tib;          /* allocated at creation: it is also the KTHREAD */','    uint32_t tib;          /* allocated at creation: it is also the KTHREAD */\n    LONG epoch;')
    s=replace(s,'    s->tib = xbox_AllocThreadTib();','    s->tib = xbox_AllocThreadTib();\n    s->epoch = g_guest_epoch;')
    anchor='    uint32_t ctx1 = s->ctx1, ctx2 = s->ctx2;'
    s=replace(s,anchor,anchor+'\n    if (s->epoch != g_guest_epoch) {\n        free(s); guest_thread_forget(); return 0;\n    }\n    t_guest_epoch = s->epoch;')
    anchor='''            /* XapiBootToDash packs its reason and two parameters into the'''
    patch='''            if (routine == 2 && BRIDGE_MEM32(page) == 0 && path[0] &&
                !strstr(path, "xboxdash") && xbox_MemoryCheckpointTaken()) {
                const char *filename = strrchr(path, '\\\\');
                filename = filename ? filename + 1 : path;
                if (strchr(filename, ';')) filename = strrchr(filename, ';') + 1;
                if (!strcasecmp(filename, "default.xbe")) {
                    memcpy(s_reboot_page, (const uint8_t *)g_xbox_mem_offset + page, sizeof(s_reboot_page));
                    s_reboot_pending = 1;
                    InterlockedIncrement(&g_guest_epoch);
                    fprintf(stderr, "[REBOOT] original same-image request, epoch %ld\\n", (long)g_guest_epoch);
                    return;
                }
            }
'''
    # _stricmp is the common runtime's portable spelling.
    patch=patch.replace('strcasecmp','_stricmp')
    s=replace(s,anchor,patch+anchor)
    s='extern int xbox_MemoryCheckpointTaken(void);\nextern int xbox_MemoryRestore(void);\nextern void guest_vmem_reset(void);\n'+s
    s+='\n#include "../../src/reboot/bridge_reset.inc"\n'
    p.write_text(s,encoding='utf-8')
    for name,inc in [('kernel_io.c','io_reset.inc'),('kernel_rtl.c','rtl_reset.inc'),('apu_core.c','apu_reset.inc')]:
        folder='apu' if name=='apu_core.c' else 'kernel'
        text=(UP/folder/name).read_text(encoding='utf-8')
        text+=f'\n#include "../../src/reboot/{inc}"\n'
        (OUT/name).write_text(text,encoding='utf-8')
    text=(UP/'kernel/guest_vmem.c').read_text(encoding='utf-8')
    text+='\nvoid guest_vmem_reset(void) { memset(s_pages, 0, sizeof(s_pages)); }\n'
    (OUT/'guest_vmem.c').write_text(text,encoding='utf-8')
    # Native Windows waits also need the same reboot cancellation that Buffy
    # implements in its POSIX wait primitives. Preserve the original deadline.
    text=(UP/'kernel/kernel_sync.c').read_text(encoding='utf-8')
    anchor='NTSTATUS __stdcall xbox_NtWaitForSingleObject('
    helpers='''extern int xbox_is_guest_thread(void);
extern int xbox_guest_doomed(void);
static DWORD sc1_reboot_wait(HANDLE handle, DWORD ms, BOOL alertable)
{
    ULONGLONG start = GetTickCount64();
    if (!xbox_is_guest_thread()) return WaitForSingleObjectEx(handle, ms, alertable);
    for (;;) {
        ULONGLONG elapsed = GetTickCount64() - start;
        DWORD left = ms == INFINITE ? 100 : (elapsed >= ms ? 0 : ms - (DWORD)elapsed);
        DWORD result = WaitForSingleObjectEx(handle, left > 100 ? 100 : left, alertable);
        if (result != WAIT_TIMEOUT || xbox_guest_doomed() ||
            (ms != INFINITE && GetTickCount64() - start >= ms)) return result;
    }
}
static DWORD sc1_reboot_wait_many(DWORD count, const HANDLE *handles, BOOL all, DWORD ms, BOOL alertable)
{
    ULONGLONG start = GetTickCount64();
    if (!xbox_is_guest_thread()) return WaitForMultipleObjectsEx(count, handles, all, ms, alertable);
    for (;;) {
        ULONGLONG elapsed = GetTickCount64() - start;
        DWORD left = ms == INFINITE ? 100 : (elapsed >= ms ? 0 : ms - (DWORD)elapsed);
        DWORD result = WaitForMultipleObjectsEx(count, handles, all, left > 100 ? 100 : left, alertable);
        if (result != WAIT_TIMEOUT || xbox_guest_doomed() ||
            (ms != INFINITE && GetTickCount64() - start >= ms)) return result;
    }
}
'''
    text=text.replace('WaitForSingleObjectEx(', 'sc1_reboot_wait(').replace('WaitForMultipleObjectsEx(', 'sc1_reboot_wait_many(')
    # Only replace API call spellings, not the xbox_ exported function names.
    text=text.replace('xbox_Ntsc1_reboot_wait(', 'xbox_NtWaitForSingleObjectEx(').replace('xbox_Ntsc1_reboot_wait_many(', 'xbox_NtWaitForMultipleObjectsEx(')
    text=replace(text,anchor,helpers+'\n'+anchor)
    (OUT/'kernel_sync.c').write_text(text,encoding='utf-8')
    p=OUT/'ohci.c';s=p.read_text(encoding='utf-8')
    s='static volatile unsigned sc1_ohci_reset_gen;\n'+s
    s=replace(s,'    unsigned waited = 0;', '    unsigned waited = 0;\n    unsigned sc1_reset_seen = sc1_ohci_reset_gen;')
    s=replace(s,'        Sleep(OHCI_TICK_MS);', '        if (sc1_reset_seen != sc1_ohci_reset_gen) {\n            sc1_reset_seen = sc1_ohci_reset_gen;\n            plugged = 0; waited = 0; held_off = 0;\n            held_off_warned = held_off_forced = 0;\n            last_status = 0; last_ack = 0; repeats = 0; hotplug_tick = 0;\n        }\n        Sleep(OHCI_TICK_MS);')
    s += '\nvoid xbox_OhciSoftReset(void) {\n    if (!s_enabled) return;\n    ohci_reset(&s_hc[0], XBOX_OHCI0_BASE, 0);\n    ohci_reset(&s_hc[1], XBOX_OHCI1_BASE, 1);\n    memset(s_dev_plugged, 0, sizeof(s_dev_plugged));\n    memset(s_reset_seq, 0, sizeof(s_reset_seq));\n    memset(s_ctrl, 0, sizeof(s_ctrl));\n    s_ctrl[0].len = s_ctrl[1].len = -1;\n    ++sc1_ohci_reset_gen;\n}\n'
    p.write_text(s,encoding='utf-8')
    p=OUT/'main.c';s=p.read_text(encoding='utf-8')
    s='#include <setjmp.h>\nextern void xbox_MemoryCheckpoint(void);\nextern void xbox_soft_reboot_arm(jmp_buf *);\nextern void xbox_soft_reboot_run(void);\nstatic jmp_buf sc1_reboot_point;\n'+s
    s=replace(s,'    xbe_entry_point();','''    xbox_MemoryCheckpoint();
    if (setjmp(sc1_reboot_point)) {
        xbox_soft_reboot_run();
        g_esp = XBOX_STACK_TOP;
    }
    xbox_soft_reboot_arm(&sc1_reboot_point);
    xbe_entry_point();''')
    p.write_text(s,encoding='utf-8')
