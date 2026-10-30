#!/usr/bin/env python3
"""Write an AArch64 GCC overlay of TGP482's runtime/cpu headers (same transform BLACK used).

devkitA64 GCC 16.1.0 crashes (aarch64_function_arg_alignment ICE) when aligned(1) may_alias
scalar typedefs reach calls at -O1/-O2. The overlay swaps each typedef for a packed may_alias
struct and rewrites the matching memory macro to access its member. The SDK checkout stays
untouched; put the overlay directory first on the include path.

    python -I make_a64_overlay.py <XboxXBERecomp>/runtime/cpu <overlay>/cpu
"""
import shutil
import sys
from pathlib import Path

TYPES = [("uint16_t", "x86_u16u"), ("uint32_t", "x86_u32u"), ("uint64_t", "x86_u64u"),
         ("float", "x86_f32u"), ("double", "x86_f64u")]


def main(argv):
    src, dst = Path(argv[1]), Path(argv[2])
    ops = (src / "x86_ops.h").read_text()
    for base, alias in TYPES:
        before = "typedef %s __attribute__((aligned(1), may_alias)) %s;" % (base, alias)
        load = "(*(%s*)(base + (uint32_t)(a)))" % alias
        if before not in ops or load not in ops:
            print("unexpected x86_ops.h: %s not found; inspect before adapting" % alias, file=sys.stderr)
            return 1
        ops = ops.replace(before, "struct __attribute__((packed, may_alias)) %s { %s value; };" % (alias, base))
        ops = ops.replace(load, "(((%s*)(base + (uint32_t)(a)))->value)" % alias)
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "x86_ops.h").write_text(ops)
    shutil.copy2(src / "x86_context.h", dst / "x86_context.h")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
