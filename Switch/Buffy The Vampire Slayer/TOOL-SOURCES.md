# Tool and source directory — Buffy probe

**Observe installed state; don't install/re-clone automatically.** These are references, not claims every checkout is installed. Capture local `git -C <folder> rev-parse HEAD` and `git remote -v` before reuse. HEAD below is only the public remote state **observed 26 Oct 2026**, not necessarily the pinned local checkout.

| Source | Public reference revision | Purpose / limitation |
| --- | --- | --- |
| [bartholomew91/buffy-xbox-decomp-tools](https://github.com/bartholomew91/buffy-xbox-decomp-tools) | `a6811e5c8d6e216c2096d07c503b03ce6c47a385` | Slayer Engine asset work; MSH vertices/partial faces, MTX/STL future work. Not a game port |
| [sp00nznet/xboxrecomp](https://github.com/sp00nznet/xboxrecomp) | `f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b` | General Xbox static recompiler candidate; title coverage to verify |
| [antoxa2584x/nfsu2-sw](https://github.com/antoxa2584x/nfsu2-sw) | `d3bbc3094f8e1ad3b34593eabd431f7d251b14cb` | Recomp-to-Switch precedent; Horizon libnx, game-specific renderer/NVK/memory. Not Buffy |
| [lemiur/Game-Decompilation-Skill-For-Claude](https://github.com/lemiur/Game-Decompilation-Skill-For-Claude) | `eedfe281d4fab7d8cdaf98b9f72f6a6ac4db04be` | Optional analysis workflow, not a substitute for verified evidence |
| [TGP482/XboxXBERecomp](https://github.com/TGP482/XboxXBERecomp) | Check local `tool-lock.json` or Git SHA | XBE parsing/recompiler experiment; applicability to Buffy uncertain |
| [XboxDev/extract-xiso](https://github.com/XboxDev/extract-xiso) | Check local checkout | Extract XISO only if input isn't already extracted |
| [switchbrew/switch-examples](https://github.com/switchbrew/switch-examples) | Check local checkout | Portable libnx project skeleton |
| [nxporting/nxport](https://github.com/nxporting/nxport) | Earlier *reviewed* `ed55d4e5aff5a8a1922edc0b95ad9b6a24096e84` | Conceptual reference for cache keying / GPU serials / mod paths; not native Buffy/Xbox solution |

Additional related public sources: [RanggaCasper/Black-Android](https://github.com/RanggaCasper/Black-Android); [portingpete/Black-2006-Recomp](https://github.com/portingpete/Black-2006-Recomp). BLACK-specific. Do not copy their fixed game hooks into Buffy.

Early Buffy parser README describes user-provided files from backup -> XISO extraction -> QuickBMS PAK extraction -> Tauri/Svelte/ThreeJS visualization. Script reference: `https://aluigi.altervista.org/bms/buffy_2002_pak.bms`. Inspect script provenance and run against samples only in a **private temporary directory** if needed; PAK extraction is *asset research*, not evidence for a CPU port.

**Do not confuse the original with [KaikoClanworth1/buffy-chaos-bleeds-pc](https://github.com/KaikoClanworth1/buffy-chaos-bleeds-pc).** That is a recompiled native PC project for `Buffy the Vampire Slayer: Chaos Bleeds` (2003), a different game; investigate reusable framework techniques only if concrete.

Earlier owner workstation probe: `C:\Programming\devkitPro`, GCC `16.1.0`, libnx `4.12.0`, switch-tools `1.13.1`, deko3d. Horizon NVK/target Vulkan, SDL3 and glslang uninstalled as of previous BLACK hardware gate. Use known toolchain, don't infer graphics availability from it.
