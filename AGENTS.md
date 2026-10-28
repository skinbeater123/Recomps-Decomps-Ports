# Repository-wide agent contract — Recomps / Decomps / Ports

Applies to all folders in this repository. The public `main` branch is the central **research and methodology authority**, not the automatically deployable source tree for every game fork.

## Required reading before work
1. `README.md` — project scope, current tracks, and owner constraints.
2. `Switch/SHARED-KNOWLEDGE.md` — historical, date-qualified Switch observations.
3. `Switch/Knowledge/README.md` and `Switch/Knowledge/REPEATABLE-WORKFLOW.md` — cross-title evidence and working method.
4. The relevant game's own up-to-date code, status, and proof files. A central summary never overrides direct current-source evidence.

## Evidence discipline
- Record every transferable claim with game, source repository/ref or supplied-file hash, platform, date, proof artifact, and status: HARDWARE-PROVEN, HOST-TESTED, SOURCE-VERIFIED, OWNER-REPORTED, HYPOTHESIS, or BLOCKED.
- State explicitly what was NOT tested. Do not promote “links”, “boots”, “renders”, or “menu runs” to “playable”.
- Keep owner-reported progress distinct from an independently reviewed test log. Preserve earlier checkpoints as history and explicitly supersede stale conclusions.
- Reuse shared algorithms and behavior only after validating target-game executable identity, ABI, GPU/audio semantics, and source license. Never silently transplant BLACK offsets or patches into Buffy or Splinter Cell.
- If a claim is contested, retain both evidence links and articulate the remaining test rather than inventing consensus.

## Implementation and efficiency
- Protect working per-game branches; do not merge, reset, or rewrite game forks when updating central knowledge.
- Treat GitHub as the source of truth for documented decisions. Preserve commit and PR references; stage local experiments separately.
- Prefer targeted source inspection, meaningful integrated milestones and the installed Eden Switch emulator for quick feedback. No NRO after every change, no large synthetic gate suites without an actual blocker, and reserve human Switch hardware testing for significant milestones.
- Native per-title recompilation is currently the working default. hakuX/FEX whole-emulator portability is an optional bounded investigation, not an authorized replacement of the playable BLACK runtime.
- Stop when the projected work becomes a substantial custom emulator or GPU/runtime rewrite without a clear economical payoff.

## Publication and licenses
- **Never commit** proprietary game archives, extracted media, executables, generated code derived from proprietary game binaries, firmware/BIOS, keys, save files, private logs or secrets. Publish hashes and non-infringing high-level observations instead.
- Preserve third-party attribution and license terms. hakuX is GPLv3-or-later; its FEX dependency is MIT. Do not assume copying hakuX code into another game port is license-neutral.
- Put durable cross-title findings in `Switch/Knowledge/EVIDENCE-REGISTER.md` and explanatory research in `Switch/Research/`. Make game-specific changes in their respective repositories.
