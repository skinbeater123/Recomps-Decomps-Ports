#!/usr/bin/env python3
"""Resolve TGP482 XboxXBERecomp [symbols] names from Buffy's shipped MSVC linker map.

TGP482's xbe_symbols only knows XDK 4831/5849 signatures, and Buffy is XDK 4432,
so it refuses the image. The retail disc, however, ships `final.map`, which names
every public function. This script maps the names TGP482's runtime replaces onto
XBE virtual addresses and writes a recompiler config into a PRIVATE directory.

    python -I map_to_tgp482.py <final.map> <default.xbe> <tgp482 sdk dir> <out.toml> [--report out.json]
        [--seed-functions] [--no-heuristics]

--seed-functions adds every map code symbol as a [functions] entry, so analysis starts from the
linker's ground truth; --no-heuristics also turns off TGP482's gap fill and pointer seeding.

MAP section N is XBE section N-1 (imagebld keeps the section order), so
xbe_va = xbe_section[N-1].vaddr + offset. The map's entry point is checked
against the XBE header's decoded entry point before anything is written.
Only counts and names go to the report; addresses stay in the private config.
"""
import json
import re
import struct
import sys
from pathlib import Path

SYM_RE = re.compile(r"^\s*([0-9a-f]{4}):([0-9a-f]{8})\s+(\S+)\s+([0-9a-f]{8})\s+(f?)\s*(i?)\s*(\S+)\s*$", re.I)
ENTRY_RE = re.compile(r"entry point at\s+([0-9a-f]{4}):([0-9a-f]{8})", re.I)
RETAIL_ENTRY_KEY = 0xA8FC57AB

# TGP482 names whose map spelling is not derivable by the generic rules below.
# Each was chosen by reading the map's mangled name, not by guessing addresses.
ALIASES = {
    "_CIacos": ["__CIacos"],
    "_CIasin": ["__CIasin"],
    "crt_acos": ["_acos"], "crt_asin": ["_asin"], "crt_atan": ["_atan"],
    "crt_cos": ["_cos"], "crt_log": ["_log"], "crt_log10": ["_log10"],
    "crt_pow": ["_pow"], "crt_sin": ["_sin"], "crt_sqrt": ["_sqrt"], "crt_tan": ["_tan"],
}

# Libraries a name belongs to, used to separate "Buffy does not link this" from "not found".
LIB_PREFIX = [
    ("Bink", "BINK"), ("WSA", "XNET"), ("XNet", "XNET"), ("XOnline", "XONLINE"),
    ("accept", "XNET"), ("bind", "XNET"), ("closesocket", "XNET"), ("connect", "XNET"),
    ("getsock", "XNET"), ("ioctlsocket", "XNET"), ("listen", "XNET"), ("recv", "XNET"),
    ("select", "XNET"), ("send", "XNET"), ("setsockopt", "XNET"), ("shutdown", "XNET"),
    ("socket", "XNET"),
]


def xbe_sections(path):
    img = Path(path).read_bytes()
    base, = struct.unpack_from("<I", img, 0x104)
    entry_enc, = struct.unpack_from("<I", img, 0x128)
    num, hdr = struct.unpack_from("<II", img, 0x11C)
    secs = []
    for i in range(num):
        h = hdr - base + i * 56
        flags, vaddr, vsize, _, _, name_addr = struct.unpack_from("<6I", img, h)
        n = name_addr - base
        secs.append((img[n:img.index(b"\0", n)].decode("latin-1"), vaddr, vsize, flags))
    return secs, entry_enc ^ RETAIL_ENTRY_KEY


def plain_names(mangled):
    """Candidate TGP482-style names for one map symbol."""
    out = set()
    m = mangled
    if m.startswith("__imp_"):
        return out
    if m.startswith("?"):
        # ?Method@Class@Namespace@@...  ->  Class_Method, Namespace_Method, Namespace_Class_Method
        head = m[1:].split("@@", 1)[0]
        parts = [p for p in head.split("@") if p]
        if not parts or parts[0].startswith("?"):
            return out
        meth, scopes = parts[0], parts[1:]
        if scopes:
            out.add(scopes[0] + "_" + meth)
            out.add("_".join(reversed(scopes)) + "_" + meth)
        else:
            out.add(meth)
        return out
    s = re.sub(r"@\d+$", "", m)
    out.add(s)
    if s.startswith("_"):
        out.add(s[1:])
    if s.startswith("@"):
        out.add(s[1:])
    return out


def main(argv):
    map_path, xbe_path, sdk, out_path = argv[1:5]
    report_path = argv[argv.index("--report") + 1] if "--report" in argv else None
    seed = "--seed-functions" in argv
    no_heur = "--no-heuristics" in argv
    secs, xbe_entry = xbe_sections(xbe_path)

    text = Path(map_path).read_text(errors="replace")
    em = ENTRY_RE.search(text)
    esec, eoff = int(em.group(1), 16), int(em.group(2), 16)
    map_entry = secs[esec - 1][1] + eoff
    if map_entry != xbe_entry:
        print("map entry %08X != xbe entry %08X: wrong map for this image" % (map_entry, xbe_entry), file=sys.stderr)
        return 2

    by_name = {}       # candidate name -> set of (va, mangled, is_func, lib)
    code_vas = set()   # every map symbol in an executable XBE section, flagged as a function
    publics = 0
    for line in text.splitlines():
        mm = SYM_RE.match(line)
        if not mm or mm.group(1) == "0000":
            continue
        sec, off = int(mm.group(1), 16), int(mm.group(2), 16)
        if sec - 1 >= len(secs):
            continue
        publics += 1
        va = secs[sec - 1][1] + off
        # assembler CRT labels carry no "f" flag, so code-section membership also counts
        mangled, obj = mm.group(3), mm.group(7)
        is_func = mm.group(5) == "f" or bool(secs[sec - 1][3] & 0x4 and secs[sec - 1][0] not in (".rdata", ".data"))
        lib = obj.split(":")[0] if ":" in obj else "<game>"
        if mm.group(5) == "f" and secs[sec - 1][3] & 0x4 and secs[sec - 1][0] not in (".rdata", ".data"):
            code_vas.add(va)
        for c in plain_names(mangled) | {mangled}:
            by_name.setdefault(c, set()).add((va, mangled, is_func, lib))

    wanted = []
    for build in sorted(p.name for p in (Path(sdk) / "xdk").iterdir() if p.is_dir()):
        sig = (Path(sdk) / "xdk" / build / "signatures.toml").read_text()
        block = re.split(r"^\[symbols\]\s*$", sig, maxsplit=1, flags=re.M)[1]
        block = re.split(r"^\[anchors\]\s*$", block, maxsplit=1, flags=re.M)[0]
        wanted += re.findall(r"^([A-Za-z_][A-Za-z_0-9]*)\s*=", block, re.M)
    wanted = sorted(set(wanted))

    resolved, ambiguous, missing, not_linked = {}, {}, [], []
    for name in wanted:
        hits = set()
        for cand in [name] + ALIASES.get(name, []):
            hits |= {h for h in by_name.get(cand, ()) if h[2]}
        vas = {h[0] for h in hits}
        if len(vas) == 1:
            va = vas.pop()
            resolved[name] = (va, sorted({h[1] for h in hits}), sorted({h[3] for h in hits}))
        elif len(vas) > 1:
            ambiguous[name] = sorted({h[1] for h in hits})
        else:
            lib = next((l for p, l in LIB_PREFIX if name.startswith(p)), None)
            (not_linked if lib else missing).append(name)

    # For each miss, the XDK-library functions sharing its method stem: an older API variant
    # (GetRenderTarget for GetRenderTarget2) means the host needs a 4432 adapter, not just an address.
    near = {}
    for name in missing:
        stem = re.sub(r"(NotInline|Fast|Ex|\d)+$", "", name.split("_", 1)[-1])
        stem = re.sub(r"^(SetRenderState|SetTextureState)_?", "", stem) or stem
        cands = sorted({h[1] for c, hs in by_name.items() if stem and stem in c
                        for h in hs if not h[1].startswith("??_C@") and h[3] in ("d3d8", "dsound", "xapilib", "LIBCMT", "d3dx8", "xgraphics")})
        if cands:
            near[name] = cands[:4]

    code_secs = [s[0] for s in secs if s[3] & 0x4 and not s[0].startswith("$$") and s[0] not in (".rdata", ".data", "DOLBY")]
    lines = ["# PRIVATE: generated from Buffy's final.map by map_to_tgp482.py. Do not publish.",
             "[xbe]", 'path = "assets/default.xbe"', "title = 0x45410012", "entry = 0x%08X" % xbe_entry,
             'out = "generated/buffy"', 'library = "Buffy.dll"', "partitions = 128",
             "code_sections = [%s]" % ", ".join('"%s"' % s for s in code_secs)]
    if no_heur:
        lines += ["gap_fill = false", "pointer_seeds = false"]
    lines += [""]
    if seed:
        lines += ["[functions]"] + ['"0x%08X" = ""' % va for va in sorted(code_vas)] + [""]
    lines += ["[symbols]"]
    for name in wanted:
        lines.append("%s = 0x%08X" % (name, resolved[name][0]) if name in resolved else "%s = 0" % name)
    Path(out_path).write_text("\n".join(lines) + "\n")

    report = {
        "map_entry_matches_xbe": True, "entry": "0x%08X" % xbe_entry, "map_symbols_in_xbe_sections": publics,
        "map_function_entries_in_code_sections": len(code_vas),
        "tgp482_symbol_names": len(wanted), "resolved": len(resolved), "ambiguous": len(ambiguous),
        "missing_but_library_linked": len(missing), "library_not_linked_by_buffy": len(not_linked),
        "missing_with_4432_variant": len(near), "missing_absent_from_image": len(missing) - len(near),
        "missing_names": missing, "near_misses": near, "ambiguous_names": ambiguous, "not_linked_names": not_linked,
        "resolved_by_library": {},
        "code_sections": code_secs,
    }
    for _, (_, _, libs) in resolved.items():
        for l in libs:
            report["resolved_by_library"][l] = report["resolved_by_library"].get(l, 0) + 1
    js = json.dumps(report, indent=2)
    if report_path:
        Path(report_path).write_text(js)
    print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
