"""Exercise blend factors observed in the original SC1 menu overlay."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = r'''
#include <assert.h>
#include "software_blend.h"
int main(void) {
    uint32_t out = 0;
    assert(sc1_blend_add(0x20202020u, 0x40404040u, 1, 1, &out));
    assert(out == 0x60606060u);
    assert(sc1_blend_add(0xff404040u, 0xff808080u, 0x306, 0x300, &out));
    assert(out == 0xff404040u);
    assert(sc1_blend_add(0x80ff0000u, 0xff0000ffu, 0x302, 0x303, &out));
    assert(out == 0xbf80007fu);
    assert(sc1_blend_add(0xffffffffu, 0xff123456u, 0, 1, &out));
    assert(out == 0xff123456u);
    assert(!sc1_blend_add(0, 0, 0xdead, 1, &out));
    return 0;
}
'''
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    tmp = Path(tmp)
    (tmp / "test.c").write_text(TEST)
    vs = Path(r"C:\Programming\VisualStudio\2026\Community")
    cmd = (f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && '
           f'"{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 '
           f'/I"{ROOT / "src"}" "{tmp / "test.c"}" '
           f'/Fe:"{tmp / "test.exe"}" && "{tmp / "test.exe"}"')
    batch = tmp / "test.cmd"
    batch.write_text("@echo off\n" + cmd + "\n")
    subprocess.run(["cmd.exe", "/c", str(batch)], cwd=tmp, check=True)
print("Observed menu blend checks passed")
