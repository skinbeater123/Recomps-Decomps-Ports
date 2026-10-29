"""Check the scene's negative wrapped coordinates and clamp behavior."""
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEST = r'''
#include <assert.h>
#include "software_texcoord.h"
int main(void) {
    assert(sc1_texcoord(-1.0f, 256, 1) == 255);
    assert(sc1_texcoord(-256.25f, 256, 1) == 255);
    assert(sc1_texcoord(256.9f, 256, 1) == 0);
    assert(sc1_texcoord(-1.0f, 256, 3) == 0);
    assert(sc1_texcoord(300.0f, 256, 3) == 255);
    return 0;
}
'''
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    tmp = Path(tmp); (tmp / 'test.c').write_text(TEST)
    vs = Path(r'C:\Programming\VisualStudio\2026\Community')
    cmd = (f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && '
           f'"{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 '
           f'/I"{ROOT / "src"}" "{tmp / "test.c"}" /Fe:"{tmp / "test.exe"}" && "{tmp / "test.exe"}"')
    (tmp / 'test.cmd').write_text('@echo off\n' + cmd + '\n')
    subprocess.run(['cmd.exe', '/c', str(tmp / 'test.cmd')], cwd=tmp, check=True)
print('Observed texture wrapping checks passed')
