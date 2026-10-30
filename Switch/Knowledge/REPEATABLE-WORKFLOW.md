# Repeatable Xbox-to-Switch 1 porting methodology

**Status:** Working method, version 0.2 (2026-10-31), including lessons from owner-completed Buffy. Not a proven universal port recipe. Favor real playable results over repeated micro-gates.

## 1. Choose the source variant from evidence
- Inventory owned PC, Xbox, Android, source-release or existing recomp branches for the *same game*. Select by actual code availability, engine/asset equivalence, graphics backend, architecture, and runtime/ABI friction—not “Android is always best” or “PC is always best”.
- Hash and identify the exact executable/version and distinguish platform-specific assets. Never commit executable-derived code or proprietary assets to this public repository.
- Prefer using an established working fork and reusing the BLACK platform integration where genuinely transferable.

## 2. Build the smallest viable code path
- **First look for original linker maps / symbol metadata.** Buffy shipped `final.map` naming 41,601 function entries; seeded sp00nznet lifting plus targeted branch/SEH audit reached 42,683/42,683 translations. Compare function-end boundaries and jump-table/data gaps before trusting disassembly heuristics; avoid translating non-code as privileged x86 instructions.
- Inventory x86 lifting/AOT recomp completeness, unresolved calls, stack/SEH/TLS, guest pointers and Xbox kernel semantics; separate static translation from runtime JIT.
- Prefer thin per-title compatibility adapters over an entire general-purpose Xbox runtime unless a **measured** cross-title need justifies it. Buffy required a narrowly scoped `wbinvd` lifter no-op, utility-drive dismount semantics, and XDK **4432** fence-to-pushbuffer synchronization: do **not** copy these directly into BLACK's different XDK/runtime.
- For old XDK graphics where HLE signatures are missing, consider reusing an **NV2A pushbuffer LLE** runtime (Buffy/sp00nznet + NFSU2-Switch) rather than implementing every D3D API variant. Preserve renderer-specific ownership and avoid rewriting a working game architecture.
- Map game input → simulation → GPU submission → presentation → audio, with timebases and buffers explicitly identified.
- Use hakuX's XBE/kernel/NV2A/APU implementations as behavioral references when relevant; verify code licensing before copying.

## 3. Select a presentation and execution target
- **PC host:** fast debugging, toolchain work, deterministic traces; not proof of Switch viability.
- **Eden:** fast Switch NRO integration and visible rendering checks; cannot guarantee libnx JIT/memory permissions, native NVK behavior or physical hardware FPS.
- **Physical Switch 1:** final authority for real-memory SVCs, GPU, controls, audio, sustained frame pacing and playable status.
- **Switch Android:** optional separate hakuX APK experiment; does not demonstrate a Horizon-native emulator.
- Record renderer API, FPS and measurement method; a graphics smoke test and a playable game are different milestones.
- **Do not make mirrored guest RAM a universal pass/fail rule:** BLACK previously passed a 64-MiB two-way alias, while the later native Buffy log reported 28 failed mirrors and continued executing. Validate aliasing per title and operation; continued execution does not guarantee all memory behavior is correct.
- **Use native NVK proof where applicable:** Buffy's 30 Oct log shows Vulkan 1.3.305 on Tegra X1, shader/pipeline prewarming, real NV2A draws, audio and controller traces. NVK remains experimental. An old “Vulkan unavailable” diagnostic cannot overrule newer real-device execution evidence.
- **Profile before scaling:** keep GL and VK captures separate; compare identical game scenes, NRO/build IDs, cache warmness, clocks and internal scale. Capture game/render-worker load, waits, pushbuffer/draw count, GPU ms, shader compile/cache, audio underruns and frame hitches. Buffy reported GL 16–30 FPS, later Vulkan samples 13.5–41.2 FPS in varying scenes; neither proves stable 30 or universal speedup. Stabilize **1× 30 FPS** before 2×/60-FPS targets.

## 4. Economic checkpoint before major rewrites
- If code can reach meaningful real gameplay with modest compatibility changes, continue the native per-title route.
- If blockers are reusable Xbox kernel/APU/NV2A semantics, adapt one small component and document its portability.
- If the fix implies building a new guest MMU, fault handler, shader translator or OS compatibility environment, perform **one bounded decision test** first and stop/shelve if payoff is unconvincing.
- Do not spend credits generating an NRO after every step. Batch changes and build only at integrated milestones; ask for human device testing only when it can resolve a real decision.

## 5. Required result format for each game-fork handoff
Record: repository/branch/HEAD; exact owned input identity (hash only); tested hardware/OS; what ran and what did not; rendering/audio/controller/video status; linked logs or checksums; open blockers and severity; transferable techniques; license status; next meaningful integration milestone; stop/go decision.

## 6. Generalization and change management
- Keep central knowledge on GitHub `main`; per-game implementation branches remain autonomous.
- Promote methods with source and execution evidence; classify untested design proposals as hypotheses.
- When a newer hardware report supersedes an old diagnostic, update the central index with dates; never silently delete prior evidence.
- Keep a compact evidence register and links rather than duplicating entire game-fork repositories, binaries or giant test outputs.
- Read the [Buffy completed-port retrospective](BUFFY-PORT-RETROSPECTIVE-2026-10-31.md) before generalizing any XDK, guest-memory, NV2A, NVK or APU fix.
