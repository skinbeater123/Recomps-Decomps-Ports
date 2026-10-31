"""Execute the original lifted XPP CLI/read/STI window and check virtual IF."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/xpp-interrupts"
OUT.mkdir(parents=True, exist_ok=True)
body = None
for path in (ROOT / "generated").glob("recomp_*.c"):
    match = re.search(r"void sub_0025F02E\(void\)\n\{.*?\n\}", path.read_text(), re.S)
    if match:
        lines = match[0].splitlines()
        start = next(i for i, line in enumerate(lines) if '"cli"' in line or "/* cli */" in line)
        end = next(i for i, line in enumerate(lines[start:], start) if '"sti"' in line or "/* sti */" in line)
        body = "\n".join(lines[start:end+1])
        break
if body is None:
    raise SystemExit("Original XPP interrupt window was not generated")
preempt_body = re.search(r"void recomp_preempt\(void\)\n\{.*?\n\}", (ROOT / 'private/host/kernel_bridge.c').read_text(encoding='utf-8'), re.S)[0]
source = r'''
#define RECOMP_GENERATED_CODE
#include "recomp_types.h"
#include <stdio.h>
#include <stdlib.h>
ptrdiff_t g_xbox_mem_offset;
RECOMP_TLS uint32_t g_eax,g_ecx,g_edx,g_ebx,g_esi,g_edi,g_esp,g_ebp,g_seh_ebp;
RECOMP_TLS int g_df;
volatile int g_gil_contended=1;
static unsigned preempts,reads,wakes,yields;
void recomp_spin_wake(void) { wakes++; }
void recomp_spin_yield(void) { yields++;preempts++; }
static int t_gil_depth=1,t_gil_nopreempt,holds_dispatch;
int xbox_thread_holds_dispatch(void) { return holds_dispatch; }
''' + preempt_body + r'''
void recomp_unimpl(const char *what,uint32_t va) { fprintf(stderr,"Unsupported %s %08X\n",what,va);exit(8); }
uint32_t xbox_mmio_read(uint32_t va,unsigned size) {
    if(va!=0xFE80200C || size!=4 || (g_eflags&0x200)) exit(9);
    RECOMP_PREEMPT();
    if(preempts) exit(10);
    reads++;return 0x1234;
}
static void original_window(void) {
''' + body + r'''
}
int main(void) {
    unsigned char *memory=calloc(1,0x200000);
    if(!memory)return 2;
    g_xbox_mem_offset=(ptrdiff_t)memory;
    g_ecx=0x100000;g_esp=0x1F0000;g_eflags=0xAD7;
    MEM32(g_ecx+8)=0x101000;MEM16(0x101080)=5;
    original_window();
    if(g_eflags!=0xAD7 || g_eax!=5 || g_ebx!=0x1234 || reads!=1 || preempts) return 11;
    RECOMP_PREEMPT();
    if(preempts!=1)return 12;
    for(unsigned i=0;i<64;i++) RECOMP_SPIN_HINT();
    if(wakes!=4 || preempts!=2 || yields!=2) return 13;
    g_eflags &= ~0x200u;
    for(unsigned i=0;i<64;i++) RECOMP_SPIN_HINT();
    if(wakes!=8 || preempts!=2 || yields!=2) return 14;
    g_eflags |= 0x200u;t_gil_nopreempt=1;
    for(unsigned i=0;i<64;i++) RECOMP_SPIN_HINT();
    if(preempts!=2) return 15;
    t_gil_nopreempt=0;holds_dispatch=1;
    for(unsigned i=0;i<64;i++) RECOMP_SPIN_HINT();
    if(preempts!=2) return 16;
    puts("PASS: original XPP interrupt window; IF cleared/restored, other flags preserved, masked preemption deferred; polling releases guest lock only outside atomic/dispatch contexts");
    free(memory);return 0;
}
'''
(OUT / "probe.c").write_text(source)
vs = Path(r"C:\Programming\VisualStudio\2026\Community")
command = f'''@echo off
call "{vs}/Common7/Tools/VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
"{vs}/VC/Tools/Llvm/x64/bin/clang-cl.exe" /nologo /Od /MD /I"{ROOT / 'generated'}" /Fe:probe.exe "{OUT / 'probe.c'}" "{ROOT / 'src/cpu.c'}"
if errorlevel 1 exit /b 1
"{OUT / 'probe.exe'}"
exit /b %errorlevel%
'''
(OUT / "run.cmd").write_text(command)
subprocess.run(["cmd.exe", "/c", str(OUT / "run.cmd")], cwd=OUT, check=True)
