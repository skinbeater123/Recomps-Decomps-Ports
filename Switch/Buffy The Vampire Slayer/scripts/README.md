# Buffy probe scripts

Authored scripts for the feasibility audit. They read the private game files and write **only to the private workspace**; none of them emits game bytes to stdout except counts, names and hashes. Run Python with `-I`.

| Script | Purpose |
| --- | --- |
| `xbe_probe.py` | XBE header, certificate, sections, XDK library versions and named kernel imports as JSON |
| `map_to_tgp482.py` | Resolves TGP482 runtime symbol names from the disc's `final.map` (XDK 4432 has no TGP482 signatures) and writes a private `xbe_recomp` config. `--seed-functions` adds every map function entry; `--no-heuristics` turns off gap fill and pointer seeding |
| `compare_recomp_functions.py` | Counts how `xbe_recomp`'s discovered functions line up with the map's function entries |
| `make_a64_overlay.py` | devkitA64 GCC 16.1.0 ICE workaround for TGP482 `runtime/cpu` headers (same transform BLACK used) |
| `map_to_seeds.py` | Map function entries as sp00nznet `tools.disasm --seed-functions` JSON |
| `compare_sp00nznet_functions.py` | sp00nznet `functions.json` vs the map: starts found/missed/extra, ends exact/padding/short/overrun, and (with `xrefs.json`) whether short gaps hold branch targets |
| `apply_map_names.py` | Applies `tools.symbols.map_names resolve` output to a private `functions.json` with sp00nznet's own sanitiser |
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

sp00nznet pipeline (E5). `V` = a private venv Python with `capstone==5.0.6`; run from a `git archive` snapshot `S` of sp00nznet `f0f8a46`; `R` = `$P/sp00nznet-run`; `T` = this folder:

```bash
python -I "$T/map_to_seeds.py" "$D/final.map" "$D/Default.xbe" "$R/map_seeds.json"
cd "$S" && "$V" -m tools.xbe_parser "$D/Default.xbe" --json "$R/buffy_analysis.json" --quiet
"$V" -m tools.disasm "$D/Default.xbe" --analysis-json "$R/buffy_analysis.json" -o "$R/disasm_seeded" --seed-functions "$R/map_seeds.json" -v
"$V" -m tools.symbols.map_names resolve "$D/final.map" "$R/buffy_analysis.json" -o "$R/map_names.json"
"$V" -I "$T/apply_map_names.py" "$S" "$R/map_names.json" "$R/disasm_seeded/functions.json"
"$V" -m tools.func_id "$D/Default.xbe" --functions "$R/disasm_seeded/functions.json" --strings "$R/disasm_seeded/strings.json" --xrefs "$R/disasm_seeded/xrefs.json" -o "$R/func_id"
"$V" -m tools.abi_analysis "$D/Default.xbe" --functions "$R/disasm_seeded/functions.json" --identified "$R/func_id/identified_functions.json" --output-dir "$R/abi"
"$V" -m tools.recomp "$D/Default.xbe" --all --split 250 --functions "$R/disasm_seeded/functions.json" --labels "$R/disasm_seeded/labels.json" --identified "$R/func_id/identified_functions.json" --abi "$R/abi/abi_functions.json" --gen-dir "$R/gen" -o "$R/recomp_out"
python -I "$T/compare_sp00nznet_functions.py" "$R/disasm_seeded/functions.json" "$D/final.map" "$D/Default.xbe" "$R/disasm_seeded/xrefs.json"
```

Never copy generated configs, generated C++, objects or game files into this repository.
