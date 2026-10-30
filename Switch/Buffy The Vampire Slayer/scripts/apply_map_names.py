#!/usr/bin/env python3
"""Name sp00nznet functions.json entries from `tools.symbols.map_names resolve` output.

    python -I apply_map_names.py <xboxrecomp sdk> <map_names.json> <functions.json>

Uses the SDK's own ghidra_naming.merge_names sanitiser. Every name gets an _<ADDR>
suffix: the map names the title's own CRT (`_matherr`, `memcpy`, ...), and unsuffixed
those collide with the host CRT's declarations and symbols (MSVC C2371 on `_matherr`).
Rewrites functions.json in place (keeps a .bak); run it on a PRIVATE copy only.
"""
import json
import sys
from pathlib import Path


def main(argv):
    sdk, names_path, funcs_path = argv[1:4]
    sys.path.insert(0, sdk)
    from tools.ghidra_naming import merge_names as mn

    raw = json.loads(Path(names_path).read_text())
    final = {}
    for addr, name in sorted(raw.items()):
        a = mn.norm_addr(addr)
        n = mn.sanitize(name)
        if not n:
            continue
        final[a] = "%s_%s" % (n[:90], a[2:].upper())
    applied = mn.apply_to_functions_json(final, funcs_path)
    print(json.dumps({"map_names": len(raw), "sanitized": len(final), "applied_to_functions": applied}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
