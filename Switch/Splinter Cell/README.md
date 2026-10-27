# Splinter Cell (2002) — native Switch integration

European retail Xbox executable, sp00nznet x86-to-C generation, and the
Burnout3/NFSU2 Horizon runtime with its NV2A Vulkan renderer. This is an early
development integration. **Menu, training and gameplay are not demonstrated.**
See [actual status](docs/SC1-PORT-STATUS.md) and [source pins](docs/SC1-REUSE-SOURCES.md).

The local project is `Projects/Splinter Cell`; the public research copy belongs
in the existing `Switch/Splinter Cell` directory. Scripts find their project
from their own location. No retail files or executable-derived code are public.

## Generate and build

Use Windows Python 3.10+ with Capstone 5 (the verified installation has 5.0.7),
devkitPro at `C:\Programming\devkitPro`, switch-sdl2, and the existing BLACK
self-contained Horizon NVK and glslang SDKs. The scripts reuse these installations.
The NVK archive is verified by SHA-256. Different SDK packaging needs an explicit
integration change; desktop Vulkan libraries cannot replace the Horizon SDK.

Put the original extracted disc in `Game Files/`. This directory is source
material and is excluded from Git. Required `default.xbe` SHA-256:

`d9cc30aa5c391d0e0ae6291e086a3b318b5a8f421b107b75266544d47254a282`

From PowerShell in the project directory:

```powershell
python scripts/inventory.py
python scripts/generate.py
./scripts/Build.ps1 -Jobs 2 -Optimization '-O0'
```

`-O0` is for diagnosis; `-O1` is the default for normal builds. Generation includes
every discovered section, ABI recovery, measured indirect-call seeds, and MMIO
accessors for DSOUND/XPP/D3D/XGRPH. It writes all analysis and generated output
outside the original disc directory. `--lift-only` reuses existing discovery/ABI
after changing a generator patch. It must not be used after changing seeds.

Output: `build/switch/sc1.nro`. Build.ps1 prints its SHA-256. The application
also verifies the supplied XBE hash before entering lifted code. Unresolved
direct/indirect calls and unsupported instructions stop with diagnostics.
No Burnout gameplay overrides, copied function addresses or logo are installed.

## Deploy a development build

```text
sdmc:/switch/splintercell/sc1.nro
sdmc:/switch/splintercell/sc1_env.txt       optional runtime settings
sdmc:/switch/splintercell/game/default.xbe
sdmc:/switch/splintercell/game/LMaps/...
sdmc:/switch/splintercell/game/Sounds/...
sdmc:/switch/splintercell/game/Videos/...
sdmc:/switch/splintercell/game/...         remaining extracted disc files
sdmc:/switch/splintercell/logs/sc1.log
sdmc:/switch/splintercell/save/...
```

Preserve the extracted layout and names; copying the ISO is unnecessary. Launch
with Atmosphère R title takeover for full memory. Before launch, compare the
copied NRO hash with the build hash and copied default.xbe with the hash above.
No SD transfer or hardware run is implied by a successful build.

For diagnosis, put `RECOMP_QUIET=0` and `RECOMP_WATCHDOG_SECS=10` on separate
lines in `sc1_env.txt`. Unsupported sites stop deliberately: preserve the log,
NRO checksum and ELF from the same build. The upstream environment variable
names are retained for runtime compatibility. Controls use the upstream Xbox
gamepad mapping (Switch buttons by label); SC1 gameplay controls remain untested.

## Optional host differential diagnosis

```powershell
./scripts/Build-Host.cmd
python scripts/check_cpu_probe.py
python scripts/run_host.py --seconds 30
```

This uses the same generated functions with the upstream Windows runtime.
The bounded run copies the extracted disc into ignored `private/host-data/game`
(approximately 4 GB), saves under `private/host-data/save`, and writes
`logs/host-run.log`. It does not run against the source dump. The CPU regression
extracts and executes the actual lifted SC1 CRT routine locally; no proprietary
body is stored in the test script or public repository.
