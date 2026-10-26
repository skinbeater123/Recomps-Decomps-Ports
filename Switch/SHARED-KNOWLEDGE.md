# Shared Xbox -> Switch 1 knowledge checkpoint

**Status date:** 2026-10-26. **Provenance:** earlier BLACK-specific reports from another workspace: `FOUNDATION-REPORT.md`, `build-evidence.json`, `HARDWARE-GATE.md`, `NXPORT-REVIEW.md`, `VULKAN-GATE.md` and private hardware-run evidence. This file is a **human-curated transfer summary**; those exact raw artifacts have **not** been imported into this public repo and should be requested or read locally if present. Never invent their contents or imply that proof for BLACK automatically transfers to Buffy.

## Hardware proven for BLACK diagnostics, NOT for Buffy

- Native libnx `.nro` ran on an actual Switch under Atmosphere/application-title-takeover. Identity `eb800005681e2b12`; supplied logs have `RUN_END log_io=OK`.
- A 4 GiB **virtual-address span** (not 4 GiB physical RAM) was reserved. `GuestReservation4GiB=PASS`.
- One 64 MiB physical source in writable NRO `.bss` was mapped simultaneously at the two guest-window addresses `0x80000000` and `0xF0000000`; 16,384 pages were sampled with reciprocal read/write checks, plus cleanup. `TrueTwoWayAliasing=PASS`. `MapProcessMemory` worked for the eligible `.bss` source. This is not the same as `svcMapMemory`.
- One ordinary page using CodeMemory passed; broader ordinary allocation/decommit semantics remain to be validated. Shared-memory and raw-physical mechanisms returned resource/state errors. These are not evidence of a general impossibility.
- Installed diagnostic exposed HOS 20.3.0, hbloader v2.4.4; exact Atmosphere version/Switch model not recorded. Hints are not successful SVC calls.
- Compiled generated BLACK functions, SDK objects and two diagnostic NROs are evidence of *compilability*, **not** playable game code. Earlier regenerated BLACK analysis: 15,042 functions and 680,140 decoded instructions across 64 partitions. Three sampled partitions (0, 60, 63) compiled at `-O2`.
- No BLACK playable build or native Vulkan/NVK clear/present proof established. Graphics remains blocked by missing genuine Horizon NVK target SDK and shader dependencies.

## Environment previously checked

- devkitPro: `C:\Programming\devkitPro`; devkitA64/GCC `16.1.0`; libnx `4.12.0`; switch-tools `1.13.1`; deko3d present.
- MSYS2 CMake/make used for native Switch builds because normal Windows CMake was rejected by devkitPro build integration.
- Target `portlibs/switch` lacked SDL3, target Vulkan/NVK, glslang, ImGui, and `sys/mman.h` at last inspection. Do **not** pretend PC SDKs satisfy Horizon graphics.
- The local `aarch64-none-elf-g++` had a reproducible `-O1/-O2` internal compiler error involving unaligned `may_alias` scalar argument typedefs. In BLACK an isolated packed `may_alias` structure/member overlay compiled and subsequently passed sampled hardware runtime tests. Do not apply it blindly to Buffy.
- Claude Code CLI was previously detected on Windows (`claude --version` 2.1.292 on 22 Oct), but must be probed again before use.

## Where reusable source/tooling was staged

Earlier workspace root: `C:\Users\Public\App Developement\Decomps - Recomps` (spelling deliberate).
Shared public checkouts were planned/staged under `Tools\Sources\`; inspect presence and exact `git rev-parse HEAD` before relying on them. No automatic install or heavy clone unless clearly justified.

- `Buffy-Xbox-Decomp-Tools` — [bartholomew91/buffy-xbox-decomp-tools](https://github.com/bartholomew91/buffy-xbox-decomp-tools): **early Slayer Engine asset/mesh exploration**, not a CPU recompiler or complete port.
- `XboxXBERecomp-TGP482` — [TGP482/XboxXBERecomp](https://github.com/TGP482/XboxXBERecomp): candidate source for x86 XBE analysis/recompilation; suitability for this game's image **unproven**.
- `xboxrecomp-sp00nznet` — [sp00nznet/xboxrecomp](https://github.com/sp00nznet/xboxrecomp): platform/runtime reference; APIs and coverage need direct assessment.
- `NFSU2-Switch` — [antoxa2584x/nfsu2-sw](https://github.com/antoxa2584x/nfsu2-sw): native Horizon examples, guest memory/renderer bootstrap and game-specific caveats. Not a turnkey Buffy engine.
- `extract-xiso` — [XboxDev/extract-xiso](https://github.com/XboxDev/extract-xiso), **only if** disc extraction is actually needed; the user already provided an extracted Buffy game directory.
- `Switch-Examples` — [switchbrew/switch-examples](https://github.com/switchbrew/switch-examples).
- `Claude-Decomp-Skills` — [lemiur/Game-Decompilation-Skill-For-Claude](https://github.com/lemiur/Game-Decompilation-Skill-For-Claude): optional procedural reference; inspect contents, do not grant it authority over owner constraints.
- `BLACK-Android` — [RanggaCasper/Black-Android](https://github.com/RanggaCasper/Black-Android) and `BLACK-PC-Recomp-HD-Map` — [portingpete/Black-2006-Recomp](https://github.com/portingpete/Black-2006-Recomp): **Black only**, not reusable Buffy game hooks.

## Architecture lessons (conditional, not yet Buffy requirements)

- Keep a **game-specific executable identity gate** (exact bytes/hash, region, XDK assumptions, patch mapping); do not reuse BLACK offsets or assume the Europe Buffy build matches US.
- Preserve guest pointers/ABI, threading/TLS/exceptions and synchronization where required. Distinguish CPU submission completion from GPU completion.
- A target Vulkan path may borrow the NFSU2 `VK_NN_vi_surface` / `NWindow` initialization while retaining a proven game-specific renderer. No usable Horizon NVK SDK was present locally; no renderer should be designed until executable analysis identifies the game's needs.
- `nxport` ([nxporting/nxport](https://github.com/nxporting/nxport)) was reviewed at commit `ed55d4e5aff5a8a1922edc0b95ad9b6a24096e84` for separated GPU submission/coherence, shader-cache identities, profiles and mods. Its Apple/Metal and Nintendo-specific implementation **does not convert Slayer Engine or solve Xbox guest memory**. Transfer methodology, not code/architecture indiscriminately.
- Assets are distinct from CPU runtime. Extracting `.pak` and displaying `.msh` does not show a game can be recompilied or played.
- Keep mod/HD work deferred until original title runs. Protect file paths and preserve output determinism.

## Priority for new Buffy probe

Examine actual `default.xbe`, file structures and dependencies. Do not start from BLACK's recompiler partitions or adapt BLACK rendering before checking whether they are relevant. Validate Europe image SHA and XBE title/sections; identify entry address, import/library signatures, any embedded engine information, possible executable protection, XDK version and rendering/audio technology from direct evidence. Record uncertainties. Attempt only a bounded public-tool parsing smoke test if it informs a decisive go/no-go question.
