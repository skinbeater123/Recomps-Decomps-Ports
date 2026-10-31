"""Run the actual lifted SC1 CRT copy against memmove, including guard bytes."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/crt-copy"
OUT.mkdir(parents=True, exist_ok=True)
body = None
for path in (ROOT / "generated").glob("recomp_*.c"):
    match = re.search(r"void sub_001B1820\(void\)\n\{.*?\n\}", path.read_text(), re.S)
    if match:
        body = match[0]
        break
if body is None:
    raise SystemExit("Original CRT copy was not generated")
# Its original jump tables remain executable-derived, local-only test data.
metadata = json.loads((ROOT / "private/sc1_analysis.json").read_text())
xbe = (ROOT / "Game Files/default.xbe").read_bytes()
image = bytearray(0x400000)
for section in metadata["sections"]:
    va, raw = int(section["virtual_addr"], 16), int(section["raw_addr"], 16)
    image[va:va+section["raw_size"]] = xbe[raw:raw+section["raw_size"]]
(OUT / "image.bin").write_bytes(image)
source = r'''
#define RECOMP_GENERATED_CODE
#include "recomp_types.h"
#include <stdio.h>
#include <stdlib.h>
ptrdiff_t g_xbox_mem_offset;
RECOMP_TLS uint32_t g_eax,g_ecx,g_edx,g_ebx,g_esi,g_edi,g_esp,g_ebp,g_seh_ebp;
RECOMP_TLS int g_df;
RECOMP_TLS uint32_t g_eflags=0x202u;
volatile int g_gil_contended;
volatile uint32_t g_icall_trace[16],g_icall_trace_idx;
volatile uint64_t g_icall_count;
void recomp_preempt(void) {}
void recomp_spin_wake(void) {}
void recomp_spin_yield(void) {}
void recomp_unimpl(const char *what,uint32_t va) { fprintf(stderr,"Unsupported %s %08X\n",what,va);exit(8); }
recomp_func_t recomp_lookup(uint32_t va) { (void)va;return NULL; }
recomp_func_t recomp_lookup_manual(uint32_t va) { (void)va;return NULL; }
recomp_func_t recomp_lookup_kernel(uint32_t va) { (void)va;return NULL; }
void recomp_icall_fail_log(uint32_t va) { fprintf(stderr,"Unexpected dispatch %08X\n",va);exit(9); }
void recomp_icall_not_code_log(uint32_t va) { recomp_icall_fail_log(va); }
''' + body + r'''
int main(void) {
    unsigned char *memory=malloc(0x400000),expected[4096];
    FILE *f=fopen("image.bin","rb");
    if(!memory || !f || fread(memory,1,0x400000,f)!=0x400000) return 2;
    fclose(f);g_xbox_mem_offset=(ptrdiff_t)memory;
    unsigned cases=0;
    for(unsigned n=0;n<=256;n++) for(unsigned sa=0;sa<4;sa++)
    for(unsigned da=0;da<4;da++) for(unsigned overlap=0;overlap<3;overlap++) {
        uint32_t src=0x100400+sa;
        uint32_t dst=overlap==0 ? 0x100800+da : overlap==1 ? src+1+da : src-1-da;
        for(unsigned i=0;i<4096;i++) memory[0x100000+i]=(unsigned char)((i*13u+6u)&0xBFu);
        memcpy(expected,memory+0x100000,4096);
        memmove(expected+dst-0x100000,expected+src-0x100000,n);
        g_eax=0;g_ecx=0;g_edx=0;g_ebx=0x12340040;
        g_esi=0x76543210;g_edi=0x12345678;g_esp=0x3F0000;g_ebp=0x3E0000;g_df=0;
        MEM32(g_esp)=0x10000;MEM32(g_esp+4)=dst;MEM32(g_esp+8)=src;MEM32(g_esp+12)=n;
        sub_001B1820();
        if(g_esp!=0x3F0004 || g_eax!=dst || g_esi!=0x76543210 || g_edi!=0x12345678 || g_ebx!=0x12340040 || g_df) {
            fprintf(stderr,"Register/stack mismatch n=%u sa=%u da=%u overlap=%u\n",n,sa,da,overlap);return 10;
        }
        if(memcmp(expected,memory+0x100000,4096)) {
            for(unsigned i=0;i<4096;i++) if(expected[i]!=memory[0x100000+i]) {
                fprintf(stderr,"Copy/guard mismatch n=%u sa=%u da=%u overlap=%u offset=%X expected=%02X actual=%02X\n",n,sa,da,overlap,i,expected[i],memory[0x100000+i]);break;
            }
            return 11;
        }
        cases++;
    }
    printf("PASS: original SC1 CRT copy; %u size/alignment/overlap cases, guard bytes and registers\n",cases);
    free(memory);return 0;
}
'''
(OUT / "probe.c").write_text(source)
vs = Path(r"C:\Programming\VisualStudio\2026\Community")
command = f'''@echo off
call "{vs}/Common7/Tools/VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
"{vs}/VC/Tools/Llvm/x64/bin/clang-cl.exe" /nologo /Od /MD /I"{ROOT / 'generated'}" /Fe:probe.exe "{OUT / 'probe.c'}"
if errorlevel 1 exit /b 1
"{OUT / 'probe.exe'}"
exit /b %errorlevel%
'''
(OUT / "run.cmd").write_text(command)
subprocess.run(["cmd.exe", "/c", str(OUT / "run.cmd")], cwd=OUT, check=True)
