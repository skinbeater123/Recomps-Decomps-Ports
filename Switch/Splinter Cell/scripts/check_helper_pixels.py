from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
TEST=r'''
#include <assert.h>
#include <string.h>
#include "gl_psh.h"
int nv2a_shader_vk=1;
int main(void) {
 Nv2aPshKey k={0};char shader[65536];
 for(unsigned n=1;n<=8;n++) {
  k.control=n;k.shader_program=1|(3<<5)|(1<<10)|(1<<15);
  for(unsigned i=0;i<n;i++){k.color_icw[i]=0x08040000;k.color_ocw[i]=0x10c00;k.alpha_icw[i]=0x18140000;k.alpha_ocw[i]=0xc00;}
  k.final0=0xc;k.final1=0x1c80;
  assert(nv2a_gl_psh(&k,shader,sizeof shader)>0);
  assert(strstr(shader,"layout(push_constant) uniform FsP { vec2 u_tscale[4]; };"));
  assert(strstr(shader,"vec4 u_tscale_unused[4];"));
  assert(strstr(shader,"samplerCube t1"));
  assert(strstr(shader,"tc0 * u_tscale[0]"));
 }
 nv2a_shader_vk=0;assert(nv2a_gl_psh(&k,shader,sizeof shader)>0);
 assert(!strstr(shader,"layout(push_constant)"));
 assert(strstr(shader,"uniform vec2 u_tscale[4];"));
 return 0;
}
'''
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
 p=Path(t);(p/'test.c').write_text(TEST)
 vs=Path(r'C:\Programming\VisualStudio\2026\Community')
 cmd=f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && "{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 /I"{ROOT / "private/burnout3-sw/xboxrecomp/src/nv2a_gl"}" "{p / "test.c"}" "{ROOT / "private/host/gl_psh.c"}" /Fe:"{p / "test.exe"}" && "{p / "test.exe"}"'
 (p/'test.cmd').write_text('@echo off\n'+cmd+'\n');subprocess.run(['cmd.exe','/c',str(p/'test.cmd')],cwd=p,check=True)
print('Generated Vulkan helper-scale shaders checked for stages 1..8; GL path preserved')
