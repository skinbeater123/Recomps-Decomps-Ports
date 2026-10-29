# SC1 port status — 29 October 2026

**Original menu navigation and saving have been demonstrated on Switch.
Training-scene execution is demonstrated on Windows, with severe diagnostic
rendering defects. Playable training remains unverified.** The development NRO contains real lifted SC1 code and
the upstream Xbox runtime/NVK renderer. It is not a replacement-game demo.

## Console checkpoint — 29 October 2026

The owner tested NRO `e7082eb8b813`: original menu navigation and saving work
on Switch. Intro and training Bink playback show black frames/white flashes and
stuttering audio; loading is slow. Download Levels reportedly crashes, but the
supplied logs contain no diagnostic for that separate failure. Start Game ends
at original `HalReturnToFirmware(2)`, the same-image Xbox relaunch request.
The tested runtime calls normal `exit`, which Buffy's earlier console evidence
identifies as unsafe while guest threads still run. Buffy's internal reboot
lifecycle has now been adapted to SC1: retain the original 4096-byte launch
page, retire the old guest threads, restore entry-point memory and allocators,
reset runtime/device state and reenter the original Xbox entry point in the
same process. Two Windows menu-to-training runs retired all four old threads
(80 ms and 30 ms, with none left parked), closed 32 old handles and reached
the authentic CIA Training Farm briefing without a supervisor relaunch.
The second run accepted Start and resumed original training 3D submissions;
its displayed scene still has the established software-rendering corruption.
The adapted lifecycle still requires console testing. The earlier manual-restart `-O1` candidate is
retained at `private/artifacts/sc1-ed8ed0ef65b2`, with NRO SHA-256
`ed8ed0ef65b2110e8863e27c32e024efa135099ded6e990ded65c944c629e3ef`
and matching ELF SHA-256
`264623cc97f329944e2639b810d74efb173a38867197ad21b9b02bdc5d480d23`.
Its manifest also records the generated-source checksums. The shared launch-page
restore path was rebuilt and replayed successfully on the Windows host.

Builds now read `VERSION` and embed a UTC timestamp in the hbmenu title, with
the full version/timestamp/revision in logs and NRO/ELF filenames. The build
script retains matching artifacts and SHA-256 manifests under `private/artifacts`.

The supplied movie interval records about 4.9 FPS, game-thread load around 92%
of a core and no output-device underruns. It does not establish a single cause
of audio stutter. SC1 uses original Bink; BLACK's working path uses XMV/WMADEC,
and Buffy uses its own original decoder. SC1's existing NVK linear-texture
hash already includes the movie-update correction found in Buffy. The next
candidate uses `-O1` instead of `-O0` and Buffy's existing guest-priority handoff
setting; performance improvement remains unverified.

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

Current rebuilt NRO: **85,145,797 bytes**, `NRO0`; matching ELF verified as
AArch64 ELF64 PIE, generated with `-O0`. NRO SHA-256:
`943fc1f3808afc4f6ddb03e05b0e866d3bc0e2a7fba31992bc8cd49f99c0177f`.
Matching ELF SHA-256:
`8d3950f09e483eb5b11029fec59afe4fb58846b74b6d754d59754c925602e912`.
Both artifacts and a generated-source-set checksum manifest are retained at
`private/artifacts/sc1-943fc1f3808a/`. These artifacts include the root CRT fix,
IF/polling, OHCI, DMA semaphore, AC97 and observed Bink/input callback recovery.
All five focused regressions pass; all nine inventoried critical source hashes
were rechecked and matched. No Switch hardware run is implied.

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
failure, XDK input-driver initialization, D3D setup and the first GPU fences. No index or guest serializer
is overridden, and the original ordered LIN loader remains in use.

Independent checks preceding the fix found over 260,000 original archive reads
matching independently decompressed LIN bytes, and compact integers matching a
separate decoder. Instruction-level comparison of 61,878 recorded serializer
instructions against original x86 execution in Unicorn found no integer-register
or control-flow divergence. This is a narrow CPU diagnostic, not an original
Xbox or full-game emulator run; Unicorn is not a build/runtime dependency.

## Remaining work

Original XDK module initializers from the four-entry table at `0x00258DD4` are
now recovered. The Windows diagnostic host routes OHCI faults to the existing
device model; the original driver enables its periodic list and its ISR claims
interrupts. CLI/STI now update virtual EFLAGS.IF, and function-entry preemption
respects that mask. The actual lifted XPP CLI/read/STI window passes its focused
flag/preemption test. These runs use `RECOMP_NO_MIRRORS=1`; the earlier invalid
heap pointers no longer depend on desktop RAM aliases to remain accessible.

The observed XNET state callback and original GPU DPC are recovered. Windows
polling now releases the guest lock periodically, as Horizon polling already
did; the pause-only diagnostic branch prevented the GPU ISR from taking the
original NOP(40) trap. Poll yields and function-entry preemption respect IF.

The original command stream selects semaphore DMA handle 8, offset 0, then
releases 5. Its RAMHT/DMA descriptor maps that to physical `0x005DE000`; the
existing executor previously required a title-specific external semaphore pointer
and left the fence word at 3. Command-based DMA resolution now performs the
submitted write through the runtime's contiguous RAM window. The XDK also uses
clear-value registers to convey NOP(9) payload; these now latch from their GPU
methods. No guest pointer, fence value or completion is forced.

Execution proceeds to original draw submission (32 draws/128 indices observed),
framebuffer clears, controller-image loading and opening `videos/logos.bik`.
Early captures are black and report degenerate geometry. Later retained CPU
framebuffer captures contain authentic intro imagery, including Sam Fisher and
the title, with visible artifacts. These are movie frames, not menu images or
proof of completed menu rendering.

AC97 Reset Registers now completes on the actual MMIO write before the driver's
single status read. Background clearing lost against the original compiler-hoisted
read, leaving CL=2 forever at `0x00244FE3`; independent disassembly confirms the
lifted control flow is faithful. Byte/word/dword reset-write tests pass without
changing the original audio routine.

Original Bink decoding and its bounded pixel-conversion callback table have also
been recovered. A strict host run consumed the intro and returned to menu object
loading without the original compact-index crash. The original vtable methods `0x000E9180`/`0x000E3DA0` have been recovered and
executed. Property method `0x00103530` through vtable `0x00277984` slot `+0x1C` is also
recovered and executed. Loading continues through nested original object
serialization, then exhausts the Windows diagnostic executable's 1 MiB native
stack while the guest stack has used about 77 KiB of its 8 MiB allocation.
The retained native/guest backtrace names the original loading calls. An 8 MiB
host stack permits loading to finish and original script startup to run. The
existing Horizon bootstrap already uses a 16 MiB native game-thread stack.

Original core expression callbacks are recovered from initialized GNatives,
including assignment and context operations. The original actor movement/transform
callbacks execute. A host run submits 83 draws and captures the authentic SC1
loading screen with its title and progress bar. The original region update
callback `0x00088140`, called at `0x00082BBC`, now executes, followed by original
actor trace, string, state and animation callbacks.

The engine raises a C++ exception while looking up an XboxLive package. The
runtime previously returned from `RtlRaiseException` without dispatching it,
which led to a subsequent access violation. A host-tested implementation calls
the original guest handler and resumes its chosen continuation in the existing
lifted function. Landing support is limited to recognizable guest exception
frames; unsupported handlers and continuations fail explicitly. The focused
frame test covers nested frames, stack/target matching, lock-state restoration
and removal of stale frames. No XboxLive files are fabricated.

The host passed original `AActor::execPlayAnim`, rotator interpolation,
sound-duration and the unaligned class-construction callback `0x0016129F`.
DirectSound then posted a DSP command and waited at `0x0023F685`. The approved
runtime's passthrough DSP does not run the effects program; its existing command
acknowledgement is now registered from the scratch pointer calculated by the
original routine. No fixed guest address is used, and DSP effects remain
unimplemented. This lets startup continue, but is not evidence of accurate
audio processing.

The next host wait at `0x000220C2` polled a terminated worker's exit status.
The runtime had discarded the worker's guest object while its handle remained
open, then returned success with a null object. Thread references now keep a
guest-visible object until both handle and references are released; the
original status polling proceeds. Original `AActor::execLockRootMotion`
`0x000CB920` and its branch arm `0x00080874` also execute; menu configuration
and the original menu loop now continue beyond both.

The original main menu now renders and accepts controller navigation on the
Windows diagnostic host. A recorded run moved the selection from Start Game to
Settings, then opened the original Settings screen. The same run navigated the
original profile keyboard and backed out through Profile Settings. The Windows
software diagnostic renderer needed the observed texture/diffuse combiner and
additive and color-multiply blend factors; unsupported combinations remain
outside that narrow correction. The resulting frames still show visual artifacts.

The host saved and selected an original profile, opened the training Bink and
displayed the original training loading screen. One run reached an Xbox quick
reboot into the same XBE with training launch data, which the current runtime
treated as an exit. A later run stalled earlier at `0x001F007B`, waiting for a
pending display flip after an early movie skip. A Windows diagnostic process
handoff then preserved the original 4 KiB launch page across a fresh process;
the restarted guest loaded original training assets, passed recovered targets
`0x00061F80` and `0x00031520`, and displayed the CIA Training Farm briefing.
After Start, original callbacks `0x000C6580`, `0x00138060`, `0x000C66E0` and
`0x00137070`, `0x00064520`, `0x000660B0`, `0x00103070`, `0x00101200` and
`0x00103FE0`, `0x00103330`, `0x00076F70`, `0x0014CB70`, `0x0014DCA0` and
`0x0014DDD0`, `0x00077300`, `0x00023FF0` and `0x00032BC0` executed. The
original training scene submitted 3D geometry; a captured host frame is severely
corrupted and does not demonstrate playable or visually accurate gameplay. The
original worker callbacks `0x0018B510`, `0x0018B0F0` and `0x00185090` executed.
A subsequent bounded 240-second host run continued submitting original 3D
geometry without another missing guest call, but the severely corrupted frames
do not establish playable training. A later trace confirms that the original
scene enables depth testing and depth writes, which the host software rasterizer
does not implement. An opt-in host diagnostic now captures PCRTC-selected scanout
at display flips using the original display pitch. It confirms the real training
briefing and subsequently shows severe 3D corruption on the actual 640x480
display surface. The previous 64x64 screenshots were offscreen targets. Frames
change while scripted stick input is delivered, but neither player movement nor
camera response is established by those corrupted images. SC1 now reports original flip retirements to the
existing runtime stall mechanism and coordinates PGRAPH and vblank handlers at
dispatch level. A bounded 240-second direct training run did not report a flip-stall timeout;
longer and native validation remain open.
The diagnostic framebuffer intermittently remained black at the briefing even
while original input polling responded to Start.
Buffy's existing implementation preserves the same launch page and coordinates
old threads, guest memory and devices during an in-process reboot. Its Eden logs
show that reboot restarting Buffy. SC1 now uses that lifecycle with Windows
OHCI checkpoint exclusions, bounded cancellable guest waits, SC1 thread-object
cleanup and exception-chain reset. Its native Switch verification remains open.

The milestone NRO SHA-256 is
`38b8b9181ec670f95f4946eb43965afc653f4ab65c3f3c236c2a529625aa1f2a`;
its matching ELF SHA-256 is
`4784a3fd8f35abf9dc00756c131c82dcb79371b9a9dad3cf19d3a1f531b02261`.
Both and the generated-set checksum are retained in
`private/artifacts/sc1-38b8b9181ec6`. The NRO predates the later Windows-only
software-renderer corrections. Eden launched this NRO and the guest opened the
original menu assets and Bink videos, but guest Vulkan device enumeration failed
with `no Vulkan device` and the log recorded zero rendered frames. Eden itself
detected the host GPU; the cause of the guest enumeration failure remains open.
A separate successful Buffy Eden guest log identifies EGL/OpenGL, not SC1's
static NVK driver; the comparison does not establish why SC1 enumeration failed.
No Eden menu rendering or physical Switch execution of this NRO is demonstrated.

A focused Eden comparison identified a guest NVK compatibility requirement:
explicit `NVK_I_WANT_A_BROKEN_VULKAN_DRIVER=1` made the retained NRO enumerate
Tegra X1 and create an NVK swapchain. Without it, enumeration reported no device.
Both Eden CLI and GUI then terminated with access violation `0xC0000005` in
the same emulator core instruction, reading address `0x28` with a null internal
object (CLI offset `0x2270D5`, GUI `0x605745`); disabling optional instancing did
not prevent the crash. Guest-rendered frames have not been confirmed. The SC1
Switch initialization now enables the NVK setting unless the user supplies it.

The new consolidated NRO SHA-256 is
`e7082eb8b81301ec74576181292a8fc788b84382afffccf453d39520886f17ed`;
its matching ELF SHA-256 is
`233a6f82bd8184fa1e84cc507783ce28cce97e90afc16eeed87ccb28ac08736b`.
Both are retained in `private/artifacts/sc1-e7082eb8b813`. The NRO has not yet
been run: the existing Eden session belongs to Buffy and must not be disturbed.
The previous milestone is retained independently.

Opt-in Windows experiments for observed Z24S8 depth and negative wrapped texture
coordinates pass focused arithmetic tests and each visibly changes the scanout,
but neither alone nor together produces recognisable training graphics. They are
not evidence of accurate rendering and are disabled by default. An original
`AActor::execMove` probe recorded six actors during initial loading, with no
further calls during stick input. The sampled actor identities are not established;
movement and camera response remain unverified.

The correct Switch deployment
storage is accessed at the owner-specified network endpoint. The original
extracted files are staged there with ISO excluded. All 680 file sizes and nine
pinned critical hashes were checked. A baseline NRO was uploaded and its hash
verified by reading it back. No SC1 console launch or
Horizon rendering is demonstrated. Original shadows, dynamic lighting,
night/thermal vision, accurate movie playback/audio, gamepad behavior and mission
progression remain unverified.

Public research is exported into the existing `Switch/Splinter Cell` directory.
The local working repository and public research repository have unrelated Git
histories, so publication uses a clean commit based on public `main`, with only
allowlisted SC1 authored files. BLACK/Buffy work and staged BLACK changes are excluded.
