# Claude Code instructions — Buffy the Vampire Slayer (Xbox 2002) -> Switch 1

Read **this file**, `../SHARED-KNOWLEDGE.md`, `FEASIBILITY-CONTRACT.md`, and `TOOL-SOURCES.md` before starting. Work as a separate research agent while Codex owns active BLACK implementation. Preserve the repo's Git state and never modify `Switch/Black` or its checkout.

**Owner goal:** small, inexpensive, fun side quest. **Not** an open-ended reverse engineering campaign. Prefer existing tested code/tools over engineering a missing subsystem. Shelve with clear evidence if achieving gameplay would take substantial custom runtime, kernel, graphics, engine recreation or manual decompilation.

**Correct title:** the **2002 original Xbox game, Buffy the Vampire Slayer**, likely The Collective's Slayer Engine. NOT `Buffy the Vampire Slayer: Chaos Bleeds` (2003), which has different code and public port projects. Never treat another title's recompilation as evidence this one works.

**Local private input path (read only):**
`C:\Users\Public\App Developement\Decomps - Recomps\Projects\Buffy The Vampire Slayer\Game Files\Buffy the Vampire Slayer (Europe)\Buffy the Vampire Slayer (Europe)`
Verify path existence and inventory before assuming its contents.

**Shared sources (inspect, never assume all present):**
`C:\Users\Public\App Developement\Decomps - Recomps\Tools\Sources`
`C:\Programming\devkitPro`
Other public references and pinned revisions are in `TOOL-SOURCES.md`.

**Switch target:** Nintendo Switch **1**, native **Atmosphere .nro**, NOT Android/Switchroot. No Switch hardware action or firmware changes without explicit authorization. Gameplay remains hypothetical.

**First run deliverable:** audit, **not** implementation. Discover executable and asset layout; identify suitable off-the-shelf reuse; perform only reversible, bounded local parsing probes. Document results in `BUFFY-FEASIBILITY-REPORT.md`, `BUFFY-EVIDENCE.json`, and `TOOL-LOCK.json` in this folder. Include copied commands, exit status, checked hashes, refs, uncertainties, exact stop/go recommendation and a realistic smallest next test. Separate facts, evidence and guesses. No expensive builds.

**Security/legal:** Never add or push original game files, `default.xbe`, ISO, extracted disc assets, binary content, disassemblies containing proprietary bytes, generated game C/C++, console keys, tokens, logs with secrets or unlicensed proprietary materials. Safe inventories (counts/extensions/sizes/hashes), public-source references and authored findings are permitted. Do not copy assets into this repository. Do not erase or modify the owner's game folder.

**Repository discipline:** use a separate `research/buffy-*` branch. Commit/push documentation only after verifying `git status` and file list. Never force-push, rewrite main or merge without review. If Git is unavailable or unauthorized, retain local report and state that no remote publication occurred.

**Cost budget:** Start by looking at actual data and reusable code. If no direct reuse path emerges quickly, finish with `STOP/SHELVE` instead of writing a new emulator/renderer. Ask for input only if access/ownership/permission blocks the essential test. No speculative runnable claims.
