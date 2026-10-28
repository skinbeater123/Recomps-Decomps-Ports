"""Check dynamic DirectSound DSP command registration without game data."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = r'''
#include <assert.h>
#include <stdint.h>
static uint32_t observed[2];
static int calls;
int xbox_ApuDspAckWord(uint32_t va) { observed[calls++] = va; return 0; }
void sc1_register_dsp_scratch(uint32_t scratch);
int main(void) {
    sc1_register_dsp_scratch(0x80010000u);
    sc1_register_dsp_scratch(0x80c70000u);
    assert(calls == 2);
    assert(observed[0] == 0x80010810u);
    assert(observed[1] == 0x80c70810u);
    return 0;
}
'''
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    tmp = Path(tmp)
    (tmp / "test.c").write_text(TEST)
    vs = Path(r"C:\Programming\VisualStudio\2026\Community")
    cmd = (f'call "{vs / "Common7/Tools/VsDevCmd.bat"}" -arch=amd64 -host_arch=amd64 >nul && '
           f'"{vs / "VC/Tools/Llvm/x64/bin/clang-cl.exe"}" /nologo /W3 '
           f'"{tmp / "test.c"}" "{ROOT / "src/dsp_commands.c"}" '
           f'/Fe:"{tmp / "test.exe"}" && "{tmp / "test.exe"}"')
    batch = tmp / "test.cmd"
    batch.write_text("@echo off\n" + cmd + "\n")
    subprocess.run(["cmd.exe", "/c", str(batch)], cwd=tmp, check=True)
print("Dynamic DSP command registration checks passed")
