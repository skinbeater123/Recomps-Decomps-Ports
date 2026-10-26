#!/usr/bin/env python3
"""Compare sp00nznet tools.disasm functions.json with the linker map's function entries.

    python -I compare_sp00nznet_functions.py <functions.json> <final.map> <default.xbe> [xrefs.json]

Starts: map entries found / missed, and detected functions the map does not list.
Ends: each found function's end against the next map symbol in its section:
  exact     end == next map symbol
  padding   end <  next map symbol and the gap is only int3/nop/zero bytes
  short     end <  next map symbol with real bytes in the gap (body cut early)
  overrun   end >  next map symbol (body runs into the next function)
"short" is split further: short_split_at_detected = the gap begins with another detected
function (the body continues there, e.g. a tail-jump alias), so no code is lost.
With xrefs.json, the remaining short gaps are split by whether any call/jump targets them:
unreferenced gaps are data (MSVC places switch tables after the body); referenced ones need review.
Prints counts only (JSON); no code or bytes.
"""
import json
import struct
import sys
from bisect import bisect_right
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_to_tgp482 import SYM_RE, xbe_sections  # noqa: E402

PAD = {0xCC, 0x90, 0x00}


def raw_reader(xbe_path):
    img = Path(xbe_path).read_bytes()
    base, = struct.unpack_from("<I", img, 0x104)
    num, hdr = struct.unpack_from("<II", img, 0x11C)
    spans = []
    for i in range(num):
        _, va, _, raw, rsize, _ = struct.unpack_from("<6I", img, hdr - base + i * 56)
        spans.append((va, raw, rsize))

    def gap_is_padding(lo, hi):
        for va, raw, rsize in spans:
            if va <= lo and hi <= va + rsize:
                return all(b in PAD for b in img[raw + lo - va:raw + hi - va])
        return False  # beyond raw data (virtual tail): not padding we can prove
    return gap_is_padding


def main(argv):
    funcs_path, map_path, xbe_path = argv[1:4]
    targets = []
    if len(argv) > 4:
        targets = sorted({int(x["to"], 16) for x in json.loads(Path(argv[4]).read_text())
                          if x.get("type") in ("call", "jump", "cond_jump")})
    secs, _ = xbe_sections(xbe_path)
    entries, symbols = set(), {}  # symbols: section index -> sorted code-symbol VAs
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
    sec_of = {}
    for n, vas in symbols.items():
        symbols[n] = sorted(vas)
        for va in vas:
            sec_of[va] = n

    funcs = json.loads(Path(funcs_path).read_text())
    if isinstance(funcs, dict):
        funcs = funcs.get("functions", list(funcs.values()))
    found = {int(f["start"], 16): f for f in funcs}
    gap_is_padding = raw_reader(xbe_path)

    ends = Counter()
    found_sorted = sorted(found)
    for va in entries & found.keys():
        n = sec_of[va]
        vas = symbols[n]
        i = bisect_right(vas, va)
        nxt = vas[i] if i < len(vas) else secs[n][1] + secs[n][2]
        end = int(found[va]["end"], 16)
        if end == nxt:
            ends["exact"] += 1
        elif end > nxt:
            ends["overrun"] += 1
        elif gap_is_padding(end, nxt):
            ends["padding"] += 1
        else:
            ends["short"] += 1
            j = bisect_right(found_sorted, end - 1)
            if j < len(found_sorted) and end <= found_sorted[j] < nxt and gap_is_padding(end, found_sorted[j]) or end in found:
                ends["short_split_at_detected"] += 1
            elif targets:
                k = bisect_right(targets, end - 1)
                key = "short_gap_branch_target" if k < len(targets) and targets[k] < nxt else "short_gap_unreferenced"
                ends[key] += 1
                ends[key + "_bytes"] += nxt - end

    extra = found.keys() - entries
    print(json.dumps({
        "detected_functions": len(found), "map_function_entries": len(entries),
        "map_entries_found": len(entries & found.keys()), "map_entries_missed": len(entries - found.keys()),
        "detected_extra_not_in_map": len(extra),
        "extra_on_unflagged_map_labels": len(extra & set(sec_of)),
        "extra_by_detection_method": dict(Counter(found[v].get("detection_method", "?") for v in extra).most_common()),
        "extra_by_section": dict(Counter(found[v].get("section", "?") for v in extra).most_common()),
        "end_vs_next_map_symbol": dict(ends),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
