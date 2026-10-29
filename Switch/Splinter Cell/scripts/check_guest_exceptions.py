"""Exercise nested guest exception continuations without retail game code."""
import subprocess
import tempfile
from pathlib import Path
from prepare_exceptions import instrument

ROOT = Path(__file__).resolve().parents[1]
fixture = '''#include <math.h>
void sub_00001000(void)
{
    uint32_t ebp = 0;
    uint32_t g_eax = recomp_leaf_ld_eax(); uint32_t g_ecx = recomp_leaf_ld_ecx(); uint32_t g_edx = recomp_leaf_ld_edx(); uint32_t g_ebx = recomp_leaf_ld_ebx(); uint32_t g_esi = recomp_leaf_ld_esi(); uint32_t g_edi = recomp_leaf_ld_edi(); uint32_t g_esp = recomp_leaf_ld_esp();
    MEM32(XBOX_FS_BASE) = esp;
    MEM32(ebp + -16) = esp;
loc_00001004: ;
    return;
}
'''
transformed, count = instrument(fixture)
assert count == 1 and 'case 0x00001004u: goto loc_00001004;' in transformed
assert 'sc1_eh_leave(&sc1_eh_frame); return;' in transformed
assert instrument(fixture.replace('MEM32(XBOX_FS_BASE) = esp;', ''))[1] == 0
TEST = r'''
#include "guest_exceptions.h"
#include <assert.h>

static int gil_depth = 1, gil_atomic;
void sc1_eh_get_gil(int *depth, int *atomic) { *depth = gil_depth; *atomic = gil_atomic; }
void sc1_eh_restore_gil(int depth, int atomic) { gil_depth = depth; gil_atomic = atomic; }

int main(void) {
    static const uint32_t outer_labels[] = {0x100, 0x104};
    static const uint32_t inner_labels[] = {0x200};
    Sc1EhFrame outer, inner;
    sc1_eh_enter(&outer, 0x1000, 0x0fc0, outer_labels, 2);
    if (!setjmp(outer.landing)) {
        sc1_eh_enter(&inner, 0x0f00, 0x0ec0, inner_labels, 1);
        assert(!sc1_eh_resume(0x100, 0x0fc0)); /* no exception dispatch */
        sc1_eh_dispatch_enter();
        assert(!sc1_eh_resume(0x999, 0x0fc0));
        assert(!sc1_eh_resume(0x100, 0x0ec0)); /* wrong guest stack */
        gil_depth = 5; gil_atomic = 2;
        sc1_eh_resume(0x104, 0x0fc0); /* abandons inner host frame */
        assert(0);
    }
    assert(sc1_eh_target() == 0x104);
    assert(gil_depth == 1 && gil_atomic == 0);
    assert(!sc1_eh_resume(0x100, 0x0fc0)); /* dispatch state restored */
    sc1_eh_leave(&outer);
    sc1_eh_dispatch_enter();
    assert(!sc1_eh_resume(0x100, 0x0fc0)); /* no stale native frame */
    sc1_eh_dispatch_leave();
    sc1_eh_enter(&outer, 0x1000, 0x0fc0, outer_labels, 2);
    sc1_eh_dispatch_enter();
    sc1_eh_reset(); /* reboot abandons the old native exception chain */
    assert(sc1_eh_target() == 0);
    sc1_eh_dispatch_enter();
    assert(!sc1_eh_resume(0x100, 0x0fc0));
    sc1_eh_dispatch_leave();
    return 0;
}
'''

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    tmp = Path(tmp)
    (tmp / "test.c").write_text(TEST)
    vs = Path(r"C:\Programming\VisualStudio\2026\Community")
    cmd = (f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && '
           f'"{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 '
           f'/I"{ROOT / "src"}" "{tmp / "test.c"}" "{ROOT / "src/guest_exceptions.c"}" '
           f'/Fe:"{tmp / "test.exe"}" && "{tmp / "test.exe"}"')
    batch = tmp / "test.cmd"
    batch.write_text("@echo off\n" + cmd + "\n")
    subprocess.run(["cmd.exe", "/c", str(batch)], cwd=tmp, check=True)
print("Guest exception frame dispatch checks passed")
