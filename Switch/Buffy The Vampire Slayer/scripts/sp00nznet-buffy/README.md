# sp00nznet xboxrecomp adapters for Buffy (XDK 4432)

What it took to get the recompiled Europe XBE from boot to its title screen on Windows (E6 in the report). Everything here is authored code or a diff against MIT-licensed sp00nznet files (`f0f8a46`). Nothing here is generated from the game.

| File | Applies to | Why |
| --- | --- | --- |
| `0001-lifter-wbinvd-noop.patch` | `sdk/tools/recomp/lifter.py` | XDK 4432 `d3d8:dxgcreate.obj` runs `wbinvd` during device creation; the lifter had no rule for it |
| `0002-kernel-fsctl-dismount-success.patch` | `sdk/src/kernel/kernel_bridge.c` | `XFormatUtilityDrive` dismounts the cache partition; the stubbed `STATUS_NOT_SUPPORTED` failed the format and the installer showed the unrecoverable disc-error screen |
| `buffy_d3d_fence.c` | game project `src/` | Replaces `D3D::BlockOnTime` (`0x00596E60`) using the XDK 4432 device layout (`[0x5A29A0]`, time `+0x30`, semaphore `+0x34`) and hands the semaphore to the pushbuffer executor. Bind it with `--manual-functions` `{"0x00596E60": "Buffy_D3D_BlockOnTime_00596E60"}` |
| `0003-new-game-main-buffy.patch` | `templates/new-game/src/main.c` | Entry `0x00579EA2` (`mainCRTStartup_00579EA2` with map names), `game\` / `save\` paths, and an opt-in all-thread dbghelp stack sampler (`RECOMP_SAMPLE_SECS`) |
| `0004-new-game-cmake-buffy.patch` | `templates/new-game/CMakeLists.txt` | Points at the toolkit snapshot and `gen_v2`, and adds the fence adapter and `src/kernel` include |
| `build.cmd`, `run.ps1` | game project root | MSVC + Ninja build, and a bounded run that writes logs and flip BMPs to `runs\<stamp>\` and resets `save\` for first-boot conditions |

The function inputs come from `../map_to_seeds.py` and `../make_manual_seeds.py` (34 hand seeds: SEH `__finally` entries and `87disp` labels). Names come from `../apply_map_names.py`, whose `_<ADDR>` suffix keeps the title's CRT names off the host CRT's.

Keep the game copy, `save\`, generated code and runs in the private workspace. The game folder is copied, not linked, so no run can write to the originals.
