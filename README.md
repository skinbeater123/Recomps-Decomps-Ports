# Recomps / Decomps / Ports

Evidence-led original Xbox → Nintendo Switch 1 native homebrew ports, with **static/native recompilation as the established default** and an optional, bounded shared-emulator research track. Our goal is actual playable games on physical Switch hardware, not simply producing an NRO or collecting compilation passes.

**Knowledge checkpoint:** 31 October 2026 (Australia/Sydney). Historical findings are separately dated; see proof levels before treating a report as current.

## Current tracks

- [BLACK](Switch/Black/) — **owner reports playable on actual Switch 1 as of 27 Oct 2026**. Cutscene/video stutter remained at that checkpoint; precise build/FPS verification belongs in its working fork. Protect the working native path.
- [Buffy the Vampire Slayer (2002)](Switch/Buffy%20The%20Vampire%20Slayer/) — **owner reports port completed**. A private 30 Oct real-Switch `1030.0049-vk` log shows the native NVK game renderer, APU, input events and gameplay-scale drawing, with scene-dependent 13.5–41.2 FPS samples. The latest final code HEAD/NRO hash is not present in the older public PR #2. [Completed-port retrospective](Switch/Knowledge/BUFFY-PORT-RETROSPECTIVE-2026-10-31.md).
- [Splinter Cell (SC1)](Switch/Splinter%20Cell/) — PC/Xbox source choices, Android-derived work and Switch-native implementation investigation. Use actual SC1 branch and status receipts for current conclusions.
- **Deathrow / other titles** — optional follow-ups; no authorization for lengthy speculative custom runtimes.
- **hakuX 1.2.0 / Xbox-modified FEX** — source-level research into reusable Xbox kernel, XBE, NV2A, APU and possible full emulator on Switch. **No Horizon native hakuX game execution or performance proof.** [Forensic assessment](Switch/Research/HAKUX-FEX-FORENSIC-2026-10-29.md).

## Shared knowledge and agent guidance

- [AGENTS.md](AGENTS.md) — common Codex/Claude/agent rules for this repository.
- [Knowledge index](Switch/Knowledge/README.md) — cross-game findings, ingestion status and evidence provenance.
- [Evidence register](Switch/Knowledge/EVIDENCE-REGISTER.md) — what has actually run vs source-inspected, user-reported, or hypothesized.
- [Repeatable porting methodology](Switch/Knowledge/REPEATABLE-WORKFLOW.md) — source selection, native AOT, GPU/audio, target tests and stop/go economics.
- [Buffy completed-port retrospective](Switch/Knowledge/BUFFY-PORT-RETROSPECTIVE-2026-10-31.md) — concrete linker-map, low-level XDK, guest-memory, NVK, performance and audio lessons from a native Switch title.
- [Shared diagnostic checkpoint](Switch/SHARED-KNOWLEDGE.md) — prior 26 Oct baseline, now with a clear 27–29 Oct supersession note.

## Owner constraints and publication rules

This is a **small, inexpensive, enjoyable side project**. Reuse proven components, prioritize meaningful integrated progress, use Eden for intermediate Switch build feedback where appropriate, and only request physical hardware tests at major milestones. Do not produce a new NRO after every trivial change or build excessive synthetic gates. Stop/shelve work if a port becomes a substantial emulator/kernel/GPU rewrite without clear value.

GitHub is the source of truth for public documentation and knowledge, but **game implementation forks remain separate**. This central repo must not reset or merge those forks as a side effect of knowledge curation.

Public content is limited to documentation, safe scripts, external source references and non-proprietary code. Never commit copyrighted game archives, extracted discs, XBEs, proprietary generated C/C++, firmware, game media, save data, private logs, credentials or keys. Use source hashes and high-level method summaries; respect GPL and third-party license obligations.

**Evidence note:** This repository's 26 Oct BLACK diagnostics were a historical snapshot and did not yet establish playability; the newer 27 Oct owner report supersedes that particular status statement. Exact playable build receipts should be linked after current fork reconciliation.
