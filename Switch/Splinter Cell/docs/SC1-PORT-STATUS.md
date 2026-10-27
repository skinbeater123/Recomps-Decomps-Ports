# SC1 port status — 27 October 2026

**Native ARM64 NRO linked; original engine/loader startup demonstrated on Windows.
No Switch execution, authentic rendered menu, training or interactive gameplay
has been demonstrated.** The development NRO contains real lifted SC1 code and
the upstream Xbox runtime/NVK renderer. It is not a replacement-game demo.

## Executable and disc

- Retail Europe/rest-of-world certificate mask `0x4`, title `5553000C`, XDK 4928.
- Build timestamp: 5 November 2002, 18:35:12 UTC; entry `0x001772D7`.
- `default.xbe`: 3,092,480 bytes, 31 sections, 148 kernel imports.
- SHA-256: `d9cc30aa5c391d0e0ae6291e086a3b318b5a8f421b107b75266544d47254a282`.
- 681 source files; no MAP/PDB/SYM/DBG found. Inventory readability check reads
  first/last bytes, with full hashes of XBEs and menu/training LIN files.
- Training source: `LMaps/001_Training/0_0_2_Training.lin` (6,511,440 bytes),
  `0_0_3_Training.lin` (6,924,726 bytes), and `common.lin` (3,118,597 bytes).
- Source dump is untouched. Complete filenames and binary-derived analysis stay
  in ignored `private/`; no complete asset conversion was attempted.

## Demonstrated original execution

The full Windows executable, using the same generated code as the Switch target,
has entered the original XBE startup, exercised CRT CPU feature probing, initialized
guest threading/audio services, created the original title metadata, accessed
Xbox cache partitions, initialized SC1's binned allocator and built the original
level-option table. It opens `LMaps/000_menu/common.lin`, reads 131,072 bytes
through the original loader, opens `UW.ini`, and reads its 2,750 bytes. It also
opens `menu.lin`, loads native classes and package objects, initializes the
original render device and XDK D3D state, and registers/executes the original
GPU ISR at `0x001F6870`. These are host startup observations, not GPU rendering
or a completed menu.

This establishes real startup and asset access, not successful completion of LIN
deserialization. A bounded capture of 31 original decompressor calls matched
Python zlib byte for byte. Audio initialization does not establish
correct or audible game audio. Windows execution does not establish Horizon behavior.

Measured integration corrections:

1. Backported existing CPUID/PUSHFD/POPFD and OF/PF support; the actual original
   CRT CPU probe passes uncached/cached paths with expected stack/register state.
2. Recovered observed allocator/stream indirect-call targets, then scoped native
   class-registration callback discovery to avoid one rebuild per missing callback.
3. Corrected new virtual-allocation alignment and page-size reporting. Before:
   the original option array lost its first entry on reallocation and constructed
   a corrupt LIN path. After: `000_menu` is retained and the original common LIN
   opens successfully. Guest filenames and allocator results are not hardcoded.
4. Adapted the existing loaderless Horizon NVK SDK's ICD dispatch and unified-heap
   allocation policy; moved caches/logs/saves into the SC1 application directory.
5. Recovered verified object-vtable methods and original XDK render-state handlers;
   implemented WBINVD as coherent guest-memory ordering, with renderer fences
   remaining in the existing backend. No guest functions are replaced.

## Build and evidence

Build command and deployment are in [README](../README.md). Local outputs:

- `build/switch/sc1.nro` — native development executable, title takeover required.
- `build/switch/sc1.elf` — AArch64 ELF64 PIE; retain with the corresponding NRO.
- `build/host/sc1.exe` — optional Windows differential diagnostic, unoptimized.
- `logs/build.log`, `logs/build-host.log`, `logs/host-run.log` — private build/run evidence.
- `private/lift/summary.json` — generator counts and unsupported sites; counts are
  emission statistics, not a correctness percentage.

Unsupported instructions and unresolved direct/indirect calls abort with the
guest address and recent call/stack state. Existing runtime API coverage and
shader coverage remain title-dependent. Original LIN loading is preserved.
The supplied NRO uses `-O0` for bring-up; it is not a performance result.

Retained baseline build: **84,625,605 bytes**, `NRO0`; ELF verified as AArch64 ELF64 PIE.
NRO SHA-256:
`ea01c973836e111507385437ae771bd4de167be5feca4b507ba20eeaef1caaef`.
The baseline NRO and matching ELF are retained locally under
`private/artifacts/baseline-ea01c973/`. Generation counts are not runtime coverage.
The original CPU probe and CRT-copy regressions pass. All nine initially
inventoried critical source hashes matched at the previous artifact check.

Optional host diagnosis: configure `-DSC1_ABI_CHECK=ON` in `build/host` to enable
the runtime's existing register/stack checks. The retained checked run reports
four nonstandard CRT/kernel call contracts before engine loading; none of these
checks identifies the later loader failure's cause. Temporary per-read tracing
and decompressor captures are absent from the delivered generated sources/NRO.

## Resolved object-index failure

The previous host failure was an invalid guest read at original instruction
`0x000397F1`, after compact index `0xF94A5E62` is decoded by `0x00047C70` and
used by `0x00039840`/`0x000397E0` while loading an object reference from serialized
Unreal bytecode (`0x0002ABC0`). The observed nested archive cursor before that
index is `0x0010E089`. The bad index causes an out-of-range import-table access.
The earlier missing-method blocker at `0x0002C230` is resolved.

The root cause is a stale, misaligned instruction retained while decoding an
embedded CRT memcpy jump table. At `0x001B197C`, the original MOV is three bytes;
an erroneous OR at `0x001B197E` survived inside it and was also lifted. That OR
changed a free-list next pointer from `...0690` to `...4690`. The allocator then
read pathname text as free-block metadata and returned invalid pointers that
desktop RAM mirrors partly concealed. The later object-index crash was a symptom.

The narrow upstream resynchronization fix removes these overlapping decodes.
The actual CRT routine failed its zero-byte copy/guard test before the fix and
passes 12,336 cases afterward. Full host execution passes the previous index
failure and reaches XDK input-driver initialization. No index or guest serializer
is overridden, and the original ordered LIN loader remains in use.

Independent checks preceding the fix found over 260,000 original archive reads
matching independently decompressed LIN bytes, and compact integers matching a
separate decoder. Instruction-level comparison of 61,878 recorded serializer
instructions against original x86 execution in Unicorn found no integer-register
or control-flow divergence. This is a narrow CPU diagnostic, not an original
Xbox or full-game emulator run; Unicorn is not a build/runtime dependency.

## Remaining work

The next observed stop is unresolved XDK module initializer `0x00258F98`, called
at `0x0025971C` from the original four-entry module table. Continue those original
driver callbacks, then verify successful menu deserialization and rendering.

Validate this same application on Switch hardware. No connected
Switch USB device or SD volume was identified during this pass; no transfer was
attempted. Original shadows, dynamic lighting, night/thermal vision, Bink movies,
audio, gamepad behavior and mission progression remain unverified.

Public research is exported into the existing `Switch/Splinter Cell` directory.
The local working repository and public research repository have unrelated Git
histories, so publication uses a clean commit based on public `main`, with only
allowlisted SC1 authored files. BLACK/Buffy work and staged BLACK changes are excluded.
