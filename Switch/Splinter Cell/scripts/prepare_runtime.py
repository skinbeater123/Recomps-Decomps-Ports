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
    text = '#include "build_identity.h"\n' + text
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
#ifdef __SWITCH__
    setenv("SC1_LAUNCH_HANDOFF", "sdmc:/switch/splintercell/save/launch-page.bin", 0);
    setenv("RECOMP_GIL_EAGER", "1", 0);
#endif
    setenv("RECOMP_WIDESCREEN", "0", 0);
    setenv("RECOMP_VK_FXAA", "0", 0);
    setenv("RECOMP_VK_ANISO", "1", 0);
    setenv("RECOMP_VK_LOD_BIAS", "0", 0);
#endif
    fprintf(stderr, "[SC1] build %s revision %s\\n", SC1_BUILD_ID, SC1_BUILD_REVISION);
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
#include <stdlib.h>
extern VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vk_icdGetInstanceProcAddr(VkInstance, const char *);
static PFN_vkCreateInstance vkCreateInstance;
'''
    header += ''.join(f'static PFN_{name} {name};\n' for name in functions)
    header += '''static int sc1_vk_global(void) {
#ifdef __SWITCH__
    /* NVK classifies Tegra X1 as non-conformant. Explicitly select the
     * documented compatibility mode unless the user supplied a value. */
    if (!getenv("NVK_I_WANT_A_BROKEN_VULKAN_DRIVER"))
        setenv("NVK_I_WANT_A_BROKEN_VULKAN_DRIVER", "1", 0);
#endif
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
    # Preserve the actual Vulkan result and count.  A failed enumeration and a
    # successful enumeration with zero devices require different investigation.
    text = replace_once(text, """    n = 8;
    if (vkEnumeratePhysicalDevices(s_inst, &n, pds) != VK_SUCCESS || !n) {
        LOGE(\"no Vulkan device\\n\");
        return 0;
    }""", """    n = 8;
    VkResult sc1_enum_result = vkEnumeratePhysicalDevices(s_inst, &n, pds);
    if (sc1_enum_result != VK_SUCCESS || !n) {
        LOGE(\"physical device enumeration result=%d count=%u\\n\", (int)sc1_enum_result, n);
        return 0;
    }""")
    (OUT / "nv2a_vk.c").write_text(text, encoding="utf-8")
    # Observe changed gamepad reports at the OHCI guest transfer boundary.
    text = (UPSTREAM / "xboxrecomp/src/usb/ohci.c").read_text(encoding="utf-8")
    text = replace_once(text, """            if (n > 0 && guest_ptr(cbp, (uint32_t)n))
                memcpy(guest_ptr(cbp, (uint32_t)n), rep, (size_t)n);""", """            if (n > 0 && guest_ptr(cbp, (uint32_t)n)) {
                memcpy(guest_ptr(cbp, (uint32_t)n), rep, (size_t)n);
#if defined(_WIN32)
                static int trace = -1;
                static int last_ly = -32768;
                if (trace < 0) trace = getenv(\"SC1_TRACE_GUEST_PAD\") != NULL;
                if (trace && n >= 20) {
                    int ly = (int16_t)((unsigned)rep[14] | ((unsigned)rep[15] << 8));
                    if (ly != last_ly) {
                        last_ly = ly;
                        fprintf(stderr, \"[SC1-PAD] td=%08X buffer=%08X bytes=%d left_y=%d\\n\", td, cbp, n, ly);
                    }
                }
#endif
            }""")
    (OUT / "ohci.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/kernel/xbox_memory_layout.c").read_text(encoding="utf-8")
    # Record the host instruction that performed the watched write; symbols
    # map it back to the original lifted function without changing guest code.
    text = replace_once(text, 'static RECOMP_TLS int s_watch_stepping;',
        'static RECOMP_TLS int s_watch_stepping;\nstatic RECOMP_TLS uintptr_t sc1_watch_host_pc;')
    text = replace_once(text, '    g_watch_last = now;\n\n    /* Return addresses',
        '    g_watch_last = now;\n#ifdef _WIN32\n    fprintf(stderr, \"[SC1-WATCH] host_rva=%llX\\n\", (unsigned long long)(sc1_watch_host_pc - (uintptr_t)GetModuleHandleW(NULL)));\n#endif\n\n    /* Return addresses')
    text = replace_once(text, '        uintptr_t fault = ep->ExceptionRecord->ExceptionInformation[1];\n\n        if (fault >= (uintptr_t)g_watch_page',
        '        uintptr_t fault = ep->ExceptionRecord->ExceptionInformation[1];\n        sc1_watch_host_pc = (uintptr_t)ep->ExceptionRecord->ExceptionAddress;\n\n        if (fault >= (uintptr_t)g_watch_page')
    # Arm the existing Windows write watch after a diagnostic identifies an object.
    text = replace_once(text, 'static int watch_arm(uint32_t va);', """static int watch_arm(uint32_t va);
#if defined(_WIN32)
int sc1_watch_address(uint32_t va) { return watch_arm(va); }
#endif""")
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
    text += '\n#include "../../src/reboot/memory_checkpoint.inc"\n'
    (OUT / "xbox_memory_layout.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/kernel/nv2a_pb_exec.c").read_text(encoding="utf-8")
    text = '#include "../../src/software_combiner.h"\n#include "../../src/software_blend.h"\n' + text
    text = '#include "../../src/software_depth.h"\n' + text
    # Experimental software-only Z24S8 support for the observed pitched scene.
    # Restrict writes to the mapped contiguous guest RAM window.
    text = replace_once(text, '    if (!(param & NV097_CLEAR_COLOR_MASK))', """#if defined(_WIN32)
    if (getenv(\"SC1_SOFTWARE_DEPTH\") && (param & 3u) && ((s_gpu.format >> 4) & 15u) == 2u) {
        uint32_t pitch = s_reg[0x20C/4] >> 16, base = s_gpu.rs.zeta_va;
        uint32_t x0 = s_gpu.clip_x, y0 = s_gpu.clip_y;
        uint32_t x1 = x0 + s_gpu.clip_w, y1 = y0 + s_gpu.clip_h;
        uint32_t hz = s_reg[0x1D98/4], vt = s_reg[0x1D9C/4];
        uint32_t rx0 = hz & 0xffffu, rx1 = (hz >> 16) + 1u;
        uint32_t ry0 = vt & 0xffffu, ry1 = (vt >> 16) + 1u;
        if (rx1 > rx0 && ry1 > ry0) {
            if (x0 < rx0) x0 = rx0; if (y0 < ry0) y0 = ry0;
            if (x1 > rx1) x1 = rx1; if (y1 > ry1) y1 = ry1;
        }
        if (x1 > x0 && y1 > y0 && pitch >= x1 * 4u && base >= 0x80000000u &&
            (uint64_t)base + (uint64_t)pitch * y1 <= 0x84000000ull &&
            !surface_write_refused(base, pitch * y1, \"clear depth\")) {
            for (uint32_t yy = y0; yy < y1; ++yy) {
                uint32_t *row = (uint32_t *)(mem + base + (size_t)yy * pitch);
                for (uint32_t xx = x0; xx < x1; ++xx)
                    row[xx] = sc1_z24s8_clear(row[xx], s_gpu.zstencil_clear, param);
            }
        }
    }
#endif
    if (!(param & NV097_CLEAR_COLOR_MASK))""")
    text = replace_once(text, '    if (bpp != 4 && bpp != 2)\n        return;\n\n    area =', """#if defined(_WIN32)
    static int sc1_depth_on = -1;
    if (sc1_depth_on < 0) sc1_depth_on = getenv(\"SC1_SOFTWARE_DEPTH\") != NULL;
#endif
    if (bpp != 4 && bpp != 2)
        return;

    area =""")
    text = replace_once(text, '            if (textured) {\n                /* Barycentric, straight', """#if defined(_WIN32)
            if (sc1_depth_on && s_gpu.rs.depth_test_enable &&
                ((s_gpu.format >> 4) & 15u) == 2u) {
                uint32_t pitch = s_reg[0x20C/4] >> 16, base = s_gpu.rs.zeta_va;
                if (base >= 0x80000000u && pitch >= (uint32_t)(x + 1) * 4u &&
                    (uint64_t)base + (uint64_t)pitch * ((uint32_t)y + 1u) <= 0x84000000ull &&
                    !surface_write_refused(base, pitch * ((uint32_t)y + 1u), \"write depth\")) {
                    float zf = (w1 * a[2] + w2 * b[2] + w0 * c[2]) / area;
                    if (!(zf >= 0.0f)) zf = 0.0f;
                    if (zf > 16777215.0f) zf = 16777215.0f;
                    uint32_t *z = (uint32_t *)(mem + base + (size_t)y * pitch) + x;
                    if (!sc1_z24s8_test_write(z, (uint32_t)(zf + 0.5f), s_gpu.rs.depth_func, s_gpu.rs.depth_write)) continue;
                }
            }
#endif
            if (textured) {
                /* Barycentric, straight""")
    text = replace_once(text, '            float a[2], b[2], c[2];', '            float a[4] = {0}, b[4] = {0}, c[4] = {0};')
    text = '#include "../../src/software_texcoord.h"\n' + text
    text = replace_once(text, '    area = (b[0] - a[0]) * (c[1] - a[1])', """#if defined(_WIN32)
    static int sc1_wrap_on = -1;
    if (sc1_wrap_on < 0) sc1_wrap_on = getenv(\"SC1_SOFTWARE_UV_WRAP\") != NULL;
#endif
    area = (b[0] - a[0]) * (c[1] - a[1])""")
    text = replace_once(text, """                if (su < 0.0f) su = 0.0f;
                if (sv < 0.0f) sv = 0.0f;
                if (sample_texture(&s_gpu.tex, (uint32_t)su, (uint32_t)sv, &texel)) {""", """                uint32_t iu, iv;
#if defined(_WIN32)
                if (sc1_wrap_on) {
                    iu = sc1_texcoord(su, s_gpu.tex.width, s_gpu.tex.addr_u);
                    iv = sc1_texcoord(sv, s_gpu.tex.height, s_gpu.tex.addr_v);
                } else
#endif
                {
                    if (su < 0.0f) su = 0.0f;
                    if (sv < 0.0f) sv = 0.0f;
                    iu = (uint32_t)su; iv = (uint32_t)sv;
                }
                if (sample_texture(&s_gpu.tex, iu, iv, &texel)) {""")
    # Bounded evidence for the actual depth format, pitch and clear flags.
    text = replace_once(text, 'static void clear_surface(uint32_t param)\n{', """static void clear_surface(uint32_t param)
{
#if defined(_WIN32)
    static int sc1_depth_trace = -1;
    if (sc1_depth_trace < 0) sc1_depth_trace = getenv(\"SC1_TRACE_DEPTH_STATE\") != NULL;
    if (sc1_depth_trace) {
        static unsigned count;
        if (count++ < 40)
            fprintf(stderr, \"[DEPTH] clear flags=%08X format=%08X pitch=%08X zeta=%08X value=%08X clip=%u,%u %ux%u\\n\", param, s_gpu.format, s_reg[0x20C/4], s_gpu.rs.zeta_va, s_gpu.zstencil_clear, s_gpu.clip_x, s_gpu.clip_y, s_gpu.clip_w, s_gpu.clip_h);
    }
#endif""")
    text = replace_once(text, '    int textured = uv && s_gpu.tex.valid;', """#if defined(_WIN32)
    static int sc1_depth_trace = -1;
    if (sc1_depth_trace < 0) sc1_depth_trace = getenv(\"SC1_TRACE_DEPTH_STATE\") != NULL;
    if (sc1_depth_trace) {
        static uint32_t last_format, last_pitch, last_zeta, last_func, last_enable;
        if (s_gpu.format != last_format || s_reg[0x20C/4] != last_pitch || s_gpu.rs.zeta_va != last_zeta || s_gpu.rs.depth_func != last_func || s_gpu.rs.depth_test_enable != last_enable) {
            last_format = s_gpu.format; last_pitch = s_reg[0x20C/4]; last_zeta = s_gpu.rs.zeta_va; last_func = s_gpu.rs.depth_func; last_enable = s_gpu.rs.depth_test_enable;
            fprintf(stderr, \"[DEPTH] draw format=%08X pitch=%08X zeta=%08X enable=%u func=%X write=%u\\n\", last_format, last_pitch, last_zeta, last_enable, last_func, s_gpu.rs.depth_write);
        }
    }
#endif
    int textured = uv && s_gpu.tex.valid;""")
    # Compare the guest CRTC scanout with the last render target; the latter
    # may be a small offscreen texture rather than the displayed frame.
    text = replace_once(text, '    dump_surface_bmp();\n\n    /* Drawn and skipped separately:',
        '    dump_surface_bmp();\n#if defined(_WIN32)\n    extern void sc1_dump_scanout(void);\n    sc1_dump_scanout();\n#endif\n\n    /* Drawn and skipped separately:')
    text = replace_once(text, '        xbox_Nv2aFrameCounterFlip();',
        '        xbox_Nv2aFrameCounterFlip();\n#if defined(_WIN32)\n        extern void sc1_dump_scanout(void);\n        extern void sc1_poll_watch(void);\n        sc1_dump_scanout();\n        sc1_poll_watch();\n#endif')
    text = replace_once(text, '    int textured = uv && s_gpu.tex.valid;', '''    int textured = uv && s_gpu.tex.valid;
    int menu_combiner = sc1_menu_combiner_matches(s_reg[0x1E60/4], s_reg[0x0AC0/4],
        s_reg[0x1E40/4], s_reg[0x0260/4], s_reg[0x0AA0/4], s_reg[0x0288/4], s_reg[0x028C/4]);''')
    text = replace_once(text, '                    put_pixel(mem, bpp, x, y, texel);',
                        '                    put_pixel(mem, bpp, x, y, menu_combiner ? sc1_menu_combiner(texel, argb) : texel);')
    blend_start = text.index('    /* src*srcAlpha + dst*(1-srcAlpha), and only that pair.')
    blend_end = text.index('\n    if (bpp == 4) {', blend_start)
    text = text[:blend_start] + '''    /* Apply the observed NV2A ADD blend factors to all four channels. */
    if (s_gpu.blend_enable && s_gpu.rs.blend_eq == 0x8006u) {
        uint32_t dst, blended;
        if (bpp == 4) dst = ((const uint32_t *)row)[x];
        else {
            uint32_t t = ((const uint16_t *)row)[x];
            dst = 0xff000000u | ((t & 0xf800u) << 8) |
                  ((t & 0x07e0u) << 5) | ((t & 0x001fu) << 3);
        }
        if (sc1_blend_add(argb, dst, s_gpu.blend_sfactor, s_gpu.blend_dfactor, &blended))
            argb = blended;
    }
''' + text[blend_end:]
    text = replace_once(text, '    if (method == 0x1D70 && s_sem_va) {', '''    extern int sc1_gpu_command(uint8_t *, uint32_t, uint32_t, uint32_t);
    if (sc1_gpu_command((uint8_t *)xbox_GetMemoryOffset(), subch, method, param))
        return;
    if (method == 0x1D70 && s_sem_va) {''')
    (OUT / "nv2a_pb_exec.c").write_text(text, encoding="utf-8")
    text = (UPSTREAM / "xboxrecomp/src/kernel/kernel_bridge.c").read_text(encoding="utf-8")
    text = '#include "../../src/guest_exceptions.h"\n' + text
    # The diagnostic supervisor restarts the same image after an Xbox quick
    # reboot, carrying the original 4 KiB launch page between processes.
    text = replace_once(text, '        if (cmdline && *cmdline) {', '''#if defined(_WIN32) || defined(__SWITCH__)
        const char *handoff = getenv("SC1_LAUNCH_HANDOFF");
        FILE *launch_file = handoff ? fopen(handoff, "rb") : NULL;
        if (launch_file) {
            uint8_t launch_page[4096];
            size_t n = fread(launch_page, 1, sizeof launch_page, launch_file);
            int extra = fgetc(launch_file);
            fclose(launch_file);
            if (n != sizeof launch_page || extra != EOF || remove(handoff) != 0) {
                fprintf(stderr, "[SC1] invalid launch handoff\\n");
                exit(1);
            }
            uint32_t page = xbox_HeapAlloc(4096, 4096);
            if (!page) { fprintf(stderr, "[SC1] launch page allocation failed\\n"); exit(1); }
            for (size_t i = 0; i < sizeof launch_page; ++i)
                BRIDGE_MEM8(page + (uint32_t)i) = launch_page[i];
            BRIDGE_MEM32(XBOX_KERNEL_DATA_BASE + KDATA_LAUNCH_DATA_PAGE) = page;
            fprintf(stderr, "[SC1] restored original launch page at %08X\\n", page);
        } else
#endif
        if (cmdline && *cmdline) {''')
    text = replace_once(text, '    xbox_HalReturnToFirmware(routine);', '''#if defined(_WIN32) || defined(__SWITCH__)
    {
        const char *handoff = getenv("SC1_LAUNCH_HANDOFF");
        uint32_t page = BRIDGE_MEM32(XBOX_KERNEL_DATA_BASE + KDATA_LAUNCH_DATA_PAGE);
        if (handoff && routine == 2 && page && BRIDGE_MEM32(page) == 0) {
            char path[64];
            size_t i;
            for (i = 0; i + 1 < sizeof path && BRIDGE_MEM8(page + 8 + i); ++i)
                path[i] = (char)BRIDGE_MEM8(page + 8 + i);
            path[i] = 0;
            if (_stricmp(path, "\\\\Device\\\\CdRom0;default.xbe") == 0) {
                uint8_t launch_page[4096];
                for (i = 0; i < sizeof launch_page; ++i)
                    launch_page[i] = BRIDGE_MEM8(page + (uint32_t)i);
                FILE *f = fopen(handoff, "wb");
                size_t written = f ? fwrite(launch_page, 1, sizeof launch_page, f) : 0;
                int close_result = f ? fclose(f) : -1;
                if (written != sizeof launch_page || close_result != 0) {
                    remove(handoff);
                    fprintf(stderr, "[SC1] launch handoff write failed\\n");
                    exit(1);
                }
                fprintf(stderr, "[SC1] saved original launch page for same-image reboot\\n");
            }
        }
    }
#endif
#ifdef __SWITCH__
    extern void sc1_horizon_exit(uint32_t);
    sc1_horizon_exit(routine);
#endif
    xbox_HalReturnToFirmware(routine);''')
    text = replace_once(text, 'static SRWLOCK s_guest_threads_lock = SRWLOCK_INIT;',
                        'static SRWLOCK s_guest_threads_lock = SRWLOCK_INIT;\n#include "../../src/thread_objects.h"')
    text = replace_once(text, '''    ReleaseSRWLockShared(&s_guest_threads_lock);
    return h;
}

/* KTHREAD of the thread behind a host handle''', '''    ReleaseSRWLockShared(&s_guest_threads_lock);
    if (!h) h = sc1_thread_host(kthread);
    return h;
}

/* KTHREAD of the thread behind a host handle''')
    text = replace_once(text, '''    guest_thread_forget();
    xbox_FreeThreadStack(g_thread_stack_top);''', '''    sc1_thread_exit(GetCurrentThreadId(), 0);
    guest_thread_forget();
    xbox_FreeThreadStack(g_thread_stack_top);''')
    text = replace_once(text, '''        guest_thread_forget();
        xbox_FreeThreadStack(g_thread_stack_top);''', '''        sc1_thread_exit(GetCurrentThreadId(), exit_status);
        guest_thread_forget();
        xbox_FreeThreadStack(g_thread_stack_top);''')
    text = replace_once(text, '''            HANDLE h = s_handle_table[i];
            s_handle_table[i] = NULL;''', '''            HANDLE h = s_handle_table[i];
            sc1_thread_close(h);
            s_handle_table[i] = NULL;''')
    start = text.index('static void bridge_ObReferenceObjectByHandle(void)')
    end = text.index('/* ── RtlRaiseException', start)
    text = text[:start] + '''static void bridge_ObReferenceObjectByHandle(void)
{
    uint32_t handle = STACK_ARG(0), object_ptr = STACK_ARG(2), object;
    if (handle == 0xFFFFFFFEu) object = guest_thread_self();
    else object = sc1_thread_reference(bridge_resolve_handle(handle));
    if (object_ptr) BRIDGE_MEM32(object_ptr) = object;
    g_eax = object ? 0 : 0xC0000008u; /* STATUS_INVALID_HANDLE */
}

''' + text[end:]
    text = replace_once(text, '    xbox_ObfDereferenceObject(XBOX_TO_NATIVE(g_ecx));',
                        '    if (!sc1_thread_dereference(g_ecx)) xbox_ObfDereferenceObject(XBOX_TO_NATIVE(g_ecx));')
    text = replace_once(text, '    xbox_ObfReferenceObject(XBOX_TO_NATIVE(g_ecx));',
                        '    if (!sc1_thread_addref(g_ecx)) xbox_ObfReferenceObject(XBOX_TO_NATIVE(g_ecx));')
    text = replace_once(text, '#define GUEST_CALL(f) do {', '''void sc1_eh_get_gil(int *depth, int *atomic) {
    *depth = t_gil_depth; *atomic = t_gil_nopreempt;
}
void sc1_eh_restore_gil(int depth, int atomic) {
    if ((depth > 0) != (t_gil_depth > 0)) {
        fprintf(stderr, "[SC1] Exception crossed guest lock ownership\\n");
        abort();
    }
    t_gil_depth = depth; t_gil_nopreempt = atomic;
}
#define GUEST_CALL(f) do {''')
    start = text.index('static void bridge_RtlRaiseException(void)')
    end = text.index('/* ── MmMapIoSpace', start)
    text = text[:start] + '''static void bridge_RtlRaiseException(void)
{
    uint32_t record = STACK_ARG(0);
    uint32_t code = record ? BRIDGE_MEM32(record) : 0;
    if (code >= 0xC0000090u && code <= 0xC0000096u) {
        _clearfp(); g_eax = 0; return;
    }
    if (code != 0xE06D7363u) {
        fprintf(stderr, "[SC1] Unsupported guest exception %08X at record %08X\\n", code, record);
        abort();
    }
    uint32_t saved_sp = g_esp, saved_ebp = g_ebp, saved_seh_ebp = g_seh_ebp;
    uint32_t saved_eax = g_eax, saved_ecx = g_ecx, saved_edx = g_edx;
    uint32_t saved_ebx = g_ebx, saved_esi = g_esi, saved_edi = g_edi;
    uint32_t context = (saved_sp - 0x300u) & ~15u;
    uint32_t frame = BRIDGE_MEM32(XBOX_FS_BASE), previous = 0;
    memset(XBOX_TO_NATIVE(context), 0, 0x2cc);
    BRIDGE_MEM32(context + 0x9c) = saved_edi; BRIDGE_MEM32(context + 0xa0) = saved_esi;
    BRIDGE_MEM32(context + 0xa4) = saved_ebx; BRIDGE_MEM32(context + 0xa8) = saved_edx;
    BRIDGE_MEM32(context + 0xac) = saved_ecx; BRIDGE_MEM32(context + 0xb0) = saved_eax;
    BRIDGE_MEM32(context + 0xb4) = saved_ebp; BRIDGE_MEM32(context + 0xb8) = BRIDGE_MEM32(record + 12);
    BRIDGE_MEM32(context + 0xc4) = saved_sp;
    sc1_eh_dispatch_enter();
    for (int i = 0; i < 64 && frame != 0xffffffffu && frame; ++i) {
        if ((frame & 3u) || frame >= 0x03fffff0u || (previous && frame <= previous)) break;
        uint32_t next = BRIDGE_MEM32(frame), handler_va = BRIDGE_MEM32(frame + 4);
        recomp_func_t handler = recomp_lookup(handler_va);
        if (!handler) handler = recomp_lookup_manual(handler_va);
        if (!handler) handler = recomp_lookup_kernel(handler_va);
        if (!handler) {
            fprintf(stderr, "[SC1] Missing guest exception handler %08X at frame %08X\\n", handler_va, frame);
            abort();
        }
        g_esp = context - 20;
        BRIDGE_MEM32(g_esp) = 0; BRIDGE_MEM32(g_esp + 4) = record;
        BRIDGE_MEM32(g_esp + 8) = frame; BRIDGE_MEM32(g_esp + 12) = context;
        BRIDGE_MEM32(g_esp + 16) = 0;
        GUEST_CALL(handler);
        uint32_t disposition = g_eax;
        g_esp = saved_sp; g_ebp = saved_ebp; g_seh_ebp = saved_seh_ebp;
        g_eax = saved_eax; g_ecx = saved_ecx; g_edx = saved_edx;
        g_ebx = saved_ebx; g_esi = saved_esi; g_edi = saved_edi;
        if (disposition != 1u) {
            fprintf(stderr, "[SC1] Unsupported guest exception disposition %08X\\n", disposition);
            abort();
        }
        previous = frame; frame = next;
    }
    sc1_eh_dispatch_leave();
    fprintf(stderr, "[SC1] Unhandled guest C++ exception at record %08X\\n", record);
    abort();
}

''' + text[end:]
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
    from prepare_soft_reboot import prepare
    prepare()
    print(f"Prepared pinned Switch host overlay: {OUT}")


if __name__ == "__main__":
    main()
