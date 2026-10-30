# Cross-title evidence register

**Established:** 2026-10-29. This register preserves provenance and explicit proof level; it is not an independently reproduced audit of all game forks.

## Evidence levels
- **HARDWARE-PROVEN:** linked, inspectable real-Switch execution receipt + exact build/input identity. Historic claims lacking raw evidence in this repo must be qualified.
- **HOST-TESTED:** instrumented desktop/Android/Eden runtime result, with environment specified.
- **SOURCE-VERIFIED:** direct inspection of source or reproducible static artifact; no execution proof.
- **OWNER-REPORTED:** user checkpoint not independently checked here.
- **HYPOTHESIS:** proposed design/possible compatibility without a target result.
- **BLOCKED:** known missing capability/failed step, with environment and date.

## Current ledger

| ID | Claim | Level and date | Evidence / limitation | Reuse decision |
|---|---|---|---|---|
| SW-001 | On a previous BLACK diagnostic Switch, a 4-GiB **virtual** reservation and two-way aliases of one 64-MiB source passed. | Prior hardware evidence summarized 2026-10-26; raw logs absent from public repo | [SHARED-KNOWLEDGE](../SHARED-KNOWLEDGE.md), including 16,384-page checks and MapProcessMemory .bss qualification. Not equivalent to complete hakuX guest VM or Linux signal recovery. | Reuse existing evidence before repeating a VA/alias smoke test. |
| BLACK-001 | BLACK became **playable on actual Switch 1**. | OWNER-REPORTED 2026-10-27 | Owner status update; current build SHA, run receipts, FPS and coverage still require fork reconciliation. This supersedes the 26 Oct “not playable” statement. | Preserve native port as working reference. |
| BLACK-002 | BLACK video/cutscenes still stutter. | OWNER-REPORTED 2026-10-27 | Cause unconfirmed. [xemu #1947](https://github.com/xemu-project/xemu/issues/1947) reports a potentially related XMV symptom but not a demonstrated shared fix. | Investigate timing/decode/queue behavior without replacing runtime. |
| HAKUX-001 | hakuX 1.2.0 includes native Xbox kernel, XBE loader, NV2A-to-Vulkan, MCPX APU and embedded FEX CPU glue. | SOURCE-VERIFIED 2026-10-29 | Uploaded hakuX archive SHA-256 `2784d7393cf62d4fd3d36d75240a5532e56dbabc82897b1314249e32271c7be4`; [source analysis](../Research/HAKUX-FEX-FORENSIC-2026-10-29.md). Not compiled. | Use for targeted compatibility research. |
| FEX-001 | Supplied FEX fork exposes Xbox-specific guest-memory-base, system-op and cycle-clock controls. | SOURCE-VERIFIED 2026-10-29 | FEX commit `52018bf46a8279b22bce738548ab3f40db467064`, archive SHA-256 `c9d343a2260d3243904d0e2b46ce4e9fe5df48aa3aad3cd3f9ffad56a8de326c`. Exact gitlink in supplied hakuX ZIP not independently confirmed. | Keep fork pinned; do not swap in unmodified FEX. |
| EMU-001 | hakuX might run as a Horizon-native emulator using FEXCore JIT + experimental Vulkan NVK. | HYPOTHESIS 2026-10-29 | Linux mmap/protect/signal faults, aliased guest memory, JIT cache, Android AHB/external-memory and renderer feature requirements remain untested on this target. | Bounded preflight only, not a replacement for recompilation. |
| EMU-002 | Running hakuX Android APK on a Switch 1 Android install may offer low-cost performance data. | HYPOTHESIS 2026-10-29 | hakuX minSdk 28; actual installed OS, Vulkan features, JIT operation and game FPS unknown. Do not change existing SD/install unilaterally. | Optional isolated test; Android success ≠ Horizon NRO success. |
| TOOL-001 | Eden Switch emulator is installed on the production PC, and graphic game rendering has been observed in it. | OWNER-REPORTED 2026-10-27 | Does not validate physical Switch performance, Horizon JIT or native NVK graphics. | Use between integrated physical-device milestones. |
| BUFFY-001 | Owner reports Buffy **completed**, superseding 26 Oct Windows-only assessment. | OWNER-REPORTED, 2026-10-31 | Source-completion and coverage details await final fork/HEAD import; current public [PR #2](https://github.com/skinbeater123/Recomps-Decomps-Ports/pull/2) stops at E6 Windows title screen. | Treat as completed user milestone, not reason to erase historical E6 provenance; [retrospective](BUFFY-PORT-RETROSPECTIVE-2026-10-31.md). |
| BUFFY-002 | Native Buffy Vulkan/NVK game renderer executed on Switch; multi-minute runtime, >1,000 draws/frame and APU/input traces. | OWNER-SUPPLIED HARDWARE LOG INSPECTED, 2026-10-30 | Private `buffyx_log.txt` build `1030.0049-vk`; Tegra X1 NVK Vulkan 1.3.305; 1280×720 swapchain, 1× internal rendering; 13.5–41.2 FPS sampled; ~1,500 APU frames/s; output logs 0 underruns/drops. Exact Git HEAD/NRO checksum not yet public. | Native Vulkan is **demonstrated**, not just a proposed SDK. Use profiling and pipeline prewarming ideas; no assumed fixed FPS. |
| BUFFY-003 | 26 Oct source-assisted recompilation achieved 42,683 translated functions, 0 failed and Windows title-screen boot. | SOURCE-VERIFIED/HOST-TESTED, 2026-10-26 | [Public E6 report](https://github.com/skinbeater123/Recomps-Decomps-Ports/blob/research/buffy-claude-audit-20261026/Switch/Buffy%20The%20Vampire%20Slayer/BUFFY-FEASIBILITY-REPORT.md), 41,601 entries from retail linker map; 34 extra seeds, `wbinvd` no-op, utility-drive dismount shim, XDK 4432 D3D fence. | Seed from linker maps; use scoped SDK-specific kernel/fence fixes; preserve copyright and ABI boundaries. |
| BUFFY-004 | Buffy continues executing with CodeMemory guest mapping despite failed additional RAM mirrors. | OWNER-SUPPLIED HARDWARE LOG INSPECTED, 2026-10-30 | `buffyx_log.txt` reports 4-GiB virtual reservation, 28 mirror failures, 0/28 mapped and later working Vulkan/FS/APU scenes. Does **not** prove mirrors are unnecessary for all correctness or games. | Avoid imposing BLACK's mirrored-window requirement as a universal gate. |
| BUFFY-005 | Later GL gameplay profiler identified a renderer/thread bottleneck; Vulkan results are a separate run. | OWNER-REPORTED profiling, 2026-10-29 | GL 16–30 FPS (usually 17–25), GL worker 90–95% busy and main game ~19% waiting; 30 Oct NVK log samples cannot be treated as an apples-to-apples speedup. | Paired exact build/scene/profile before optimization claims. |
| SC1-001 | Splinter Cell source-variant and Android-derived implementation path under investigation. | Historical fork conversation; current status unverified here | Current `SC1-PORT-STATUS.md` and fork HEAD not yet ingested into central main. | Do not generalize the chosen base prematurely. |

## Pending evidence reconciliation
1. Capture BLACK's latest real-Switch playable commit/build identity, version, measured FPS, gameplay coverage and video-stutter traces.
2. Locate/ingest Buffy's **final** implementation fork HEAD and NRO checksum, complete-playthrough/known-limitations evidence and paired GL/NVK profiling. The 30 Oct Vulkan hardware log and old E6 report are already collated.
3. Read the current SC1 fork HEAD, `SC1-PORT-STATUS.md`, PC-versus-Xbox analysis and Android graphics progress.
4. Verify hakuX v1.2.0 gitlink to FEX, nested dependency closure and current native NVK capability data.
5. Promote a generalizable technique to the [method](REPEATABLE-WORKFLOW.md) only when proof is adequate, with a source link and relevant caveat.
