"""Recover callback arguments at SC1's observed native-class registration calls.

This is deliberately scoped to the hash-pinned European executable. The two
callbacks first seen dynamically at 0x28760 and 0x531D0 use this same call site
pattern. Only aligned .text pointers preceded by NOP/INT3 padding are accepted.
"""
import json
import struct
import sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM

ROOT = Path(__file__).resolve().parents[1]


def main():
    metadata = json.loads((ROOT / "private/sc1_analysis.json").read_text())
    section = next(s for s in metadata["sections"] if s["name"] == ".text")
    base, offset = int(section["virtual_addr"], 16), int(section["raw_addr"], 16)
    data = (ROOT / "Game Files/default.xbe").read_bytes()
    code = data[offset:offset + section["raw_size"]]
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True
    history, recovered, vptr_stores = [], {}, {}
    sites = 0
    for instruction in decoder.disasm(code, base):
        if instruction.id == 0:
            history.clear()
            continue
        if (instruction.mnemonic == "mov" and len(instruction.operands) == 2
                and instruction.operands[0].type == X86_OP_MEM
                and instruction.operands[0].mem.base and not instruction.operands[0].mem.index
                and instruction.operands[0].mem.disp == 0
                and instruction.operands[1].type == X86_OP_IMM):
            vptr_stores[instruction.operands[1].imm] = instruction.address
        if (instruction.mnemonic == "call" and instruction.operands
                and instruction.operands[0].type == X86_OP_IMM
                and instruction.operands[0].imm == 0x2C670):
            sites += 1
            for prior in reversed(history):
                if prior.mnemonic.startswith("j") or prior.mnemonic in ("call", "ret", "int3"):
                    break
                if prior.mnemonic != "push" or prior.operands[0].type != X86_OP_IMM:
                    continue
                target = prior.operands[0].imm
                if (base + 2 < target < base + len(code) and target % 16 == 0
                        and all(byte in (0x90, 0xCC) for byte in code[target - base - 2:target - base])):
                    recovered[target] = {"start": f"0x{target:08X}",
                        "registration_call": f"0x{instruction.address:08X}",
                        "pointer_argument": f"0x{prior.address:08X}"}
        history.append(instruction)
        if len(history) > 48:
            history.pop(0)
    class_count = len(recovered)
    # Reuse the toolkit's scanner, but seed only tables backed by an actual
    # object-vptr store in code, with padded method entries. Do not feed its
    # entire inferred classification database back into function discovery.
    sys.path.insert(0, str(ROOT / "private/burnout3-sw/xboxrecomp"))
    from tools.func_id.vtable_scanner import _find_vtables, _filter_vtables
    rdata = next(s for s in metadata["sections"] if s["name"] == ".rdata")
    ranges = [{"name": ".rdata", "va": int(rdata["virtual_addr"], 16),
               "raw": int(rdata["raw_addr"], 16), "size": rdata["raw_size"]}]
    vtables = _filter_vtables(_find_vtables(data, set(), [(base, base+len(code))], ranges))
    verified_tables = 0
    for table in vtables:
        address = table["address"]
        if address not in vptr_stores:
            continue
        verified_tables += 1
        for target in table["entries"]:
            if target % 16 == 0 and target > base+2 and all(
                    byte in (0x90, 0xCC) for byte in code[target-base-2:target-base]):
                recovered.setdefault(target, {"start": f"0x{target:08X}",
                    "vtable": f"0x{address:08X}", "vptr_store": f"0x{vptr_stores[address]:08X}"})
    vtable_count = len(recovered)-class_count
    output = ROOT / "private/class_callback_seeds.json"
    # The original SetRenderState dispatch at 0x001ED472 was observed indexing
    # base 0x001FBBA8 with state 0x9D, reaching 0x001ED970. The guarded branch
    # covers states 0x88..0xA5; the table ends before float data at 0x001FBE40.
    d3d = next(s for s in metadata["sections"] if s["name"] == "D3D")
    d3d_base, d3d_raw = int(d3d["virtual_addr"], 16), int(d3d["raw_addr"], 16)
    for slot in range(0x001FBDC8, 0x001FBE40, 4):
        target = struct.unpack_from("<I", data, d3d_raw + slot - d3d_base)[0]
        if not d3d_base <= target < d3d_base + d3d["raw_size"] or target % 16:
            raise RuntimeError(f"Unexpected XDK dispatch entry at {slot:08X}")
        recovered[target] = {"start": f"0x{target:08X}", "observed_dispatch_slot": f"0x{slot:08X}"}
    output.write_text(json.dumps([recovered[t] for t in sorted(recovered)], indent=2))
    print(f"Native registration sites: {sites}; padded class callbacks: {class_count}; verified vtables: {verified_tables}; additional methods: {vtable_count}; SDK dispatch entries: {len(recovered)-class_count-vtable_count}")


if __name__ == "__main__":
    main()
