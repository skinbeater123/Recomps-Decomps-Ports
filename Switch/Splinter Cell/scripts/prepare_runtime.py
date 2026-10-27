"""Adapt authored upstream boot glue in an ignored overlay; no retail code patches."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sc1_generate", Path(__file__).with_name("generate.py"))
generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate)
UPSTREAM = generate.UPSTREAM
OUT = ROOT / "private" / "host"


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise RuntimeError(f"Upstream boot glue changed at {before!r}")
    return text.replace(before, after, 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    text = (UPSTREAM / "src/main.c").read_text(encoding="utf-8")
    text = replace_once(text, "0x001D2807u", generate.LOCK["executable"]["entry"] + "u")
    text = text.replace("sdmc:/switch/b3x", "sdmc:/switch/splintercell")
    text = text.replace("Burnout 3: Takedown", "Splinter Cell (2002)")
    text = replace_once(text, '#  define NFSU2_DEFAULT_SAVE_DIR NULL',
        '#  define NFSU2_DEFAULT_SAVE_DIR "' + (ROOT / 'private/host-data/save').as_posix() + '"')
    # Keep enough emergency stack to identify native recursion on this host.
    text = replace_once(text, '    SymSetOptions(SYMOPT_DEFERRED_LOADS | SYMOPT_UNDNAME);',
                        '    ULONG guarantee = 65536;\n    SetThreadStackGuarantee(&guarantee);\n    SymSetOptions(SYMOPT_DEFERRED_LOADS | SYMOPT_UNDNAME);')
    text = replace_once(text, '    if (ep->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION) {', '''    if (ep->ExceptionRecord->ExceptionCode == EXCEPTION_STACK_OVERFLOW) {
        void *frames[96];
        USHORT count = CaptureStackBackTrace(0, 96, frames, NULL);
        fprintf(stderr, "[CRASH] native stack overflow at RIP=%llX module=%p\\n",
                (unsigned long long)ep->ContextRecord->Rip, GetModuleHandleA(NULL));
        print_guest_state();
        for (USHORT i = 0; i < count; ++i) {
            char storage[sizeof(SYMBOL_INFO) + 256] = {0};
            SYMBOL_INFO *symbol = (SYMBOL_INFO *)storage;
            DWORD64 displacement = 0;
            symbol->SizeOfStruct = sizeof(SYMBOL_INFO); symbol->MaxNameLen = 255;
            if (SymFromAddr(GetCurrentProcess(), (DWORD64)frames[i], &displacement, symbol))
                fprintf(stderr, "  native %u %s+%llX\\n", i, symbol->Name,
                        (unsigned long long)displacement);
            else fprintf(stderr, "  native %u %p\\n", i, frames[i]);
        }
        fflush(stderr);
    }
    if (ep->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION) {''')
    # The Switch fork protects OHCI pages on Windows, but its diagnostic host
    # reporter omitted the existing device fault handler. Keep using that model.
    text = replace_once(text, '        uintptr_t fault = ep->ExceptionRecord->ExceptionInformation[1];', '''        uintptr_t fault = ep->ExceptionRecord->ExceptionInformation[1];
        extern int xbox_OhciOwnsAddress(uint32_t);
        extern int xbox_OhciHandleMmio(void *, uint32_t);
        uintptr_t guest = fault - (uintptr_t)g_xbox_mem_offset;
        if (guest <= UINT32_MAX && xbox_OhciOwnsAddress((uint32_t)guest) &&
                xbox_OhciHandleMmio(ep->ContextRecord, (uint32_t)guest))
            return EXCEPTION_CONTINUE_EXECUTION;''')
    text = replace_once(text, '    if (!xbox_MemoryLayoutInit(xbe_data, xbe_size)) {', '''    extern int sc1_validate_xbe(const void *, size_t);
    if (!sc1_validate_xbe(xbe_data, xbe_size)) {
        fatal("Wrong default.xbe: this build requires the verified European retail executable.");
        free(xbe_data);
        return 1;
    }
    if (!xbox_MemoryLayoutInit(xbe_data, xbe_size)) {''')
    text = replace_once(text, '    setenv("RECOMP_PRESENT_CROP_Y", "16", 0);',
                        '    setenv("RECOMP_PRESENT_CROP_Y", "0", 0);')
    text = replace_once(text, '''    {
        extern void b3x_options_load(void);   /* recomp_manual.c: Gameplay picture rows */
        b3x_options_load();
    }''', '''    /* No Burnout gameplay hooks or options are installed. */''')
    # A reached unsupported instruction must fail where it occurs.
    text = replace_once(text, '    setenv("RECOMP_USB", "1", 0);',
                        '    setenv("RECOMP_UNIMPL_TRAP", "1", 0);\n    setenv("RECOMP_USB", "1", 0);')
    text = replace_once(text, '    game_dir = getenv("NFSU2_GAME_DIR");', '''#ifdef _WIN32
    if (!getenv("RECOMP_WIDESCREEN")) _putenv("RECOMP_WIDESCREEN=0");
    if (!getenv("RECOMP_VK_FXAA")) _putenv("RECOMP_VK_FXAA=0");
    if (!getenv("RECOMP_VK_ANISO")) _putenv("RECOMP_VK_ANISO=1");
    if (!getenv("RECOMP_VK_LOD_BIAS")) _putenv("RECOMP_VK_LOD_BIAS=0");
#else
    setenv("RECOMP_WIDESCREEN", "0", 0);
    setenv("RECOMP_VK_FXAA", "0", 0);
    setenv("RECOMP_VK_ANISO", "1", 0);
    setenv("RECOMP_VK_LOD_BIAS", "0", 0);
#endif
    game_dir = getenv("NFSU2_GAME_DIR");''')
    # Game-created guest threads are still alive when startup returns. Terminate
    # the Horizon process instead of unloading memory beneath those threads.
    text = replace_once(text, '    switch_shutdown();\n    return rc;',
                        '    switch_shutdown();\n    _Exit(rc);')
    text = replace_once(text, '    xbox_kernel_shutdown();', '''#ifdef __SWITCH__
    switch_shutdown();
    _Exit(0);  /* guest workers may still own memory and code pages */
#endif
    xbox_kernel_shutdown();''')
    (OUT / "main.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "src/switch_nx.c").read_text(encoding="utf-8")
    text = text.replace("sdmc:/switch/b3x", "sdmc:/switch/splintercell")
    text = text.replace('/b3x_log.txt', '/logs/sc1.log').replace('/b3x_env.txt', '/sc1_env.txt')
    text = replace_once(text, '    s_t0 = armGetSystemTick();', '''    mkdir("sdmc:/switch/splintercell", 0777);
    mkdir("sdmc:/switch/splintercell/logs", 0777);
    mkdir("sdmc:/switch/splintercell/save", 0777);
    s_t0 = armGetSystemTick();''')
    (OUT / "switch_nx.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "src/switch_saltynx.c").read_text(encoding="utf-8")
    (OUT / "switch_saltynx.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/nv2a_vk/nv2a_vk.c").read_text(encoding="utf-8")
    text = text.replace("sdmc:/switch/b3x", "sdmc:/switch/splintercell")
    # Reuse BLACK's hardware-confirmed policy for this exact NVK archive.
    # Its single local heap exposes HOST_VISIBLE|COHERENT|CACHED memory types.
    before = '''            return i;
    return UINT32_MAX;
}'''
    after = '''            return i;
#ifdef __SWITCH__
    if (want == VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT && s_memprops.memoryHeapCount == 1 &&
            (s_memprops.memoryHeaps[0].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT)) {
        for (i = 0; i < s_memprops.memoryTypeCount; i++)
            if ((bits & (1u << i)) && s_memprops.memoryTypes[i].heapIndex == 0 &&
                    (s_memprops.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT))
                return i;
    }
#endif
    return UINT32_MAX;
}'''
    text = replace_once(text, before, after)
    # Same static ICD dispatch route used by BLACK's working Horizon host.
    # This SDK exports the ICD resolver rather than Vulkan loader trampolines.
    functions = sorted(set(re.findall(r'\b(vk[A-Z]\w+)\s*\(', text)))
    functions = [name for name in functions if name != "vkCreateInstance"]
    header = '''#pragma once
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <stdio.h>
extern VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vk_icdGetInstanceProcAddr(VkInstance, const char *);
static PFN_vkCreateInstance vkCreateInstance;
'''
    header += ''.join(f'static PFN_{name} {name};\n' for name in functions)
    header += '''static int sc1_vk_global(void) {
    vkCreateInstance = (PFN_vkCreateInstance)vk_icdGetInstanceProcAddr(VK_NULL_HANDLE, "vkCreateInstance");
    return vkCreateInstance != NULL;
}
static int sc1_vk_instance(VkInstance instance) {
    int ok = 1;
'''
    for name in functions:
        header += f'    {name} = (PFN_{name})vk_icdGetInstanceProcAddr(instance, "{name}");\n'
        header += f'    if (!{name}) {{ fprintf(stderr, "[VK] missing {name}\\n"); ok = 0; }}\n'
    header += '    return ok;\n}\n'
    (OUT / "sc1_vk_dispatch.h").write_text(header, encoding="utf-8")
    text = replace_once(text, '#include <vulkan/vulkan.h>', '#include "sc1_vk_dispatch.h"')
    text = replace_once(text, '    ai.pApplicationName = "nfsu2x";',
                        '    if (!sc1_vk_global()) return 0;\n    ai.pApplicationName = "Splinter Cell";')
    text = replace_once(text, '    n = 8;\n    if (vkEnumeratePhysicalDevices',
                        '    if (!sc1_vk_instance(s_inst)) return 0;\n    n = 8;\n    if (vkEnumeratePhysicalDevices')
    (OUT / "nv2a_vk.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/kernel/xbox_memory_layout.c").read_text(encoding="utf-8")
    text = replace_once(text, '''void xbox_mmio_write(uint32_t va, uint32_t val, unsigned size)
{''', '''void xbox_mmio_write(uint32_t va, uint32_t val, unsigned size)
{
    /* AC97 RR completes on the register write, before XDK's single read.
     * Some original drivers hoist that read out of the following spin loop.
     * Apply the same channel-reset model on Windows and Horizon. */
    if (va >= 0xFEC00108u && va < 0xFEC00180u) {
        for (unsigned byte = 0; byte < size; ++byte) {
            uint32_t reg = va + byte;
            if (reg >= 0xFEC0010Bu && reg < 0xFEC00180u && (reg & 15u) == 11u)
                val &= ~(2u << (byte * 8u));
        }
    }''')
    (OUT / "xbox_memory_layout.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/kernel/nv2a_pb_exec.c").read_text(encoding="utf-8")
    text = replace_once(text, '    if (method == 0x1D70 && s_sem_va) {', '''    extern int sc1_gpu_command(uint8_t *, uint32_t, uint32_t, uint32_t);
    if (sc1_gpu_command((uint8_t *)xbox_GetMemoryOffset(), subch, method, param))
        return;
    if (method == 0x1D70 && s_sem_va) {''')
    (OUT / "nv2a_pb_exec.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/kernel/kernel_bridge.c").read_text(encoding="utf-8")
    # SC1's original binned allocator indexes pool metadata by address >> 16.
    # NtAllocateVirtualMemory must return a 64 KiB-aligned new reservation and
    # report a page-rounded region size. A 4 KiB-aligned 65520-byte block loses
    # the allocation's metadata association during the next realloc/copy.
    text = replace_once(text, '    uint32_t xbox_va = xbox_HeapAlloc(size, 4096);', '''    if (size > 0xFFFFF000u) {
        g_eax = 0xC0000017u;
        return;
    }
    size = (size + 4095u) & ~4095u;
    uint32_t xbox_va = xbox_HeapAlloc(size, 65536);''')
    text = replace_once(text, 'xbox_va = xbox_ReserveAlloc(size, 4096);',
                        'xbox_va = xbox_ReserveAlloc(size, 65536);')
    text = replace_once(text, '            want /= 2;\n            xbox_va = xbox_HeapAlloc(want, 4096);',
                        '            want = ((want / 2u) + 4095u) & ~4095u;\n            xbox_va = xbox_HeapAlloc(want, 65536);')
    (OUT / "kernel_bridge.c").write_text(text, encoding="utf-8")
    for name in ("LICENSE", "xboxrecomp/NOTICE"):
        (OUT / Path(name).name).write_text((UPSTREAM / name).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Prepared pinned Switch host overlay: {OUT}")


if __name__ == "__main__":
    main()
