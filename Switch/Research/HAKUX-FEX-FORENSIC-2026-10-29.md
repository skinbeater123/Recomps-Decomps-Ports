# hakuX 1.2.0 and Xbox-modified FEX — Switch 1 forensic source findings

**Reviewed:** 2026-10-29 (Australia/Sydney). **Scope:** non-executing inspection of two owner-supplied source ZIPs. No NRO, APK, FEX Switch build, real Switch hakuX game run, or FPS measurement has been performed. Findings are useful architectural references, not a validated emulator port.

## Exact inputs
- `hakuX-1.2.0.zip`: SHA-256 `2784d7393cf62d4fd3d36d75240a5532e56dbabc82897b1314249e32271c7be4`; source archive with kernel/XBE, NV2A/Vulkan, APU, Android and FEX glue. Its `external/fex` source directory is empty.
- `FEX-52018bf46a8279b22bce738548ab3f40db467064.zip`: SHA-256 `c9d343a2260d3243904d0e2b46ce4e9fe5df48aa3aad3cd3f9ffad56a8de326c`; includes ARM64 x86 translator, FEXCore, system instruction handling and Xbox integration. External `fmt`, `range-v3`, `rpmalloc`, `xxhash`, `vixl` etc submodule folders lack their sources. Exact hakuX v1.2.0 FEX gitlink SHA remains to be verified from Git metadata.
- Fork: [rfandango/FEX at 52018bf](https://github.com/rfandango/FEX/commit/52018bf46a8279b22bce738548ab3f40db467064), not automatically interchangeable with upstream FEX.

## Architecture map and reusable slices
| Layer | Source evidence (archive paths) | Potential cross-title use |
|---|---|---|
| XBE / disc / kernel | `native/core/{xbe_load,xdvdfs}.c`, `native/kernel/` | Kernel behaviour, loader semantics and Xbox APIs; verify license before copying |
| Guest CPU | `native/cpu/cpu.cpp`; `FEXCore/include/FEXCore/Core/Context.h` | Xbox system ops, guest-base mapping and FEX dynamic fallback research; no need to embed JIT into native BLACK by default |
| NV2A / Vulkan | `hw/xbox/hle/pb/`, `hw/xbox/hle/vk/` | Push-buffer, shader/texture format and GPU synchronization behavior where relevant |
| MCPX audio | `native/dev/apu/` | Voice/audio scheduling and APU-compatible interfaces |
| Guest memory | `native/core/vm.c`, `native/cpu/cpu.cpp` | VM alias model and known portability issues |
| JIT cache | `FEXCore/Source/Interface/Core/SharedCodeBufferManager.cpp`, `FEXCore/include/FEXCore/Utils/AllocatorHooks.h` | ARM64 instruction generation design, not a drop-in libnx implementation |

## FEX's Xbox-specific extensions
The fork defines `SetGuestMemoryBase`, `EnableSystemOps`, `SetGuestCycleCounterRatio`, `SetIDTRegister`, `SetHookQuery`, and x87 precision controls under `FEXCore/include/FEXCore/Core/Context.h`. hakuX wires the core in `native/cpu/cpu.cpp` and uses an Xbox-specific syscall/exception interface, rather than running a generic Linux x86 userspace environment. One fork commit addresses `RDTSC` time accounting around host pauses. This **does not** demonstrate that BLACK's separate XMV stutter is caused by the same issue.

## The two critical Horizon portability blockers
1. **Memory and faults:** `native/core/vm.c` reserves a 4-GiB *virtual* guest span, maps aliased physical pages with Linux `mmap(MAP_SHARED|MAP_FIXED)`, and uses `memfd_create` or AHardwareBuffer. hakuX employs `mprotect`, SIGSEGV/SIGBUS and Linux `ucontext_t` to intercept MMIO, track dirty pages and recover from guest faults. Horizon/libnx is not a POSIX memory manager. Reproducing efficient alias mapping **and** frequent recoverable protected-page faults is not yet demonstrated.
2. **JIT:** FEX uses dynamically generated ARM64 code caches (initial 64 MiB, up to 128 MiB as configured in this fork) with RWX Linux mappings and page guards. libnx `jitCreate`, RW/RX addresses and access transitions are promising primitives, but not sufficient proof for cache patching, relocations, instruction-cache coherency or dispatch recovery. Switch Cortex-A57 requires a conservative ARMv8 profile and verified host CPU feature detection.

**Important reuse:** The historical BLACK hardware diagnostics already reported a 4-GiB virtual reservation and two-way aliases of one 64-MiB .bss source using `MapProcessMemory` (see [shared knowledge](../SHARED-KNOWLEDGE.md)). Do **not** repeat those identical tests just to obtain another PASS. They do not yet prove hakuX's *general* dynamic mappings, high-frequency protection/fault recovery or JIT runtime semantics.

## GPU and device dependencies
hakuX's `hw/xbox/hle/vk/vkdev.c` expects a Vulkan graphics queue, `largePoints`, timeline semaphores, at least four descriptor sets and Vulkan 1.3 paths for `dynamicRendering`/`synchronization2`. It uses Android surface and external-hardware-buffer import mechanisms. Native Switch [mesa-switch](https://github.com/danfromtico/mesa-switch) and [nvk-switch](https://github.com/jhuz0/nvk-switch) may enable GPU work but there is no demonstrated Xbox-frame test, current feature enumeration or performance data for hakuX. Android hardware buffer import cannot simply be assumed on Horizon. Audio uses Android AAudio; Switch equivalents require integration.

## Separate, cheaper Android-on-Switch experiment
Switch v1 has [LineageOS support](https://lineageos.github.io/lineage_wiki/devices/nx/variant1/). hakuX's Android minimum is API 28. On a safe separate Android environment the APK could be used to test real Tegra A57 + GPU performance before undertaking native Horizon adaptation. This is only a **hypothesis**; driver extensions, CPU features, guest mapping/JIT permissions, thermal headroom and playable FPS must be measured. Do not alter the owner's established homebrew SD installation or assume Android results translate to an NRO.

## Disposition and stop/go
- **GO (selective):** consult hakuX XBE, Xbox kernel, GPU and APU logic where actual native port work exposes matching missing semantics. Maintain per-game forks and license boundaries.
- **GO (bounded investigation only):** reconcile exact FEX gitlink, close needed third-party dependencies, analyze Horizon guest memory/fault/JIT, compare existing hardware evidence, and query Vulkan target capabilities. Build/test once at an integrated decision milestone.
- **NO current commitment:** shipping a full native hakuX NRO or replacing playable BLACK. An NRO linking, simple clear/present, or showing a menu does not prove general Xbox game performance.
- **Optional alternative:** isolated Switch Android hakuX run using owned game material and credible FPS/audio/render capture, with no disruption to existing device.

## Source and license constraints
hakuX top-level license in uploaded source: **GPLv3-or-later**. FEX source: **MIT**. Third-party code has independent notices. Do not treat hakuX as permissively licensed merely because FEX is MIT; evaluate distribution obligations before transplanting any module. Do not publish game ISOs, XBE, ROMs, firmware, extracted executable-derived code or game media.

## Supporting references
- [hakuX upstream](https://github.com/rfandango/hakuX)
- [FEX fork 52018bf](https://github.com/rfandango/FEX/commit/52018bf46a8279b22bce738548ab3f40db467064)
- [libnx JIT API](https://switchbrew.github.io/libnx/jit_8h.html)
- [mesa-switch](https://github.com/danfromtico/mesa-switch), [nvk-switch](https://github.com/jhuz0/nvk-switch)
- [xemu issue #1947, BLACK XMV](https://github.com/xemu-project/xemu/issues/1947) — related symptom only, **not** a proven fix or identical cause
- [Repeatable workflow](../Knowledge/REPEATABLE-WORKFLOW.md), [evidence register](../Knowledge/EVIDENCE-REGISTER.md)

**Next actual work:** reconcile live BLACK/Buffy/SC1 fork states, identify which hakuX behavior is useful to existing blockers, and perform one cost-limited emulator stop/go investigation if warranted. Not a full emulator implementation order.
