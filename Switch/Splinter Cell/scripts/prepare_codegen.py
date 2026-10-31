"""Backport CPUID/EFLAGS lifting to the pinned Switch fork (MIT xboxrecomp).

Based on sp00nznet/xboxrecomp f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b.
Keep the Switch fork's register, memory, preemption and MMIO ABI intact.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "private/burnout3-sw/xboxrecomp"
DEST = ROOT / "private/codegen"


def once(text, before, after):
    if text.count(before) != 1:
        raise RuntimeError(f"Codegen patch context changed: {before[:90]}")
    return text.replace(before, after, 1)


def main():
    for directory in ("tools", "templates/runtime"):
        shutil.copytree(SOURCE / directory, DEST / directory, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "output"))
    # Upstream switch-arm resynchronization fix. SC1's CRT copy at 0x1B1820
    # retained an OR decoded from inside MOV's displacement at 0x1B197E.
    # That spurious store changes a freed block's next pointer by 0x4000.
    path = DEST / "tools/recomp/disasm.py"
    text = path.read_text(encoding="utf-8")
    text = once(text, '''                if cs_insn.address in decoded:
                    break          # rejoined a stream we already have
                decoded[cs_insn.address] = self._decode_instruction(cs_insn)''',
        '''                if cs_insn.address in decoded:
                    break          # rejoined a stream we already have
                # Drop every stale instruction beginning inside this real
                # instruction, not just the one straddling the arm's entry.
                for inner in range(cs_insn.address + 1,
                                   cs_insn.address + cs_insn.size):
                    decoded.pop(inner, None)
                decoded[cs_insn.address] = self._decode_instruction(cs_insn)''')
    path.write_text(text, encoding="utf-8")
    path = DEST / "tools/recomp/lifter.py"
    text = path.read_text(encoding="utf-8")
    text = once(text, '    "rdtsc", "cpuid",      # Special instructions',
                '    "rdtsc",               # CPUID preserves EFLAGS')
    text = once(text, '    "pushfd", "pushal", "popal",',
                '    "pushfd", "pushal", "popal", "cpuid",')
    marker = '        # ── Time stamp counter ──'
    instructions = '''        # CPU/EFLAGS backport; same implementation as upstream xboxrecomp.
        if m == "cpuid":
            return ["{ uint32_t _id[4]; xbox_Cpuid(eax, ecx, _id);"
                    " eax = _id[0]; ebx = _id[1]; ecx = _id[2]; edx = _id[3]; }"]
        if m == "cli":
            return ["g_eflags &= ~0x200u; /* cli */"]
        if m == "sti":
            return ["g_eflags |= 0x200u; /* sti */"]
        if m == "pushfd":
            return ["PUSH32(esp, recomp_pushfd()); /* pushfd */"]
        if m == "popfd":
            out = ["{ uint32_t _efl; POP32(esp, _efl); recomp_popfd(_efl); }"]
            if self.needs_cf:
                out.append("_cf = (int)(g_eflags & 1u);")
            return out

'''
    text = once(text, marker, instructions + marker)
    marker = '    cmp_macro, test_macro, desc = cond_info\n'
    conditions = '''    if flag_setter == "eflags":
        cf, pf, zf, sf, of = ("((g_eflags >> %d) & 1u)" % n for n in (0, 2, 6, 7, 11))
        values = {"je": zf, "jne": f"!{zf}", "jb": cf, "jae": f"!{cf}",
                  "jbe": f"({cf} || {zf})", "ja": f"(!{cf} && !{zf})",
                  "js": sf, "jns": f"!{sf}", "jo": of, "jno": f"!{of}",
                  "jp": pf, "jnp": f"!{pf}", "jl": f"({sf} != {of})",
                  "jge": f"({sf} == {of})", "jle": f"({zf} || {sf} != {of})",
                  "jg": f"(!{zf} && {sf} == {of})"}
        value = values.get(_JCC_CANON.get(jcc, jcc))
        return (value, desc) if value else None
'''
    text = once(text, marker, marker + conditions)
    marker = '    # ── bsf/bsr: ZF is the only flag they define ──'
    overflow = '''    # Upstream OF/PF fix: unsigned width-aware formulas avoid host UB.
    def _overflow_flag():
        t = _sf_utype
        if flag_setter == "cmp":
            a, b, r, same = lhs, rhs, f"({lhs}) - ({rhs})", False
        elif flag_setter == "sub" and rhs == "_fb":
            a, b, r, same = "(_fa + _fb)", "_fb", "_fa", False
        elif flag_setter == "add" and rhs == "_fb":
            a, b, r, same = "(_fa - _fb)", "_fb", "_fa", True
        elif flag_setter in ("and", "or", "xor", "test"):
            return "0"
        else:
            return None
        signs = f"(({t})({a}) ^ ({t})({b}))"
        if same:
            signs = f"(({t})~{signs})"
        return f"((({t})({signs} & (({t})({a}) ^ ({t})({r})))) >> {_sf_top})"
    if jcc in ("jo", "jno"):
        value = _overflow_flag()
        if value is not None:
            return (f"({value} != 0)" if jcc == "jo" else f"({value} == 0)"), desc
    if (flag_setter in ("sub", "add", "and", "or", "xor") and lhs == "_fa"
            and jcc in ("jp", "jpe", "jnp", "jpo")):
        return ("RECOMP_PARITY8(_fa)" if jcc in ("jp", "jpe") else "(!RECOMP_PARITY8(_fa))"), desc

'''
    text = once(text, marker, overflow + marker)
    marker = '        # Check if this instruction uses flags (jcc, setcc, cmovcc)'
    flags = '''        if curr.mnemonic == "pushfd" and last_flag_setter:
            parts, mask = [], 0
            for condition, bit in (("jb", 1), ("jp", 4), ("je", 0x40), ("js", 0x80), ("jo", 0x800)):
                value = _make_condition(condition, last_flag_setter, last_flag_ops)
                if not value:
                    lifter.unimplemented.setdefault("pushfd flags", []).append(curr.address)
                    stmts.append(f'RECOMP_UNIMPL("pushfd flags", 0x{curr.address:08X}u);')
                    break
                mask |= bit
                parts.append(f"(({value[0]}) ? 0x{bit:X}u : 0u)")
            if parts:
                stmts.append(f"g_eflags = (g_eflags & ~0x{mask:X}u) | " + " | ".join(parts) + ";")

'''
    text = once(text, marker, flags + marker)
    marker = '        elif curr.mnemonic in _FLAGS_UNDEFINED:\n'
    text = once(text, marker, '''        elif curr.mnemonic == "popfd":
            last_flag_setter, last_flag_ops = "eflags", []
''' + marker)
    path.write_text(text, encoding="utf-8")
    header = DEST / "templates/runtime/recomp_types.h"
    text = header.read_text(encoding="utf-8")
    text = once(text, 'if (g_gil_contended) recomp_preempt();',
                'if (g_gil_contended && (g_eflags & 0x200u)) recomp_preempt();')
    text = once(text, 'if (__builtin_expect(g_gil_contended, 0)) recomp_preempt();',
                'if (__builtin_expect(g_gil_contended, 0) && (g_eflags & 0x200u)) recomp_preempt();')
    text = once(text, '#include <sched.h>\nvoid recomp_spin_wake(void);',
                '#include <sched.h>\nextern RECOMP_TLS uint32_t g_eflags;\nvoid recomp_spin_wake(void);')
    text = once(text, 'if ((turns & 63u) == 0)\n        recomp_spin_yield();',
                'if ((turns & 63u) == 0 && (g_eflags & 0x200u))\n        recomp_preempt();')
    # MSVC's pause-only branch starves ISRs waiting on the guest lock when
    # original D3D spins for a fence. Match the existing Horizon poll yield.
    text = once(text, '#define RECOMP_SPIN_HINT() _mm_pause()', '''extern RECOMP_TLS uint32_t g_eflags;
void recomp_spin_wake(void);
void recomp_preempt(void);
static inline void recomp_spin_hint(void) {
    static RECOMP_TLS unsigned turns;
    _mm_pause();
    if ((++turns & 15u) == 0) recomp_spin_wake();
    if ((turns & 63u) == 0 && (g_eflags & 0x200u)) recomp_preempt();
}
#define RECOMP_SPIN_HINT() recomp_spin_hint()''')
    marker = 'extern RECOMP_TLS int g_df;'
    helpers = '''
/* CPUID/EFLAGS helpers backported from xboxrecomp f0f8a461 (MIT). */
extern RECOMP_TLS uint32_t g_eflags;
#define RECOMP_EFL_WRITABLE 0x00247FD5u
static inline uint32_t recomp_pushfd(void) {
    return (g_eflags & ~0x400u) | 0x2u | (g_df ? 0x400u : 0u);
}
static inline void recomp_popfd(uint32_t value) {
    g_eflags = (value & RECOMP_EFL_WRITABLE) | 0x2u;
    g_df = (int)((value >> 10) & 1u);
}
void xbox_Cpuid(uint32_t leaf, uint32_t subleaf, uint32_t out[4]);
'''
    header.write_text(once(text, marker, marker + helpers), encoding="utf-8")
    print(f"Prepared CPU instruction backport: {DEST}")


if __name__ == "__main__":
    main()
