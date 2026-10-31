"""Execute the original VM float-greater handler, including its shared tail."""
import re, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bodies={}
for p in (ROOT/'generated').glob('recomp_*.c'):
 s=p.read_text(encoding='utf-8')
 for a in ['0002FF90','00030006']:
  b=re.search(r'void sub_'+a+r'\(void\)\n\{.*?\n\}',s,re.S)
  if b:bodies[a]=b.group()
assert len(bodies)==2
SOURCE=r'''
#define RECOMP_GENERATED_CODE
#include "recomp_types.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
ptrdiff_t g_xbox_mem_offset;
RECOMP_TLS uint32_t g_eax,g_ecx,g_edx,g_ebx,g_esi,g_edi,g_esp,g_ebp,g_seh_ebp;
RECOMP_TLS uint32_t g_eflags=0x202;
RECOMP_TLS int g_df,g_fp_top,g_fp_cmp;
RECOMP_TLS uint16_t g_fp_cc,g_fp_control_word=0x37f;
RECOMP_TLS double g_fp_stack[8];
volatile int g_gil_contended;
void recomp_preempt(void){}
void recomp_spin_wake(void){}
void recomp_spin_yield(void){}
static void literal(void){
 uint32_t f=MEM32(g_esp+4),result=MEM32(g_esp+8),code=MEM32(f+12);
 assert(MEM8(code-1)==0x1e);MEM32(result)=MEM32(code);MEM32(f+12)=code+4;g_esp+=12;
}
#undef RECOMP_ICALL_SAFE_AT
#define RECOMP_ICALL_SAFE_AT(target,stack,site) literal()
void sub_00030006(void);
'''+ '\n'.join(bodies.values())+r'''
int main(void){
 g_xbox_mem_offset=(ptrdiff_t)calloc(1,0x400000);assert(g_xbox_mem_offset);
 float cases[][2]={{0,0},{1,0},{-1,0},{0,1},{1,1},{1,-1},{-1,-2},{-2,-1},{NAN,0},{0,NAN},{INFINITY,0},{0,INFINITY},{-0.0f,0.0f}};
 for(unsigned i=0;i<sizeof cases/sizeof cases[0];++i){
  g_esp=0x3f0000;g_ecx=0x110000;g_esi=0x12345678;
  MEM32(g_esp+4)=0x100000;MEM32(g_esp+8)=0x120000;
  MEM32(0x10000c)=0x130000;MEM32(0x100008)=g_ecx;
  MEM8(0x130000)=0x1e;MEMF(0x130001)=cases[i][0];
  MEM8(0x130005)=0x1e;MEMF(0x130006)=cases[i][1];MEM8(0x13000a)=0x16;
  sub_0002FF90();
  unsigned expected=cases[i][0]>cases[i][1],got=MEM32(0x120000);
  if(got!=expected){fprintf(stderr,"float greater: %g > %g expected %u got %u\n",cases[i][0],cases[i][1],expected,got);return 1;}
  assert(g_esp==0x3f000c && g_esi==0x12345678 && g_fp_top==0);
 }
 puts("Original VM float-greater comparison and ABI verified");return 0;
}
'''
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
 p=Path(t);(p/'test.c').write_text(SOURCE);vs=Path(r'C:/Programming/VisualStudio/2026/Community')
 cmd=f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && "{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 /I"{ROOT / "generated"}" "{p / "test.c"}" /Fe:"{p / "test.exe"}" && "{p / "test.exe"}"'
 (p/'test.cmd').write_text('@echo off\n'+cmd+'\n');subprocess.run(['cmd.exe','/c',str(p/'test.cmd')],cwd=p,check=True)
