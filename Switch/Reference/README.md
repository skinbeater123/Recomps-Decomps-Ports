# Prior evidence and tooling — reference archive

**Provenance:** User-supplied evidence from earlier BLACK Switch 1 investigations, archived **26 October 2026** to make existing research available to Claude working on *Buffy the Vampire Slayer (2002)*. The files are historical inputs, **not newly reproduced results**. Keep the chronology explicit:

1. `BLACK-FOUNDATION-REPORT-20261026.md` plus `BLACK-build-evidence-20261026.json` describe the **pre-hardware** compiler/bootstrap gate. In that earlier snapshot, hardware execution was `NOT TESTED`.
2. `BLACK-HARDWARE-GATE-20261026.md` **supersedes that hardware status**: the owner's later supplied logs proved libnx hardware execution and memory primitives, but not Vulkan or Black/Buffy gameplay.
3. `NXPORT-REVIEW.md` records reusable methodology, not working Buffy Switch integration.
4. `bootstrap-recomps-HISTORICAL.ps1` is a source-inventory/workspace setup script captured from the earlier work. **Audit its side effects; do not run during the first Buffy probe**. Its optional flags can install software/download repos; it was written for a different workspace Git layout.

Use the separate Buffy documents in `../Buffy The Vampire Slayer/` to guide this audit. None of these reports contain Buffy XBE-specific execution proof. Copyrighted/private game binaries, full generated functions, hardware logs and build packages were **not** imported.
