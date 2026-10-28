"""Run the pinned Xbox pipeline without writing into the retail game directory."""
import argparse
import hashlib
import json
import subprocess
import sys
import shutil
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
PRIVATE = PROJECT / "private"
LOCK = json.loads((PROJECT / "dependencies.json").read_text())
UPSTREAM = PRIVATE / "burnout3-sw"
TOOLKIT = UPSTREAM / "xboxrecomp"


def run_module(name, *args):
    log = PROJECT / "logs" / (name + ".log")
    print(f"Running {name}; log: {log}", flush=True)
    with log.open("w", encoding="utf-8") as output:
        subprocess.run([sys.executable, "-u", "-m", "tools." + name,
                        *map(str, args)], cwd=TOOLKIT, stdout=output,
                       stderr=subprocess.STDOUT, check=True)


def finish_generation():
    # Upstream emits silent ret-shaped bodies for unresolved direct calls.
    # A bring-up artifact must report them at the actual guest address instead.
    staging = PROJECT / "private" / "generated-stage"
    from prepare_exceptions import prepare
    prepare(staging)
    # The original DirectSound routine computes the DSP scratch address.
    # Register its command word with the existing passthrough DSP model,
    # without replacing any original instruction or fixing a guest address.
    dsp_files = []
    for path in staging.glob("recomp_*.c"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r'void sub_0023F51E\(void\)\n\{.*?\n\}', text, re.S)
        if not match:
            continue
        body = match.group(0)
        marker = '    ebx = MMIO_RD32(eax);'
        if body.count(marker) != 1:
            raise RuntimeError("Original DirectSound scratch calculation changed")
        body = body.replace(marker, marker + '\n    sc1_register_dsp_scratch(ebx);', 1)
        text = text[:match.start()] + body + text[match.end():]
        text = text.replace('#include <math.h>',
                            '#include <math.h>\nvoid sc1_register_dsp_scratch(uint32_t);', 1)
        path.write_text(text, encoding="utf-8")
        dsp_files.append(path)
    if len(dsp_files) != 1:
        raise RuntimeError("Expected one original DirectSound command function")
    # Diagnose a reached timing failure without altering the driver's writes.
    flip_files = []
    for path in staging.glob("recomp_*.c"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r'void sub_001F6D20\(void\)\n\{.*?\n\}', text, re.S)
        if not match:
            continue
        body = match.group(0)
        marker = 'loc_001F6DD4: ;'
        if body.count(marker) != 1:
            raise RuntimeError("Original flip enqueue changed")
        body = body.replace(marker, marker + '\n    sc1_trace_flip_queue(edi, MMIO_RD32(esi + 0x1C0));', 1)
        text = text[:match.start()] + body + text[match.end():]
        retire = re.search(r'void sub_001F6990\(void\)\n\{.*?\n\}', text, re.S)
        if not retire:
            raise RuntimeError("Original flip retirement missing")
        retire_body = retire.group(0)
        marker = '    if (CMP_NE(_fa, _fb)) goto loc_001F6A51;'
        if retire_body.count(marker) != 1:
            raise RuntimeError("Original flip retirement changed")
        retire_body = retire_body.replace(marker, '    sc1_trace_flip_retire(edx, edi);\n' + marker, 1)
        marker = '    MMIO_WR32(esi + 0x1BC, (ecx));'
        if retire_body.count(marker) != 1:
            raise RuntimeError("Original flip retirement counter changed")
        retire_body = retire_body.replace(marker, marker + '\n    nv2a_pb_flip_retired(1);', 1)
        text = text[:retire.start()] + retire_body + text[retire.end():]
        vblank = re.search(r'void sub_001F6A60\(void\)\n\{.*?\n\}', text, re.S)
        if not vblank:
            raise RuntimeError("Original vblank routine missing")
        vblank_body = vblank.group(0)
        marker = 'loc_001F6A84: ;'
        if vblank_body.count(marker) != 1:
            raise RuntimeError("Original vblank counter changed")
        vblank_body = vblank_body.replace(marker, marker + '\n    nv2a_pb_flip_retired(0);', 1)
        marker = '    RECOMP_PREEMPT();'
        if vblank_body.count(marker) != 1 or vblank_body.count('return;') != 1:
            raise RuntimeError("Original vblank exit shape changed")
        vblank_body = vblank_body.replace(marker, '    uint8_t sc1_irql = sc1_d3d_enter();\n    xbox_Nv2aVblankTaken();\n' + marker, 1)
        vblank_body = vblank_body.replace('return;', 'sc1_d3d_leave(sc1_irql); return;', 1)
        text = text[:vblank.start()] + vblank_body + text[vblank.end():]
        pgraph = re.search(r'void sub_001F6FB0\(void\)\n\{.*?\n\}', text, re.S)
        if not pgraph:
            raise RuntimeError("Original PGRAPH handler missing")
        pgraph_body = pgraph.group(0)
        if pgraph_body.count(marker) != 1 or pgraph_body.count('return;') != 1:
            raise RuntimeError("Original PGRAPH exit shape changed")
        pgraph_body = pgraph_body.replace(marker, '    uint8_t sc1_irql = sc1_d3d_enter();\n    uint32_t sc1_source = sc1_pgraph_enter();\n' + marker, 1)
        pgraph_body = pgraph_body.replace('return;', 'sc1_pgraph_leave(sc1_source); sc1_d3d_leave(sc1_irql); return;', 1)
        text = text[:pgraph.start()] + pgraph_body + text[pgraph.end():]
        text = text.replace('#include <math.h>', '#include <math.h>\nvoid sc1_trace_flip_queue(uint32_t, uint32_t);\nvoid sc1_trace_flip_retire(uint32_t, uint32_t);\nvoid nv2a_pb_flip_retired(unsigned);\nuint8_t sc1_d3d_enter(void);\nvoid sc1_d3d_leave(uint8_t);\nuint32_t sc1_pgraph_enter(void);\nvoid sc1_pgraph_leave(uint32_t);\nvoid xbox_Nv2aVblankTaken(void);', 1)
        path.write_text(text, encoding="utf-8")
        flip_files.append(path)
    if len(flip_files) != 1:
        raise RuntimeError("Expected one original flip enqueue function")
    stubs = staging / "recomp_stubs_unresolved.c"
    text = stubs.read_text()
    text = re.sub(r'void (sub_([0-9A-Fa-f]+))\(void\) \{[^\n]*\}',
                  lambda m: f'void {m[1]}(void) {{ recomp_icall_fail_log(0x{m[2]}u); }}', text)
    stubs.write_text(text)
    for path in staging.iterdir():
        if path.is_file():
            target = PROJECT / "generated" / path.name
            if not target.exists() or target.read_bytes() != path.read_bytes():
                # A changed file must be newer than its object even when
                # restoring a retained stage after temporary diagnostics.
                shutil.copyfile(path, target)
    for old in (PROJECT / "generated").glob("recomp_*.c"):
        if not (staging / old.name).exists():
            old.unlink()


def main():
    global TOOLKIT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lift-only", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    options = parser.parse_args()
    for directory in (PRIVATE, PROJECT / "logs", PROJECT / "generated"):
        directory.mkdir(parents=True, exist_ok=True)
    pin = LOCK["burnout3-sw"]
    if not UPSTREAM.exists():
        subprocess.run(["git", "clone", "--branch", pin["branch"],
                        pin["url"], str(UPSTREAM)], check=True)
        subprocess.run(["git", "-C", str(UPSTREAM), "checkout", "--detach",
                        pin["commit"]], check=True)
    head = subprocess.check_output(["git", "-C", str(UPSTREAM),
                                    "rev-parse", "HEAD"], text=True).strip()
    if head != pin["commit"]:
        raise SystemExit(f"Unexpected runtime revision {head}; expected {pin['commit']}")
    xbe = PROJECT / "Game Files" / "default.xbe"
    with xbe.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != LOCK["executable"]["sha256"]:
        raise SystemExit("Unrecognised XBE: this integration currently requires the pinned European retail executable")
    run_module("xbe_parser", xbe, "--json", PRIVATE / "sc1_analysis.json", "--quiet")
    if options.prepare_only:
        return
    if not options.lift_only:
        subprocess.run([sys.executable, str(PROJECT / "scripts/recover_class_seeds.py")], check=True)
        run_module("disasm", xbe, "--analysis-json", PRIVATE / "sc1_analysis.json",
                   "-o", PRIVATE / "disasm", "--seed-functions", PROJECT / "config/seed_functions.json",
                   "--seed-functions", PRIVATE / "class_callback_seeds.json", "--force")
        run_module("func_id", xbe, "--functions", PRIVATE / "disasm/functions.json",
                   "--strings", PRIVATE / "disasm/strings.json",
                   "--xrefs", PRIVATE / "disasm/xrefs.json", "-o", PRIVATE / "func_id")
        run_module("abi_analysis", xbe, "--disasm-dir", PRIVATE / "disasm",
                   "--func-id-dir", PRIVATE / "func_id", "--output-dir", PRIVATE / "abi")
    subprocess.run([sys.executable, str(PROJECT / "scripts/prepare_codegen.py")], check=True)
    TOOLKIT = PRIVATE / "codegen"
    staging = PRIVATE / "generated-stage"
    staging.mkdir(exist_ok=True)
    for old in staging.glob("recomp_*"):
        if old.is_file():
            old.unlink()
    run_module("recomp", xbe, "--game-name", "Splinter Cell", "--all", "--split", "150",
               "--disasm-dir", PRIVATE / "disasm", "--func-id-dir", PRIVATE / "func_id",
               "--abi-dir", PRIVATE / "abi", "--gen-dir", PRIVATE / "generated-stage",
               "-o", PRIVATE / "lift", "--mmio-sections", "DSOUND,XPP,D3D,XGRPH")
    finish_generation()


if __name__ == "__main__":
    main()
