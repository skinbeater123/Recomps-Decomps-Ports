# Buffy probe scripts

Authored scripts for the feasibility audit. They read the private game files and write **only to the private workspace**; none of them emits game bytes to stdout except counts, names and hashes. Run Python with `-I`.

| Script | Purpose |
| --- | --- |
| `xbe_probe.py` | XBE header, certificate, sections, XDK library versions and named kernel imports as JSON |
| `map_to_tgp482.py` | Resolves TGP482 runtime symbol names from the disc's `final.map` (XDK 4432 has no TGP482 signatures) and writes a private `xbe_recomp` config. `--seed-functions` adds every map function entry; `--no-heuristics` turns off gap fill and pointer seeding |
| `compare_recomp_functions.py` | Counts how `xbe_recomp`'s discovered functions line up with the map's function entries |
| `make_a64_overlay.py` | devkitA64 GCC 16.1.0 ICE workaround for TGP482 `runtime/cpu` headers (same transform BLACK used) |
| `Build-RecompHost.cmd` + `host-tools/` | Builds only `xbe_recomp`/`xbe_symbols` from TGP482 into `<workspace>/Projects/Buffy The Vampire Slayer/private/build/host` |

Reproduce (Git Bash; `WS` = workspace root, `D` = extracted game folder, `SDK` = TGP482 checkout, `P` = `$WS/Projects/Buffy The Vampire Slayer/private`):

```bash
python -I xbe_probe.py "$D/Default.xbe" --kernel-names
cmd //c Build-RecompHost.cmd
python -I map_to_tgp482.py "$D/final.map" "$D/Default.xbe" "$SDK" "$P/probe/config/buffy_mapsonly.toml" --seed-functions --no-heuristics --report "$P/probe/e1b_map_symbols.json"
"$P/build/host/xbe_recomp.exe" "$P/probe/config/buffy_mapsonly.toml" "$D/Default.xbe" "$P/probe/generated/buffy_mapsonly"
python -I compare_recomp_functions.py "$P/probe/generated/buffy_mapsonly/x86_func_mapping.cpp" "$D/final.map" "$D/Default.xbe"
python -I make_a64_overlay.py "$SDK/runtime/cpu" "$P/probe/a64/overlay/cpu"
aarch64-none-elf-g++ -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE -std=gnu++20 -O2 -c \
  -I "$P/probe/a64/overlay" -I "$SDK/runtime" "$P/probe/generated/buffy_mapsonly/x86_recomp.0.cpp" -o p0.o
```

Never copy generated configs, generated C++, objects or game files into this repository.
