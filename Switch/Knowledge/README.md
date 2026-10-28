# Cross-title knowledge base — Xbox to Switch 1

**Initialized:** 2026-10-29. This is a living **evidence index and methodology**, not a claim that all current game-fork code or private proof artifacts have been audited.

## Entry points
- [Evidence register](EVIDENCE-REGISTER.md): provenance, proof level, repeatability and unresolved tests.
- [Repeatable workflow](REPEATABLE-WORKFLOW.md): decision-making and implementation order across titles.
- [Historical Switch baseline](../SHARED-KNOWLEDGE.md): 26 Oct diagnostic results with 29 Oct supersession note.
- [hakuX + FEX forensic findings](../Research/HAKUX-FEX-FORENSIC-2026-10-29.md): emulator alternative and targeted compatibility reuse.

## Portfolio
- **BLACK:** playable on an actual Switch according to owner checkpoint dated 27 Oct 2026; cutscene/video stutter remained. Preserve the established native port; seek current commit and run evidence before describing exact fixes or FPS.
- **Buffy the Vampire Slayer:** independent Xbox decomp/recomp track; source lifting and native/graphics experiments have been discussed, but a playable Switch result is **not** established here. Reconcile actual fork HEAD, PRs and artifact receipts before upgrading status.
- **Splinter Cell (SC1):** PC-versus-Xbox input choice, Android-derived work and native Switch path are under investigation. Reconcile `SC1-PORT-STATUS.md` and actual fork HEAD before using any game-specific implementation conclusion.
- **Deathrow / other Xbox titles:** optional future candidates, not authorized large engineering projects.
- **hakuX/FEX:** alternative shared Xbox emulator and reference architecture. Source-reviewed; **no** native Horizon hakuX gameplay or performance proof.

## Transfer procedure
1. Identify the exact fork URL, branch, commit SHA, source executable hash and legal publication boundary.
2. Read the fork's current results and distinguish host, Eden, Android, and **physical Switch** evidence.
3. Extract the generalizable technique and prerequisites; identify which parts are game-specific.
4. Add a short, dated evidence entry with exact proof and known failures; then link it from here if substantial.
5. Only promote a generalized rule after at least one applicable real use, and ideally a second-title confirmation. Do not confuse a potentially reusable abstraction with demonstrated cross-game reuse.

**Pending ingestion:** current BLACK build/runtime receipts; Buffy latest graphics/NRO evidence; SC1/PC-vs-Xbox decision checkpoint and Android branch; exact fork HEADs and canonical links. These must be gathered from the respective repositories, not reconstructed from stale memory.
