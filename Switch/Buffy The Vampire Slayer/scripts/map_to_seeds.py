#!/usr/bin/env python3
"""Write sp00nznet `tools.disasm --seed-functions` JSON from Buffy's linker map.

    python -I map_to_seeds.py <final.map> <default.xbe> <out seeds.json>

Every map symbol flagged "f" in an executable XBE section becomes one seed
({"start": "0x...", "note": "final.map"}). These are linker-recorded entry points,
not inference, so sp00nznet's warning about mid-function seeds does not apply.
The output holds addresses only and belongs in the PRIVATE workspace.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_to_tgp482 import SYM_RE, xbe_sections  # noqa: E402


def main(argv):
    map_path, xbe_path, out_path = argv[1:4]
    secs, _ = xbe_sections(xbe_path)
    entries = set()
    for line in Path(map_path).read_text(errors="replace").splitlines():
        mm = SYM_RE.match(line)
        if not mm or mm.group(1) == "0000" or mm.group(5) != "f":
            continue
        n = int(mm.group(1), 16) - 1
        if n >= len(secs) or not secs[n][3] & 0x4 or secs[n][0] in (".rdata", ".data"):
            continue
        entries.add(secs[n][1] + int(mm.group(2), 16))
    seeds = [{"start": "0x%08X" % va, "note": "final.map"} for va in sorted(entries)]
    Path(out_path).write_text(json.dumps(seeds))
    print(json.dumps({"seeds": len(seeds)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
