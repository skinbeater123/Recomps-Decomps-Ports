# Repeatable Xbox-to-Switch 1 porting methodology

**Status:** Working method, version 0.1 (2026-10-29). Not a proven universal port recipe. Favor real playable results over repeated micro-gates.

## 1. Choose the source variant from evidence
- Inventory owned PC, Xbox, Android, source-release or existing recomp branches for the *same game*. Select by actual code availability, engine/asset equivalence, graphics backend, architecture, and runtime/ABI friction—not “Android is always best” or “PC is always best”.
- Hash and identify the exact executable/version and distinguish platform-specific assets. Never commit executable-derived code or proprietary assets to this public repository.
- Prefer using an established working fork and reusing the BLACK platform integration where genuinely transferable.

## 2. Build the smallest viable code path
- Inventory x86 lifting/AOT recomp completeness, unresolved calls, stack/SEH/TLS, guest pointers and Xbox kernel semantics; separate static translation from runtime JIT.
- Prefer thin per-title compatibility adapters over an entire general-purpose Xbox runtime unless a **measured** cross-title need justifies it.
- Map game input → simulation → GPU submission → presentation → audio, with timebases and buffers explicitly identified.
- Use hakuX's XBE/kernel/NV2A/APU implementations as behavioral references when relevant; verify code licensing before copying.

## 3. Select a presentation and execution target
- **PC host:** fast debugging, toolchain work, deterministic traces; not proof of Switch viability.
- **Eden:** fast Switch NRO integration and visible rendering checks; cannot guarantee libnx JIT/memory permissions, native NVK behavior or physical hardware FPS.
- **Physical Switch 1:** final authority for real-memory SVCs, GPU, controls, audio, sustained frame pacing and playable status.
- **Switch Android:** optional separate hakuX APK experiment; does not demonstrate a Horizon-native emulator.
- Record renderer API, FPS and measurement method; a graphics smoke test and a playable game are different milestones.

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
