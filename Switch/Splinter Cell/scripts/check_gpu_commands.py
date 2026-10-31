"""Check the active NV2A DMA semaphore and XDK software-method transport."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/gpu-commands"
OUT.mkdir(parents=True, exist_ok=True)
source = r'''
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
int sc1_gpu_command(uint8_t *,uint32_t,uint32_t,uint32_t);
#define W(a) (*(uint32_t*)(memory+(uint32_t)(a)))
int main(void) {
    uint8_t *memory=VirtualAlloc(NULL,0x100000000ull,MEM_RESERVE,PAGE_NOACCESS);
    if(!memory)return 2;
    if(!VirtualAlloc(memory+0xFD000000,0x800000,MEM_COMMIT,PAGE_READWRITE) ||
       !VirtualAlloc(memory+0x805D0000,0x10000,MEM_COMMIT,PAGE_READWRITE))return 2;
    W(0xFD002210)=0x03000000;
    W(0xFD700040)=8;W(0xFD700044)=0x8000011B;
    W(0xFD7011B0)=0x0002B03D;W(0xFD7011B4)=0x20;W(0xFD7011B8)=0x005DE003;
    W(0x805DE000)=3;W(0x805DE004)=0xABCDEF01;
    sc1_gpu_command(memory,0,0x1A4,8);
    sc1_gpu_command(memory,0,0x1D6C,0);
    if(!sc1_gpu_command(memory,0,0x1D70,5) || W(0x805DE000)!=5 || W(0x805DE004)!=0xABCDEF01)return 3;
    sc1_gpu_command(memory,0,0x1D6C,4);
    sc1_gpu_command(memory,0,0x1D70,6);
    if(W(0x805DE000)!=5 || W(0x805DE004)!=6)return 4;
    sc1_gpu_command(memory,0,0x1D8C,0x400094);
    sc1_gpu_command(memory,0,0x1D90,4);
    if(W(0xFD401A88)!=0x400094 || W(0xFD40186C)!=4)return 5;
    sc1_gpu_command(memory,1,0x1D90,7);
    if(W(0xFD40186C)!=4)return 6;
    puts("PASS: submitted DMA semaphore release, offset, guard word and clear-register latches");
    VirtualFree(memory,0,MEM_RELEASE);return 0;
}
'''
(OUT / "probe.c").write_text(source)
vs = Path(r"C:\Programming\VisualStudio\2026\Community")
command = f'''@echo off
call "{vs}/Common7/Tools/VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul
if errorlevel 1 exit /b 1
"{vs}/VC/Tools/Llvm/x64/bin/clang-cl.exe" /nologo /Od /MD /I"{ROOT / 'generated'}" /Fe:probe.exe "{OUT / 'probe.c'}" "{ROOT / 'src/gpu_commands.c'}"
if errorlevel 1 exit /b 1
"{OUT / 'probe.exe'}"
exit /b %errorlevel%
'''
(OUT / "run.cmd").write_text(command)
subprocess.run(["cmd.exe", "/c", str(OUT / "run.cmd")], cwd=OUT, check=True)
