# Buffy Switch feasibility contract — FIRST CLAUDE RUN

## What we're assessing

Original Xbox **Buffy the Vampire Slayer (2002), Europe game data**, targeting a native **Nintendo Switch 1 Atmosphere .nro**. This is a fast feasibility audit; **not** a commitment to write or port an entire Xbox game runtime.

Private source location:
`C:\Users\Public\App Developement\Decomps - Recomps\Projects\Buffy The Vampire Slayer\Game Files\Buffy the Vampire Slayer (Europe)\Buffy the Vampire Slayer (Europe)`

## Stage A — identify the actual data (read-only)

1. Verify that path and nested case-sensitive/repeated folder naming; list types/counts and high-level sizes. Find `default.xbe`, or document if missing. Show no game bytes in Git.
2. Report SHA-256 and size for XBE and any containing ISO if present, title/version/region and *verifiably parsed* XBE headers/sections/entrypoint/base/address conventions; do not invent technical details.
3. Inventory major file types (PAK, MSH, MTX, STL and any others actually encountered), obvious compression/packing patterns, engine strings if securely read, and unusual dependencies. Avoid massive file-by-file dump; summarize.
4. Separate Europe-build observations from US/game prototype/forum guesses. `Buffy The Vampire Slayer (Europe)` folder name is not executable identity proof.

## Stage B — reusable tool investigation

Check local availability and exact versions/SHAs of devkitPro, libnx, switch-tools, Python, VS/CMake, Git, 7-Zip, public source clones, optionally Claude skills. See `TOOL-SOURCES.md`. Avoid installing dependencies without a demonstrated need.

For each plausible path, fill evidence table: **tool**, **supports this exact title?**, **runtime/CPU lift**, **graphics (Xbox D3D/NV2A -> Switch)**, **audio/input/filesystem**, **estimated integration cost**, **missing pieces**, **why it does/doesn't save time**.

- Buffy Slayer Engine MSH tool = early asset research, does **not** recompile XBE or implement runtime.
- sp00nznet/xboxrecomp and TGP482 XboxXBERecomp = candidate static recompilers; confirm applicability to this XBE (not merely repo README).
- NFSU2 Switch = platform-layer proof reference; isolate truly portable components/licensing.
- Black Android/framework = a *different game*, not a free Buffy renderer/kernel contract.
- nxport = ideas for caches/profiles/submission, **not** a drop-in Xbox/Slayer Engine implementation.
- Search public code for an actual **2002 Buffy** recompilation or engine-level restoration; reject `Chaos Bleeds` false positives.

## Stage C — inexpensive decisive tests ONLY

If stages A/B identify a realistic source path, pick at most **one or two fast, reversible tests**:
- Parse XBE with a maintained public tool or inspect file/section metadata and identify kernel/library requirements.
- Verify that a selected asset parser recognizes actual sample file **without** copying it into Git.
- Optionally prove compiler/frontend can accept a tiny generic input; **do not generate full game code**, download huge SDKs, build a new renderer, or test on hardware in this first run.

Capture exact commands, compiler/tool versions, return codes, outputs/hashes that can be shared, and failure reasons. A failed test can be valuable if decisive. Don't fabricate artifacts or claim a running Switch port.

## Decision gates

- **GO — scoped prototype:** game-specific XBE analysis works and identifiable existing CPU/runtime/graphics/input pieces promise a small adapter; next test is narrow and concrete.
- **CONDITIONAL / RESEARCH ONLY:** executable and assets can be parsed, but missing graphics/kernel/runtime proof remains and one small decisive test could resolve it. Specify the exact test.
- **STOP / SHELVE:** no path without deep manual decompilation, writing a bespoke game engine, building an Xbox VM/emulator or an entire graphics backend. Conclude promptly, and describe what would change that judgment.

Ask whether a **PC intermediate port** would *actually* reduce Switch effort, not merely defer it. Do not require PC gameplay first if a smaller direct proof is feasible, but do not misclassify a PC-only renderer as Switch-ready.

## Report outputs (docs only)

Write in this directory:
- `BUFFY-FEASIBILITY-REPORT.md`: short executive decision; input identity; file/engine observations; candidate comparison; tested evidence; blockers; next 1-2 small tests; confidence and effort estimate.
- `BUFFY-EVIDENCE.json`: `date`, `repo_sha`, `input_root`, `xbe_sha256`, `file_counts`, `tools_checked`, `commands`, `gate_results`, `decision`, `unverified_assumptions`. No data payloads.
- `TOOL-LOCK.json`: exact local source SHAs and compiler versions with `missing`/ `not_checked` statuses distinguished.

Finish with clean Git status and a branch/commit reference if committed. Do not touch BLACK's worktree or commit any binary/artifacts/game files.
