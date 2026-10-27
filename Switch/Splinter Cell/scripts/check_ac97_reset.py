"""Check immediate AC97 reset completion through the actual MMIO write path."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/ac97-reset"
OUT.mkdir(parents=True, exist_ok=True)
path = ROOT / "private/host/xbox_memory_layout.c"
if not path.exists(): path = ROOT / "private/burnout3-sw/xboxrecomp/src/kernel/xbox_memory_layout.c"
body = re.search(r"void xbox_mmio_write\(.*?\n\}", path.read_text(encoding="utf-8"), re.S)[0]
source = r'''
#include <windows.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
static ptrdiff_t g_memory_offset;
static int g_mmio_count;
static struct { uint32_t lo,hi; void (*write)(void *,uint32_t,uint32_t,unsigned);void *opaque; } g_mmio[1];
''' + body + r'''
int main(void) {
 uint8_t *memory=VirtualAlloc(NULL,0x100000000ull,MEM_RESERVE,PAGE_NOACCESS);
 if(!memory || !VirtualAlloc(memory+0xFEC00000,4096,MEM_COMMIT,PAGE_READWRITE))return 2;
 g_memory_offset=(ptrdiff_t)memory;
 for(unsigned off=0x10B;off<0x180;off+=16) {
  xbox_mmio_write(0xFEC00000+off,0xFF,1);
  if(memory[0xFEC00000ull+off]!=0xFD)return 3;
  xbox_mmio_write(0xFEC00000+off-1,0xFFFF,2);
  if(memory[0xFEC00000ull+off]!=0xFD || memory[0xFEC00000ull+off-1]!=0xFF)return 4;
  xbox_mmio_write(0xFEC00000+off-3,0xFFFFFFFF,4);
  if(memory[0xFEC00000ull+off]!=0xFD || memory[0xFEC00000ull+off-3]!=0xFF)return 5;
 }
 xbox_mmio_write(0xFEC00108,0x02020202,4);
 if(*(uint32_t*)(memory+0xFEC00108ull)!=0x00020202)return 6;
 xbox_mmio_write(0xFEC00100,0xFFFFFFFF,4);
 if(*(uint32_t*)(memory+0xFEC00100ull)!=0xFFFFFFFF)return 7;
 puts("PASS: AC97 reset clears before the next read; byte/word/dword writes preserve other bits");
 VirtualFree(memory,0,MEM_RELEASE);return 0;
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
