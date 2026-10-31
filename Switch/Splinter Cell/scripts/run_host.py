"""Bounded differential run using a private disc copy, never the source dump."""
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--seconds", type=int, default=30)
parser.add_argument("--launch-page", type=Path, help="replay a previously captured original 4 KiB launch page")
options = parser.parse_args()
WORK = ROOT / "private/host-data"
GAME = WORK / "game"
GAME.mkdir(parents=True, exist_ok=True)
print("Preparing private extracted disc copy (ISO excluded)", flush=True)
for source in (ROOT / "Game Files").rglob("*"):
    if not source.is_file() or source.suffix.lower() == ".iso":
        continue
    destination = GAME / source.relative_to(ROOT / "Game Files")
    if not destination.exists() or destination.stat().st_size != source.stat().st_size:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
lock = json.loads((ROOT / "dependencies.json").read_text())
with (GAME / "default.xbe").open("rb") as source:
    if hashlib.file_digest(source, "sha256").hexdigest() != lock["executable"]["sha256"]:
        raise SystemExit("Private executable copy hash mismatch")
environment = dict(os.environ, NFSU2_GAME_DIR=str(GAME), RECOMP_VBLANK="1",
                   RECOMP_AC97_READY="plain", RECOMP_USB="1", RECOMP_PB_EXEC="1",
                   RECOMP_UNIMPL_TRAP="1", RECOMP_WATCHDOG_SECS=os.environ.get("RECOMP_WATCHDOG_SECS", "10"), RECOMP_WATCHDOG_KEEP="1")
handoff = WORK / "sc1-launch-page.bin"
handoff.unlink(missing_ok=True)
if options.launch_page:
    if options.launch_page.stat().st_size != 4096:
        raise SystemExit("A captured launch page must contain exactly 4096 bytes")
    shutil.copyfile(options.launch_page, handoff)
environment["SC1_LAUNCH_HANDOFF"] = str(handoff)
# Prevent Windows error-reporting dialogs from obstructing a bounded diagnostic.
ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
log = ROOT / "logs/host-run.log"
with log.open("w", encoding="utf-8") as output:
    deadline = time.monotonic() + options.seconds
    timed_out = False
    restarts = 0
    process_ids = []
    while True:
        child = subprocess.Popen([str(ROOT / "build/host/sc1.exe")], cwd=WORK,
            env=environment, stdout=output, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        process_ids.append(child.pid)
        try:
            code = child.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            child.kill()
            code = child.wait()
        if timed_out or code or not handoff.exists():
            break
        shutil.copyfile(handoff, WORK / "sc1-last-launch-page.bin")
        restarts += 1
        if restarts > 5:
            raise RuntimeError("More than five guest title relaunches in one run")
        output.write(f"\n[SC1] supervising guest title relaunch {restarts}\n")
        output.flush()
result = {"exit_code": code, "timeout": timed_out, "relaunches": restarts,
          "process_ids": process_ids,
          "internal_reboots": log.read_text(errors="replace").count("[REBOOT] guest reset ("),
          "executable_sha256": hashlib.sha256((ROOT / "build/host/sc1.exe").read_bytes()).hexdigest(),
          "limit_seconds": options.seconds, "log": str(log)}
(ROOT / "private/host-run.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
if code and not timed_out:
    raise SystemExit(1)
