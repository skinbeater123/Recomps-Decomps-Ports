"""Check the original menu's observed texture/diffuse combiner pattern."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = r'''
#include <assert.h>
#include "software_combiner.h"
int main(void) {
    assert(sc1_menu_combiner_matches(1, 0x08040000, 0x00010c00,
        0x18140000, 0x00000c00, 0x0000000c, 0x00001c80));
    assert(!sc1_menu_combiner_matches(1, 0x08040000, 0x00000c00,
        0x18140000, 0x00000c00, 0x0000000c, 0x00001c80));
    assert(sc1_menu_combiner(0xffffffffu, 0xfe4c4c4cu) == 0xfe989898u);
    assert(sc1_menu_combiner(0x80ffffffu, 0x80333333u) == 0x40666666u);
    assert(sc1_menu_combiner(0xff808080u, 0xffffffffu) == 0xffffffffu);
    assert(sc1_menu_combiner(0x00000000u, 0xffffffffu) == 0);
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
print("Observed menu combiner checks passed")
