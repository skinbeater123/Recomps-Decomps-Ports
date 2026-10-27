"""Execute SC1's actual lifted CRT CPU probe; this is not an engine boot test."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "cpu-probe"
OUT.mkdir(parents=True, exist_ok=True)
body = None
for path in (ROOT / "generated").glob("recomp_*.c"):
    match = re.search(r"void sub_001AA1D0\(void\)\n\{.*?\n\}", path.read_text(encoding="utf-8"), re.S)
    if match:
        body = match[0]
        break
if body is None:
    raise SystemExit("Original CRT CPU probe was not generated")
source = r'''
#define RECOMP_GENERATED_CODE
#include "recomp_types.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
ptrdiff_t g_xbox_mem_offset;
RECOMP_TLS uint32_t g_eax,g_ecx,g_edx,g_ebx,g_esi,g_edi,g_esp,g_ebp,g_seh_ebp;
RECOMP_TLS int g_df;
volatile int g_gil_contended;
void recomp_preempt(void) {}
void recomp_unimpl(const char *what, uint32_t va) {
    fprintf(stderr,"Unimplemented in original probe: %s at %08X\n",what,va);
    exit(9);
}
''' + body + r'''
int main(void) {
    unsigned char *memory = calloc(1, 0x400000);
    assert(memory);
    g_xbox_mem_offset = (ptrdiff_t)memory;
    g_esp = 0x3F0000;
    g_ebx = 0x76543210;
    g_ebp = 0x12345678;
    MEM32(0x2D2E60) = 0xFFFFFFFFu;
    MEM32(g_esp+4) = 0;
    sub_001AA1D0();
    printf("probe: esp=%08X ebx=%08X ebp=%08X mmx=%u enabled=%u\n",
        g_esp,g_ebx,g_ebp,MEM32(0x2D2E60),MEM32(0x392D68));
    /* EBP is local in this ABI; g_ebp is a published frame hint. */
    if (g_esp != 0x3F0004 || g_ebx != 0x76543210 || MEM32(0x3EFFFC) != 0x12345678
        || MEM32(0x2D2E60) != 1 || MEM32(0x392D68) != 1) return 10;
    g_esp = 0x3F0000;
    MEM32(g_esp+4) = 0x40000;
    sub_001AA1D0();
    if (g_esp != 0x3F0004 || g_ebx != 0x76543210 || MEM32(0x392D68) != 0) return 11;
    puts("PASS: original SC1 CRT CPUID probe; stack, callee registers and MMX result preserved");
    free(memory);
    return 0;
}
'''
(OUT / "probe.c").write_text(source)
cpu = ROOT / "src" / "cpu.c"
extras = f' "{cpu}"' if cpu.exists() else ''
vs = Path(r"C:\Programming\VisualStudio\2026\Community")
command = f'''@echo off
call "{vs}/Common7/Tools/VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
"{vs}/VC/Tools/Llvm/x64/bin/clang-cl.exe" /nologo /Od /MD /I"{ROOT / 'generated'}" /Fe:probe.exe "{OUT / 'probe.c'}"{extras}
if errorlevel 1 exit /b 1
"{OUT / 'probe.exe'}"
exit /b %errorlevel%
'''
(OUT / "run.cmd").write_text(command)
subprocess.run(["cmd.exe", "/c", str(OUT / "run.cmd")], cwd=OUT, check=True)
