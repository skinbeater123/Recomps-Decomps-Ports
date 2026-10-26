# Buffy the Vampire Slayer (2002, Xbox, Europe) → Switch 1: feasibility audit

**Date:** 2026-10-26 · **Author:** Claude Code (independent of Codex's BLACK workstream) · **Repo base:** `main` @ `58d7327`

## Decision: CONDITIONAL. The CPU side is now proven on both recompilers; one decisive runtime test is left

The retail disc ships the developer's full **MSVC linker map (`final.map`)** next to `Default.xbe`. Its timestamp matches the XBE's PE timestamp exactly. It names every one of the 41,601 function entries (38,841 of them game code from 563 object files) and gives their exact addresses. With the map supplying function boundaries:

- **TGP482** lifts the whole XBE with **0 unimplemented instructions**. Generated partitions compile for AArch64 at `-O2` once BLACK's GCC workaround is applied.
- **sp00nznet** (update, E5) finds **all 41,601 map functions** and translates **42,656/42,656 functions, 0 failed**. 99.3% of function ends agree with the map. One real instruction needs a lifter rule (`wbinvd` in XDK D3D device creation).

So the CPU half of a static recompilation is not the risk here.

The open question is the **runtime**, meaning the kernel, D3D8/NV2A graphics and DirectSound/APU audio. Buffy is built with **XDK 4432**, an early 2002 SDK:

- **TGP482 runtime.** Its high-level (HLE) XDK layer only covers XDK 4831/5849, and it renders through Windows D3D12. Using it for Buffy means porting that HLE layer to 4432 (render-state numbering, about 52 struct offsets, about 10 older API variants, DirectSound differences). On top of that it needs a Switch host such as BLACK-Android's Vulkan/SDL3 layer, which is itself still unproven on Switch.
- **sp00nznet `xboxrecomp`, as ported to Switch in `nfsu2-sw`.** This one is **title-agnostic**. It runs the game's own statically linked D3D library and executes the resulting NV2A pushbuffer through GL or Vulkan backends. Audio goes through a low-level (LLE) MCPX APU model taken from xemu, and Horizon memory is handled by a Win32-compat layer. It routes **120/120** of Buffy's kernel imports, and the NFSU2 port reports running on console. Because it works at the pushbuffer level, it **sidesteps the XDK 4432 HLE gap entirely**. Its x86 lifter now handles Buffy (E5).

**Recommended route:** sp00nznet xboxrecomp (Switch fork from nfsu2-sw), with function boundaries seeded from `final.map`. TGP482 stays as a validated fallback for the CPU side.

**Effort:** small for CPU lifting (already shown). The runtime is **medium** (weeks of hobby time) if the sp00nznet pushbuffer executor handles 4432-era D3D output with only small fixes, and **large** if it does not. Nothing here needs a new emulator or a new renderer.

**What would change this to STOP:** sp00nznet's runtime failing to reach a first presented frame on PC because of 4432-specific pushbuffer, APU or kernel behaviour that needs substantial new low-level emulation, *and* the TGP482 4432 HLE port turning out to be more than a focused adaptation.

### Milestones (no milestone is claimed beyond its evidence)

| Milestone | Status |
| --- | --- |
| Executable identity / layout parsed | **Proven** (own probe + sp00nznet parser + TGP482 loader agree) |
| Assets extracted | Not attempted (not needed for the runtime decision) |
| Functions recompiled (lifted to C/C++) | **Proven on both.** TGP482: whole image, 0 unimplemented. sp00nznet: 42,656/42,656 translated, 0 failed, 11 unimplemented sites (10 in-body data, 1 real `wbinvd`) |
| Generated code compiles for AArch64 | **Proven for 2 of 128 TGP482 partitions** (largest + first) with overlay. sp00nznet C **not compiled** yet |
| NRO linked | **No** |
| Graphics displayed | **No** |
| Gameplay | **No** |

## 1. Input identity (Europe build, private, read-only)

| Item | Value |
| --- | --- |
| Folder | `…\Game Files\Buffy the Vampire Slayer (Europe)\Buffy the Vampire Slayer (Europe)` (extracted, 152 files, 2,007,716,654 bytes) |
| ISO alongside | `Buffy the Vampire Slayer.iso`, 2,008,481,792 B, SHA-256 `423aedd3f8d1fac04fd2f8889bf054ddb12006c01fdd1d721057dacae2efbd5a` |
| Archive | `Buffy the Vampire Slayer (Europe).7z`, 473,989,863 B, SHA-256 `d24bc77e408a1918beeb41d23fcb26ea89b5179bd78ac4b3c82368fe5090a065` |
| `Default.xbe` | 7,819,264 B, SHA-256 `F91CD33C980F6B5514AA98925397338EE1DE6E7B432DD393EFD470C0F0702F40`, SHA-1 `A11E0B70E3848885CF127D16348F97AE1CC471D3` |
| `final.map` | 15,129,566 B, SHA-256 `ce6e0d00dd2cff78b9de68c54bd208815a0b0883b9aff73e6c56e1663b80ba5b`; module `XGameBuffy`, timestamp `3d35c92d` = XBE PE timestamp |
| Certificate | Title ID `45410012` (publisher `EA`, #18), name "Buffy: The Vampire Slayer", region `0x4` (rest of world/PAL), version `0x2`, cert time 2002-08-07 |
| Build path | `F:\srccore\Final\XGameBuffy.exe` (PE built 2002-07-17) |
| Base / entry / thunk | base `0x10000`; entry `0x00579EA2` (retail key); kernel thunk `0x00616D80`; TLS dir `0x007126E0`; no protection/packing seen |
| XDK | All 8 libraries **1.0.4432 QFE1**: XAPILIB, D3D8, D3DX8, XGRAPHC, DSOUND, XBOXKRNL, WMVDEC, LIBCMT |
| Kernel imports | 120, all named (cross-checked: own table, map, sp00nznet) |

Whether the ISO's embedded XBE is byte-identical to the extracted one was not checked. The extracted one is what was analysed.

**Sections (14, all preload):** `.text` 5.50 MB (0x11000), `D3D` 71 KB, `D3DX` 8.7 KB, `XGRPH` 8 KB, `DSOUND` 115 KB, `WMADECXM` 2 KB, `WMADEC` 99 KB, `WMVDEC` 202 KB, `XPP` 30 KB, `.rdata` 1.23 MB, `.data` 1.81 MB virtual (145 KB raw), `DOLBY` 29 KB, plus `$$XTIMAGE`/`$$XSIMAGE` (title and save images). Map section N lines up exactly with XBE section N-1; the map's entry point resolves to the XBE header's entry point.

## 2. How the executable works (from the map's names and addresses)

- **Slayer Engine, C++ (MSVC 7-era):** 563 game objects such as `Slayer.obj`, per-character AI (`Angel`, `Spike`, `Master`, …), `TResourceManager` PAK loading (`SceneRes.obj`), a scripting/property system (`InstanceManager.obj`, `TScriptDef`), cinematics, collision, and a D3D abstraction layer of its own (`D3D_Render`, `D3D_Shaders`, `D3D_State`, `D3D_Texture`, …).
- **C++ EH:** 174 `__CxxFrameHandler` frames, **0 try blocks** (counted from FuncInfo tables). Unwinding is destructor-only, so TGP482's "0 catch blocks" is correct, not a miss.
- **Graphics:** standard XDK **D3D8** API. It uses programmable **vertex shaders** (`CreateVertexShader`/`LoadVertexShader`/`SelectVertexShader`), `SetPixelShader` (no `CreatePixelShader` linked), cube and volume textures, palettes, `DrawIndexedVertices(UP)`, `DrawVerticesUP`, and stencil/shadow render states. **No Bink.** It doesn't call the `D3DDevice_*Push`/`RunPushBuffer` APIs. Whether the game writes NV2A registers directly (the image does contain `D3D__GpuReg`) is unverified.
- **Audio:** XDK **DirectSound** over the MCPX APU (`dsstdfx.bin` effects image, I3DL2 reverb, HRTF), with WMA music decoded by the linked XDK `WMADEC`.
- **Video:** 5 WMV (ASF) intro/legal movies, decoded by the linked XDK `WMVDEC` software decoder.
- **System:** `CreateThread` (multithreaded), `XMountUtilityDrive`/`XFormatUtilityDrive` (HDD cache; `install.dat` is 109 MB), save games and memory units, `XLaunchNewImageA`, and XInput (gamepad).

## 3. Assets actually present

| Type | Count / size | Observation |
| --- | --- | --- |
| `.pak` | 65 / 1.7 GB | All begin `0x00052014`; chunked container (header shows a `0x8000` block size); embeds `.mtx`/`.msh`/`.wav`/`.tga` names. Format not parsed this run |
| `.wma` | 62 / 95 MB | Music (`Sound/Music`) |
| `.rpe` | 8 / 22 MB | Dialogue banks (header: version 1, entry count) |
| `.wmv` | 5 | ASF GUID header |
| `.xpr` | 4 | `XPR0` XDK resource bundles (fonts, launch images) |
| `.mtx` | 2 loose (more in PAKs) | Magic `MULTITEX` |
| `.msh`, `.stl` | inside PAKs only | No loose files. No `.stl` names in the sampled PAK |
| other | `install.dat`, `dsstdfx.bin`, `final.map`, `Credits.txt`, `DVD.txt` | |

A recompiled engine reads the original PAKs itself, so **asset parsing is not on the critical path** for a port.

## 4. Tools: what is real

| Tool (local HEAD) | Exact title? | CPU lift | Graphics | Audio/input/FS | Verdict |
| --- | --- | --- | --- | --- | --- |
| bartholomew91/buffy-xbox-decomp-tools `a6811e5` | Yes, assets only | — | — | — | A 256-line Tauri prototype: pattern-searches MSH vertex blocks, faces acknowledged wrong, no PAK/MTX/STL parser. **Saves no port work.** (Its public repo also ships 224 extracted `.msh` game files; don't copy that practice.) |
| TGP482/XboxXBERecomp `90bccea` | Not supported by its scanner (`no signatures for these library builds; available: 4831 5849`) | **Works with map seeds: 0 unimplemented** | HLE D3D8 → D3D12 (Windows), 4831/5849 only | HLE DSound→XAudio2, SDL3 | CPU proven; runtime needs an XDK 4432 port plus a Switch host |
| sp00nznet/xboxrecomp `f0f8a46` (v0.16.0) | Parser OK; kernel 120/120 routed | **Works with map seeds** (capstone 5.0.6): 42,656/42,656 translated, 0 failed | LLE: NV2A pushbuffer executor → D3D11/GL | xemu APU LLE, kernel shim | **Best runtime fit** (title-agnostic); its `tools/symbols/map_names.py` named 41,612 functions from our map |
| antoxa2584x/nfsu2-sw `d3bbc30` | No (NFSU2) | uses sp00nznet | Adds `nv2a_gl` (switch-mesa) + `nv2a_vk` (NVK) | Horizon memory/input/files/SDL2 audio in `platform/win32_compat.c` | **Switch platform layer to reuse**; NFSU2 hooks (`src/`, 67 fixed addresses in `recomp_manual.c`) are not reusable |
| RanggaCasper/Black-Android `c1b7fb0` | No (BLACK) | uses TGP482 pin `99078b1` | Vulkan backend for TGP482 (`native/vulkan.cpp`, no game addresses) | SDL3 | Only helps the TGP482 route |
| nxporting/nxport `ed55d4e` | No | — | Concepts only | — | Methodology only (already reviewed for BLACK) |
| lemiur/Game-Decompilation-Skill `eedfe28` | — | Byte-matching decomp method | — | — | Not the chosen route; 38,841 game functions is disproportionate even with names |
| XboxDev/extract-xiso `3f5b62c` | — | — | — | — | Not needed: input already extracted |

No public **2002 Buffy** recompilation, decompilation or engine restoration was found (web search plus repository review). `buffy-chaos-bleeds-pc` is the 2003 sequel and was not used as evidence.

## 5. What transfers from BLACK

| BLACK result | Buffy status |
| --- | --- |
| devkitA64 GCC 16.1.0 / libnx 4.12.0 / switch-tools 1.13.1 | Re-verified installed (pacman db) |
| GCC `aarch64_function_arg_alignment` ICE on `aligned(1) may_alias` scalars | **Reproduced on Buffy's partition 0** (`aarch64.cc:7502`). The packed-struct overlay (`scripts/make_a64_overlay.py`, same transform) fixes it for partitions 0 and 50 |
| TGP482 recompiler | Same tool; HEAD built in 8 s from BLACK's already-fetched Zydis/toml++ |
| 4 GiB reservation + `MapProcessMemory` aliasing at `0x80000000`/`0xF0000000` (hardware PASS) | **Directly relevant**: both runtimes place guest apertures there. nfsu2-sw prefers shared memory (BLACK saw resource/state errors for it on this console) and falls back to code memory without mirrors. BLACK's proven `MapProcessMemory` alias is the likely fix |
| Native NVK clear/present | Still unproven on hardware (BLACK workstream). nfsu2-sw's **GL path via devkitPro `switch-mesa`** avoids depending on it |
| BLACK hooks/renderer, XDK 5849 config | **Not transferable** (different title, different XDK) |

## 6. Experiments (all private outputs, exact commands in `BUFFY-EVIDENCE.json`)

1. **XBE identity probe** (`scripts/xbe_probe.py`): exit 0; the results above.
2. **E1a, TGP482 `xbe_symbols`:** exit 1, `no signatures for these library builds; available: 4831 5849`. This is a hard stop for its automated path.
3. **E1b, map → TGP482 symbols** (`scripts/map_to_tgp482.py`):
   - The map's entry matches the XBE.
   - Of 248 runtime names, **119 resolve** to unique addresses (D3D8 72, DSound 34, XAPI 7, CRT 6) and 2 are ambiguous (adjustor thunks).
   - 41 belong to libraries Buffy doesn't link (Bink, XNet, XOnline).
   - Of the remaining 86, about 10 are real **4432 API variants** (`GetRenderTarget` vs `GetRenderTarget2`, a single `SetVertexShaderConstant` vs `…1/4/Fast`, `D3D::InternalAddRefSurface`, `D3D::MakeSpace`, `SetTileNoWait`, `PixelJar::Lock2DSurface`). The rest are **not linked** into this image (unused XDK functions; trig is inlined x87).
   - XDK data globals (`D3D::g_Device`, `D3D__RenderState`, `D3D__TextureState`, `D3D__DirtyFlags`, `g_FvfVertexShader`) are named in the map too.
4. **E2, TGP482 `xbe_recomp`, three variants** (4 s each):

   | Config | Functions | Map entries missed | Extra vs map | Overlapping decodes | Unimplemented insns |
   | --- | --- | --- | --- | --- | --- |
   | default heuristics | 44,228 | 133 | 2,760 | 607 | **821** (28 kinds: `iretd`, `lldt`, `insb`, `arpl`, `daa`…: data decoded as code) |
   | + map seeds | 44,516 | 0 | 2,915 | 601 | 821 |
   | **map seeds, no gap-fill/pointer heuristics** | **41,718** | **0** | 117 | **7** | **0** |

   The last row covers 5,927,002 of 6,315,372 code-section bytes, with 344 jump tables and 40 callback entries. Output is 135 files / 204 MB of C++, **kept private**.
5. **E3, AArch64 compile** (`aarch64-none-elf-g++ 16.1.0 -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE -std=gnu++20 -O2`):
   - Partition 0 with pristine headers: **ICE**, exit 1.
   - With the overlay: partition 0 compiles in 4 s (`.text` 194,825 B) and partition 50 (largest, 2.9 MB source) in 6 s (`.text` 272,452 B), both exit 0.
   - The other 126 partitions were not compiled.
6. **E4, sp00nznet parser + kernel coverage:** exit 0; parser output matches. **120/120 imports routed**, 0 needing new code.
7. **E5, sp00nznet pipeline, seeded from `final.map`.**
   - **Setup:** a private venv with `capstone==5.0.6` (wheel SHA-256 `761c3dea…7064`). The pipeline ran from a `git archive` snapshot of `f0f8a46`, so the shared checkout stayed pristine. Seeds come from `scripts/map_to_seeds.py` (41,601 entries).
   - **disasm** (all code sections, 1.91 M instructions):

     | Run | Time | Functions | Map entries missed | Extra vs map | End = next map symbol / padding | Short ends | Overruns |
     | --- | --- | --- | --- | --- | --- | --- | --- |
     | unseeded | 568 s | 43,129 | 25 | 1,553 | 28,548 / 12,702 | 305 | 21 |
     | **map-seeded** | 747 s | 42,656 | **0** | 1,055 | 27,937 / 13,354 (**99.3%**) | 306 | **4** |

     The extras are mostly `tail_jump_alias` entries (811), sp00nznet's design for tail jumps into function bodies. 1,040 are in `.text`; none are in `DOLBY`, which is APU DSP code that the disassembler also swept as x86.
   - **The 306 short ends** (`scripts/compare_sp00nznet_functions.py` with `xrefs.json`; gap contents checked separately):
     - 24 continue in another detected function.
     - 264 gaps (16,019 bytes) contain no branch target. Nearly all start with MSVC multi-byte NOP fill followed by switch jump/index tables, so they are data, not lost code.
     - **18 gaps (1,061 bytes) do contain a branch target**. These need review or a `[function]`-style seed.
   - **map_names resolve:** `entry point check: MATCH`. 75,658 symbols resolved and 41,612 function names applied (`scripts/apply_map_names.py`, using sp00nznet's own sanitiser).
   - **func_id** (18 s): 4,975 vtables validated and 32,312 functions classified as game code.
   - **abi_analysis** (3 s): 42,656 entries, 7,468 of them `thiscall`.
   - **recomp** (`--all --split 250`, 148 s): **42,656/42,656 translated, 0 failed**. That's 3,874,674 lines of C in 171 files (153 MB, private).
   - **Remaining issues:**
     - 3 unresolved call stubs. One is a LIBCMT x87 dispatch label (`87disp.obj`) that needs a seed. Two are misdecoded data, one of them outside the image.
     - 11 unimplemented-instruction sites. Ten are data inside game-function bodies (`CIBone`, `CharacterPhysics`, `BuffyFXMgr`, `GUIMenuLoadGame`, `TipWindow`); they would only trap if executed. **One is a real `wbinvd` in XDK `d3d8:dxgcreate.obj`**, which needs a no-op lifter rule before D3D device creation can run.

## 7. Most important blocker

**Nobody has yet shown Buffy's XDK 4432 D3D/DSound output running on any runtime.** On the recommended route that means the sp00nznet NV2A pushbuffer executor and APU. On the TGP482 route it means a 4432 HLE layer that doesn't exist yet. The CPU translation is no longer the question. For the Switch build specifically, the second blocker is the same one BLACK has: a GPU backend proven on hardware (GL via `switch-mesa`, or NVK).

## 8. Next experiments (smallest first)

1. ~~Lift Buffy with sp00nznet, seeded by the map~~. **Done (E5): PASS.** No unresolved or unsupported-instruction blockers outside data regions, apart from the one `wbinvd`.
2. **Windows boot-to-first-flip** with the sp00nznet runtime, from the `templates/new-game` project. Pass: kernel init, XDK D3D device creation and at least one pushbuffer flip of the EA/Fox logo path, with the log captured. This PC step *does* shorten the Switch path: the lifted code, kernel and pushbuffer executor are the same code the Switch build uses, and only the presentation backend changes.
   - If it fails deep in APU/NV2A emulation for 4432-specific reasons, re-evaluate. The TGP482 4432 HLE port becomes the fallback, otherwise shelve.
   - **Prep, small:**
     - Map `wbinvd` to a no-op in the lifter.
     - Seed the `87disp.obj` label.
     - Review the 18 gaps that contain a branch target.
     - Drop the two misdecoded-data stubs.
     - Configure `xbox_memory_layout.h` from E4's section table (`.data` virtual end `0x009163B4`, `.bss` included).

Only after (2) passes: install devkitPro `switch-sdl2` + `switch-mesa`, build the nfsu2-sw platform layer around Buffy's generated code, and replace its shared-memory mode with BLACK's proven `MapProcessMemory` alias if the console rejects shared memory.

## 9. Unverified assumptions / uncertainties

- nfsu2-sw's console results are upstream claims; they were not reproduced here.
- sp00nznet's "title-agnostic" support has not been demonstrated on an XDK 4432 image.
- Tegra X1 performance of a 5.5 MB `.text` title plus LLE pushbuffer execution is unmeasured.
- Only 2 of 128 TGP482 partitions were compiled for AArch64. sp00nznet's 171 C files were not compiled for any target. No link was attempted.
- sp00nznet's C output being translated does not mean it is semantically correct. In particular, the abi_analysis results for the 7,468 `thiscall` functions are unverified.
- PAK internal format and the `XLaunchNewImageA` use (`launch_indyj.xpr`) were not investigated.
- The aluigi `buffy_2002_pak.bms` script was not retrieved (HTTP 403).
- Whether the ISO's XBE equals the extracted `Default.xbe` was not checked.

## 10. Publication hygiene

Committed: this report, `BUFFY-EVIDENCE.json`, `TOOL-LOCK.json` and authored scripts under `scripts/`. Nothing executable-derived is committed: no XBE bytes, generated C++, map-derived address configs or assets. Private outputs live in the workspace's git-ignored `Projects/Buffy The Vampire Slayer/private/`.
