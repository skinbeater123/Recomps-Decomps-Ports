# Reused sources — 27 October 2026

| Source | Pin / role | Integration gap |
| --- | --- | --- |
| [Burnout3 Switch](https://github.com/antoxa2584x/burnout3-sw) | `28663a61cb925311d2ff516d6216df84af0b7c42`, branch `switch`; selected generator, C guest ABI, kernel, Horizon lifecycle, filesystem, SDL audio/input, pushbuffer executor, NV2A Vulkan shaders/renderer | SC1-specific discovery, XDK 4928 behavior, Bink/LIN execution and shadow correctness remain to be proven |
| [xboxrecomp](https://github.com/sp00nznet/xboxrecomp) | `f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b`; narrow CPUID/EFLAGS/OF/PF lifting backport and Pentium III identity | Retains the Switch fork's TLS, register, preemption, MMIO and memory ABI; no general runtime replacement |
| [NFSU2 Switch](https://github.com/antoxa2584x/nfsu2-sw) | Local reference `d3bbc3094f8e1ad3b34593eabd431f7d251b14cb`; inherited through Burnout3 | Its title-specific hooks and addresses are not copied |
| [BLACK NX](https://github.com/gerisson1996/BLACK-NX-PORT) | Inspected `b50fc26a75363fe954ca1c22d450118970b45dc6`; alternative C++ host/platform | More game-specific BLACK/Android glue; not selected |
| [XboxXBERecomp](https://github.com/TGP482/XboxXBERecomp) | Local `90bccea3fc6ef8dba8c6b601e11c94c8048b3494`; alternative generator/SDK | Different guest ABI; not combined with the selected runtime |
| [Black-Android](https://github.com/RanggaCasper/Black-Android) | Local `c1b7fb0079cb1c0bad1c375ef4b983f00a436399`; existing ARM64 lineage/reference | No BLACK generated functions or gameplay hooks reused |
| Local BLACK Horizon integration | Read-only NVK/glslang installations and the hardware-confirmed unified-heap allocation policy/static ICD dispatch pattern | SC1 has its own small C adaptation; BLACK source, stage and working files are untouched |

The self-contained NVK archive SHA-256 is
`ff65a74b46fe749f6be73eac3c8968d70e312c7646f815f26b69f4aa35737d26`.
It exports the ICD resolver, so the SC1 renderer loads entry points through
`vk_icdGetInstanceProcAddr`, as the existing BLACK host does. No new renderer is
created. The archive includes its Expat/zlib/Rust support; raw Mesa SDK link
instructions cannot be applied unchanged. glslang is the existing Switch build.

Boot glue is generated from pinned upstream source into `private/host` with
checked replacement contexts. The upstream checkout stays intact. The generator
overlay similarly lives under `private/codegen`. Original resolution is retained
and Burnout's 16-line overscan crop is removed. No game time-step changes or
picture-option hooks are carried over. Windows-only scheduling/environment/clock
bridges support differential debugging and are excluded from the Switch binary.

An SC1 startup run also exposed incorrect new-allocation alignment in the
shared bridge. SC1's original binned allocator indexes pool metadata by the upper
16 address bits. A narrow `kernel_bridge.c` overlay page-rounds region sizes and
uses 64 KiB alignment for new reservations, including pure-reserve fallbacks.
This preserves the original level-option array across reallocations; the same
game code then constructs and opens `LMaps/000_menu/common.lin` correctly.
No allocator, game table or filename is replaced with title-specific results.

The actual class-initialization callbacks at `0x00028760` and `0x000531D0`
revealed the same registration pattern calling `0x0002C670`. The scoped
`recover_class_seeds.py` pass reads immediate callback arguments at those call
sites and accepts only aligned `.text` entries preceded by compiler NOP/INT3
padding. It found 231 callback entries at 261 registration sites, including
20 missing entries in the prior discovery. The generated seed table is private;
the script and the separately maintained measured seeds are public.
The same pass reuses xboxrecomp's vtable scanner, retaining tables only when
decoded code stores their address into an object and method entries have
compiler padding. It verified 238 tables and supplied 89 previously missing
method starts, including the observed archive target `0x0002C230`. Inferred
interior labels are not indiscriminately promoted to function entries.
The original D3D SetRenderState dispatch then exposed another missing target
at `0x001ED970`. Its indexed call at `0x001ED472` proves the 30-entry handler
table for states `0x88..0xA5`; the same recovery pass reads that exact table and
checks that every target lies in the XDK D3D section. This reuses original
handlers rather than replacing render-state operations.

XDK 4928 graphics startup reached WBINVD at `0x001F6202`. The instruction bridge
now orders coherent guest-memory accesses with a host memory barrier. This is
separate from renderer submission and GPU-completion fences, which remain the
upstream runtime's responsibility.

The same pinned sp00nznet source supplies a narrow switch-arm decoding fix.
SC1's CRT copy (`0x001B1820`) has an embedded jump table followed by an arm
at `0x001B197C`. The old resynchronizer kept a stale instruction at `0x001B197E`,
inside that arm's MOV instruction. The resulting extra byte OR changed a freed
block's next pointer by `0x4000`, eventually causing the bad compact object index.
The overlay now removes every stale instruction starting inside a newly decoded
instruction. `check_crt_copy.py` extracts and executes the actual lifted CRT
routine locally: the old code fails even for a zero-byte copy; the fixed code
passes 12,336 size/alignment/overlap cases, guard-byte and register checks.

## LIN and other references

Both landaire articles were read: [part 1](https://landaire.net/a-file-format-uncracked-for-20-years/)
and [part 2](https://landaire.net/a-file-format-uncracked-for-20-years-part-2/).
Their reconstruction work concerns object loading/assets, not a completed native
game port. LIN is an ordered loading stream with implicit object dependencies;
the original loader is retained here. No wholesale conversion was attempted.
[unrealin](https://github.com/landaire/unrealin) and
[UE2OffsetDump](https://github.com/landaire/UE2OffsetDump) remain diagnostic
references; US-specific addresses were not applied to this European executable.

[SCDA-XBERecomp](https://github.com/TGP482/SCDA-XBERecomp) concerns Double Agent,
not SC1. [EnhancedSC](https://github.com/Joshhhuaaa/EnhancedSC) is the PC behavior
reference. [SwitchWakerHD](https://github.com/centollOS/SwitchWakerHD) uses a
different console/GPU architecture and was not needed for the selected path.

## Licenses

Burnout3/xboxrecomp authored code and the CPU backport are MIT; see
`src/LICENSE.xboxrecomp` and upstream `LICENSE`, `NOTICE`, `LICENSES/`.
The APU/NV2A components include xemu-derived LGPL-2.1+ material. Retain the exact
upstream source, license notices and applicable relinking/source obligations when
distributing binaries. Mesa/nxvk, glslang, SDL2, libnx and devkitPro retain their
own licenses and attribution. The existing SDK NOTICE is kept with the SDK.
Retail data and generated game code remain private and are not published.
