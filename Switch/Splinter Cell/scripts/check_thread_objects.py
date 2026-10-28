"""Exercise guest thread-object lifetime with a deterministic host stub."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = r'''
#include <stdint.h>
#include <assert.h>
#include <string.h>
typedef void *HANDLE;
typedef uint32_t DWORD;
typedef int SRWLOCK;
#define SRWLOCK_INIT 0
#define FALSE 0
#define DUPLICATE_SAME_ACCESS 0
#define STILL_ACTIVE 259
#define WAIT_OBJECT_0 0
#define WAIT_TIMEOUT 258
static uint32_t memory[1024], next_va = 16, exit_code = STILL_ACTIVE;
static int terminated, closes, frees;
#define BRIDGE_MEM32(a) memory[(a)/4]
#define XBOX_TO_NATIVE(a) ((void *)&memory[(a)/4])
static uint32_t xbox_HeapAlloc(uint32_t n, int align) { uint32_t p=next_va; (void)align; next_va+=n; return p; }
static void xbox_HeapFree(uint32_t p) { (void)p; frees++; }
static void AcquireSRWLockExclusive(SRWLOCK *p) { (void)p; }
static void ReleaseSRWLockExclusive(SRWLOCK *p) { (void)p; }
static HANDLE GetCurrentProcess(void) { return (HANDLE)1; }
static int DuplicateHandle(HANDLE a,HANDLE h,HANDLE b,HANDLE *out,int c,int d,int e) { (void)a;(void)b;(void)c;(void)d;(void)e; *out=(HANDLE)((uintptr_t)h+100); return 1; }
static int CloseHandle(HANDLE h) { (void)h; closes++; return 1; }
static DWORD GetThreadId(HANDLE h) { return (uintptr_t)h == 7 || (uintptr_t)h == 107 ? 42 : 0; }
static int GetExitCodeThread(HANDLE h, DWORD *out) { if (!GetThreadId(h)) return 0; *out=exit_code; return 1; }
static DWORD WaitForSingleObject(HANDLE h, DWORD t) { (void)h;(void)t; return terminated ? WAIT_OBJECT_0 : WAIT_TIMEOUT; }
#include "thread_objects.h"
int main(void) {
    assert(!sc1_thread_addref(0) && !sc1_thread_host(0));
    uint32_t object = sc1_thread_reference((HANDLE)7);
    assert(object && BRIDGE_MEM32(object+4)==0 && BRIDGE_MEM32(object+0x120)==STILL_ACTIVE);
    assert(sc1_thread_reference((HANDLE)7)==object);
    assert(sc1_thread_addref(object));
    assert(sc1_thread_host(object)==(HANDLE)107);
    terminated=1; exit_code=0; sc1_thread_exit(42, 0);
    assert(BRIDGE_MEM32(object+4)==1 && BRIDGE_MEM32(object+0x120)==0);
    sc1_thread_close((HANDLE)7);
    assert(sc1_thread_host(object)==(HANDLE)107 && !frees);
    assert(sc1_thread_dereference(object) && !frees);
    assert(sc1_thread_dereference(object) && !frees);
    assert(sc1_thread_dereference(object) && frees==1 && closes==1);
    assert(!sc1_thread_reference((HANDLE)99));
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
print("Guest thread-object lifetime checks passed")
