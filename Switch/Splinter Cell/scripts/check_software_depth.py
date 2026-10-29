"""Check the observed Z24S8 clear and depth comparisons."""
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEST = r'''
#include <assert.h>
#include "software_depth.h"
int main(void) {
    uint32_t p = 0x12345678u;
    p = sc1_z24s8_clear(p, 0xffffff00u, 1);
    assert(p == 0xffffff78u);
    p = sc1_z24s8_clear(p, 0x0000009au, 2);
    assert(p == 0xffffff9au);
    assert(sc1_z24s8_test_write(&p, 0x123456u, 0x203u, 1));
    assert(p == 0x1234569au);
    assert(!sc1_z24s8_test_write(&p, 0x123457u, 0x203u, 1));
    assert(p == 0x1234569au);
    assert(sc1_z24s8_test_write(&p, 0x123456u, 0x202u, 0));
    assert(!sc1_z24s8_test_write(&p, 0x123455u, 0x202u, 0));
    assert(p == 0x1234569au);
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
print('Observed Z24S8 depth checks passed')
