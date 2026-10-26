#!/usr/bin/env python3
"""Compare TGP482 xbe_recomp's discovered functions with the linker map's function entries.

    python -I compare_recomp_functions.py <generated dir>/x86_func_mapping.cpp <final.map> <default.xbe>

Prints counts only (JSON): map entries found, map entries missed, and analysis entries the
map does not list (candidate data-as-code or compiler-internal labels). No code or bytes.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_to_tgp482 import SYM_RE, xbe_sections  # noqa: E402


def main(argv):
    mapping, map_path, xbe_path = argv[1:4]
    found = {int(m, 16) for m in re.findall(r"\{0x([0-9A-F]+)u, sub_", Path(mapping).read_text())}
    secs, _ = xbe_sections(xbe_path)
    entries, labels = set(), set()
    for line in Path(map_path).read_text(errors="replace").splitlines():
        mm = SYM_RE.match(line)
        if not mm or mm.group(1) == "0000":
            continue
        n = int(mm.group(1), 16) - 1
        if n >= len(secs) or not secs[n][3] & 0x4 or secs[n][0] in (".rdata", ".data"):
            continue
        va = secs[n][1] + int(mm.group(2), 16)
        (entries if mm.group(5) == "f" else labels).add(va)
    extra = found - entries
    print(json.dumps({
        "recomp_functions": len(found), "map_function_entries": len(entries),
        "map_entries_found": len(entries & found), "map_entries_missed": len(entries - found),
        "recomp_extra_not_in_map": len(extra),
        "recomp_extra_matching_unflagged_map_labels": len(extra & labels),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
