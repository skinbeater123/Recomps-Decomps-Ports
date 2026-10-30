# Buffy (Xbox 2002) → Switch 1: completed-port retrospective and transfer notes

**Compiled:** 2026-10-31 (Australia/Sydney). **Game:** Buffy the Vampire Slayer (2002 original Xbox, Europe/PAL), title ID `45410012`, XDK **4432**. **Portfolio status:** Owner reports Buffy port *completed*. This retrospective records (a) independently inspectable **GitHub evidence through 26 Oct** and (b) newer **owner-supplied native Switch runtime/profiling observations through 30 Oct**. It is **not** a substitute for importing final working fork HEAD, final NRO checksum or game-completion/coverage receipts.

### Evidence provenance and limits
- [Buffy PR #2](https://github.com/skinbeater123/Recomps-Decomps-Ports/pull/2), branch `research/buffy-claude-audit-20261026`, HEAD `1a1ecf62c089c6daeaaa96d5cdf0e6b595f7db3b`: public scripts, E1–E6 investigation, [feasibility report](../Buffy%20The%20Vampire%20Slayer/BUFFY-FEASIBILITY-REPORT.md), [evidence JSON](../Buffy%20The%20Vampire%20Slayer/BUFFY-EVIDENCE.json), tool pins. As of this review PR #2 remains open and **ends at Windows title screen**, not at final Switch completion.
- Owner-supplied **`buffyx_log.txt`**, last modified 2026-10-30, 1,727 rendered lines; private, not published. Contains actual Switch `[switch]`/libnx runtime, build `1030.0049-vk`, XBE boot, NVK gm20b GPU initialization, draw/GPU measurements, controller/FS/APU records and frame-rate samples through 125 s. This proves a **native Switch Vulkan execution trace** but does not independently identify the associated git commit or establish every level/playthrough completed.
- Separate owner/Claude report on late-October **OpenGL gameplay**: approximately **16–30 FPS**, usually **17–25 FPS**, GL thread **90–95%** busy with no idle, game thread around **80%** busy and around **19%** lost to GPU waits. Source profiler binary and exact run identity must be paired with their matching NRO and config for formal comparison. These numbers must not be falsely presented as the Vulkan run.
- Current final public build/HEAD, film playback, quality of audio, control coverage and full game completion receipts are **pending source reconciliation**, despite owner's explicit port-completed milestone. Do not roll that milestone back to E6.

## 1. What solved CPU recompilation

**Retail linker map beats blind discovery.** Original PAL game contains the developer's MSVC `final.map`, matching executable timestamp. Public report identifies **41,601 map function entries** and complete function naming. It was used to seed both lifters, rather than treating spurious x86 bytes in switch tables or codec data as instructions.

- TGP482 XboxXBERecomp with automatic signatures failed on **XDK 4432** (signatures supported 4831/5849). With map-seeded, heuristics-limited function detection, it lifted **41,718** functions with zero unimplemented instructions, but its 4432-specific HLE runtime would have required substantial adaptation.
- The chosen path was [sp00nznet/xboxrecomp](https://github.com/sp00nznet/xboxrecomp), drawing on [NFSU2-Switch](https://github.com/antoxa2584x/nfsu2-sw)'s Horizon runtime and **low-level NV2A pushbuffer execution**, which avoids hardcoding newer-XDK D3D8 HLE interfaces.
- E5 initially lifted **42,656/42,656** functions with zero translate failures. E6 added **34 targeted manual seeds**: 17 SEH `__finally` entries plus 17 LIBCMT dispatch labels. Branch-target gap count decreased **18 → 1**; **42,683/42,683** translated with zero failures. Manual seeds were not a license for unbounded guessing.
- At Windows E6, original code + shared runtime reached title screen after the first-run hard-disk-cache install; 25 FPS flips and a rendered title screen were observed; movie quads remained black at that stage.
- A known devkitA64 GCC 16.1.0 internal compiler error on packed `may_alias` scalars was previously mitigated using a packed-structure overlay; do not apply this to arbitrary project code without reproducing the failure.

**Portable method:** inventory the exact executable and look for vendor link maps/debug symbols before spending tokens on broad heuristics; compare seeded vs unseeded function ranges, audit gaps with *actual* branch targets, and keep generated proprietary output private.

## 2. Three small correctness adaptations that unlocked execution

1. **`wbinvd`** from older XDK D3D device creation: on a static native translation path, a carefully scoped no-op lifter rule was sufficient in the tested context. **Do not** ignore arbitrary privileged instructions globally.
2. **Utility-drive dismount:** returning success for Buffy's `FSCTL_DISMOUNT_VOLUME` path allowed `XFormatUtilityDrive` / first-run extraction to proceed. Respect private cache persistence and title-specific semantics; a blanket success for every FSCTL in every game would be unsafe.
3. **XDK 4432 `D3D::BlockOnTime`**: wire guest D3D semaphore/fence waits to NV2A pushbuffer executor progress, rather than assuming command submission equals completion. **Never copy this 4432-specific adapter into BLACK's XDK 5849 code without ABI and behavior verification.**

**Portable method:** trace a single blocked guest call to the concrete kernel/PB/APU primitive it requires, then add the narrowest adapter with a reproducible before/after run. Preserve a platform-specific compatibility table with SDK-version guards.

## 3. Native Switch runtime: 30 Oct Vulkan evidence

The 30 Oct `buffyx_log.txt` reports:
- Atmosphère title-override/full-memory applet type 0, core mask `0x7`, **3,189 MB available** reported; **4,096 MB virtual guest reservation**, 64 MB contiguous guest window; `120/120` bridged kernel imports. Generated CPU code is running natively; this is **not full-system Xbox CPU emulation**.
- Guest mapped from **CodeMemory views of heap blocks without aliasing**. All **28 additional RAM mirrors failed** (`0xD401` / host refusal); tiled aperture at `0xF0000000` also failed. Crucially, the game then **continued running**, reaching sound, game files and 1,000+ draw-call scenes. **This is not proof that the missing aliases have no correctness effects**; it does prove that an unqualified “all Xbox titles require fully aliased guest RAM to boot” rule is wrong.
- Actual native Vulkan device: **NVIDIA Tegra X1 (NVK gm20b), Vulkan 1.3.305**; swapchain **1280×720, 3 images**; internal original game surface **640×480** stored in a **853×480** render target; **1× rendering**, no FXAA, 1× anisotropy, depth D24S8. NVK warns that it is not Vulkan-conformant. This is **much stronger evidence than an isolated clear/present gate**.
- **61 shader programs**, **122 cached SPIR-V** objects, **91 pipelines prewarmed in ~249 ms**; 563 KB pipeline cache. Draw stats include ~**1,465**, **2,112** and **1,719** calls/frame in different scene samples, with associated GPU estimates **17.24 ms**, **8.91 ms** and **8.32 ms** average respectively. These are different time windows, not a paired same-scene benchmark.
- Sampled FPS at approximately 10,20,30,...120 seconds: **22.9, 41.2, 38.7, 24.8, 13.5, 30.4, 36.2, 27.4, 19.4, 15.4, 21.2, 25.3**. Scene-dependent **13.5–41.2 FPS** in this trace; does not establish stable 30 FPS or a universal Vulkan-over-GL speedup. There are frame hitches ~51–56 ms even when no shaders or textures were compiled/loaded.
- **APU pacing ~1,500 frames/s (real-time target)** in the logged periods; output repeatedly reports **0 device gaps, 0 queue underruns, 0 dropped buffers**. This is evidence of output queue stability, **not** a listening-based audio-quality audit. Native OHCI interrupts and pad reports demonstrate active input/device emulation; not every controller action is verified.
- The log still emits a counter named **“GL thread idle”** while the renderer registers **NV2A Vulkan**; likely legacy profiler wording. Do **not** misclassify this run as GL or infer GL/Vulkan comparison from that counter.
- Shader prewarm, cache/descriptor reuse, render-pass barriers, zero-copy WSI, frame timing, worker-thread presentation and vertex culling instrumentation are all transferable *diagnostic strategies*. Their exact Vulkan code, shader cache bytes and Xbox device ABI are not automatically portable to another game's renderer.

## 4. The performance lesson: measure the actual bottleneck, not the story

Earlier reported **GL** gameplay was **16–30 FPS, mostly 17–25** with GL worker 90–95% busy and game thread waiting approximately 19% for GPU work. This justified a bounded Vulkan/NVK test. The later **Vulkan** hardware trace demonstrates functional native integration but still fluctuates widely, including sub-20-FPS scenes. These are **different runs**; do not infer a quantified speedup without equal scene, clocks, settings, input, NRO identity and profiler.

In some Vulkan windows the estimated GPU cost is about 8–9 ms but the total game frame takes much longer, so GPU execution alone cannot explain the final FPS. Candidate contributors: CPU-side pushbuffer decode, draw submission volume, command recording, draw-call overhead, thread/guest lock scheduling, and synchronization. Conversely, in the 17.24-ms GPU sample, GPU load is clearly material. **Investigate per scene, not one universal bottleneck.**

A good next *optimization* experiment (only if needed) is a matched GL/NVK baseline at **1×** with identical route, clocks and profile capture, prioritizing stable **30 FPS** before 2× scaling, postprocessing or 60 FPS claims. The port's completion milestone and performance optimization are separate statuses.

## 5. Reuse matrix for the rest of the portfolio

| Transfer | BLACK | Splinter Cell | Future Xbox-only titles |
|---|---|---|---|
| Detect `final.map` or equivalent symbol provenance before heuristics | Useful methodology, not Buffy's actual symbols | High priority before rerunning lifting | Very high |
| sp00nznet + title-independent NV2A pushbuffer path | Compare only if needed; preserve functioning BLACK direct D3D8→Vulkan path | May be relevant to Xbox variant, but don't assume PC port uses NV2A | Strong candidate if XDK HLE unsupported |
| XDK 4432 fence and utility-drive adaptations | **Do not copy directly** (XDK 5849/runtime differences) | Only after direct ABI/call trace | SDK-version-gated adapter library |
| CodeMemory guest memory without all mirrors | Not a reason to discard BLACK's proven MapProcessMemory alias implementation | Test own actual game needs | Avoid mandating universal alias pass |
| NVK 1× pipeline/cache/descriptor/worker-present lessons | Compare implementation/driver constraints; preserve own proven shader results | Strong renderer diagnostics reference | Candidate backend optimization |
| APU 1,500-frame pacing and zero-underrun checks | Useful verification criteria, no APU replacement mandate | Useful | Strong |
| GL/VK profiler and draw/hitch counters | Compare per scene/per NRO | Strong | Strong |

## 6. Repeatable completion packet requirement

For a **finished** port, central knowledge should eventually link: game fork URL + branch + commit, owner-confirmed playable/complete milestone, executable identity hash (not binaries), NRO build/hash and renderer API, device/Horizon/clock settings, real gameplay route and video/audio/controller checks, representative FPS with profiler matching that exact build, recognized limitations, approved shareable source changes and upstream licenses. **This file intentionally contains no extracted game content, executable-derived C or proprietary asset data.**

**Outstanding action:** obtain/inspect the **actual final Buffy GitHub fork or export**. PR #2 is an accurate *historical* source-level record, but does **not** contain the 30 Oct finished gameplay/Vulkan work. Do not merge that PR as though it were the final port.
