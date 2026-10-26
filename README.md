# Recomps / Decomps / Ports

Evidence-led research and low-effort experiments for original Xbox -> Nintendo Switch 1 native homebrew ports. The goal is a **native Atmosphere .nro**, not Switchroot, streaming, a full emulator, or a new general-purpose Xbox runtime.

## Tracks

- [BLACK](Switch/Black/) — separate active Codex implementation and hardware tests. Preserve its existing workstream.
- [Buffy the Vampire Slayer (2002)](Switch/Buffy%20The%20Vampire%20Slayer/) — independently researched by Claude Code; **feasibility audit before any port**.
- Deathrow — optional follow-up only.

Shared context: [Switch/SHARED-KNOWLEDGE.md](Switch/SHARED-KNOWLEDGE.md).

## Owner constraints

This is a **small, inexpensive, fun side quest**. Reuse proven components and test decisive blockers early. If Buffy needs months of reverse engineering, a new GPU renderer, or a bespoke emulation platform, recommend shelving it rather than quietly expanding scope.

Public repository = documentation, safe scripts, external source references, and **non-proprietary** code only. Never upload game archives, extracted disc contents, XBEs, executable-derived regenerated C/C++, firmware, proprietary textures/audio/video, save data, private logs, or credentials. Keep those outside this Git tree. Report hashes and high-level analysis without embedding copyrighted payloads. Respect upstream licenses.

Current findings are dated **26 Oct 2026 (Australia/Sydney)**. Some were inherited from prior local tests and must not be treated as reverified by this repo.
