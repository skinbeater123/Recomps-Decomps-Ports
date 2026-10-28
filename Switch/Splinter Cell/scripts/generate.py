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
