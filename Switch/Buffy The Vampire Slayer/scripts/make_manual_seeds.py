#!/usr/bin/env python3
"""Hand seeds sp00nznet's disassembler misses on Buffy, derived from the map and the image.

    python -I make_manual_seeds.py <functions.json> <final.map> <default.xbe> <out.json>

Two kinds, both verified rather than inferred:

1. SEH __finally entries. MSVC places a __try/__finally termination handler after
   the function body: the normal path `call`s its second half, and _local_unwind
   enters at its first instruction through the scope table. That first
   instruction is never a call target, so the disassembler misses it. A seed is
   written only when the uncovered gap start is referenced from .rdata as a scope
   table entry {enclosing, filter = 0, handler}.
2. LIBCMT 87disp.obj labels. Assembler x87 dispatch entry points (__rtonepop,
   ...) that the map lists without the "f" flag and math helpers tail-jump into.

Output: [{"start": "0x...", "note": ...}] for tools.disasm --seed-functions.
"""
import json
import struct
import sys
from bisect import bisect_right
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_to_tgp482 import SYM_RE, xbe_sections  # noqa: E402
from compare_sp00nznet_functions import raw_reader  # noqa: E402


def main(argv):
    funcs_path, map_path, xbe_path, out_path = argv[1:5]
    secs, _ = xbe_sections(xbe_path)
    img = Path(xbe_path).read_bytes()
    base, = struct.unpack_from("<I", img, 0x104)
    num, hdr = struct.unpack_from("<II", img, 0x11C)
    rdata = None
    for i in range(num):
        _, va, _, raw, rsize, name_addr = struct.unpack_from("<6I", img, hdr - base + i * 56)
        n = name_addr - base
        if img[n:img.index(b"\0", n)] == b".rdata":
            rdata = img[raw:raw + rsize]
    scope_handlers = set()
    for o in range(8, len(rdata) - 3, 4):
        if struct.unpack_from("<I", rdata, o - 4)[0] == 0:
            scope_handlers.add(struct.unpack_from("<I", rdata, o)[0])

    entries, symbols, labels_87 = set(), {}, []
    for line in Path(map_path).read_text(errors="replace").splitlines():
        mm = SYM_RE.match(line)
        if not mm or mm.group(1) == "0000":
            continue
        n = int(mm.group(1), 16) - 1
        if n >= len(secs) or not secs[n][3] & 0x4 or secs[n][0] in (".rdata", ".data"):
            continue
        va = secs[n][1] + int(mm.group(2), 16)
        symbols.setdefault(n, set()).add(va)
        if mm.group(5) == "f":
            entries.add(va)
        elif mm.group(7) == "LIBCMT:87disp.obj":
            labels_87.append((va, mm.group(3)))
    sec_of = {}
    for n, vas in symbols.items():
        symbols[n] = sorted(vas)
        for va in vas:
            sec_of[va] = n

    funcs = json.loads(Path(funcs_path).read_text())
    found = {int(f["start"], 16): f for f in funcs}
    ranges = sorted((int(f["start"], 16), int(f["end"], 16)) for f in funcs)
    starts = [r[0] for r in ranges]
    pad = raw_reader(xbe_path)

    def covered(a):
        i = bisect_right(starts, a) - 1
        return i >= 0 and ranges[i][0] <= a < ranges[i][1]

    seeds = []
    for va in sorted(entries & found.keys()):
        vas = symbols[sec_of[va]]
        i = bisect_right(vas, va)
        if i >= len(vas):
            continue
        nxt, end = vas[i], int(found[va]["end"], 16)
        if end >= nxt or pad(end, nxt):
            continue
        a = end
        while a < nxt and (covered(a) or pad(a, a + 1)):
            a += 1
        if a < nxt and a not in found and a in scope_handlers:
            seeds.append({"start": "0x%08X" % a, "note": "SEH __finally handler entry from .rdata scope table"})
    for va, name in labels_87:
        seeds.append({"start": "0x%08X" % va, "note": "LIBCMT 87disp.obj x87 dispatch label %s (map, no f flag)" % name})
    Path(out_path).write_text(json.dumps(seeds, indent=1))
    print(json.dumps({"seh_finally": sum(s["note"].startswith("SEH") for s in seeds),
                      "x87_dispatch_labels": len(labels_87), "total": len(seeds)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
