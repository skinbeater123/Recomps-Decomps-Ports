"""Bounded differential run using a private disc copy, never the source dump."""
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--seconds", type=int, default=30)
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
# Prevent Windows error-reporting dialogs from obstructing a bounded diagnostic.
ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
log = ROOT / "logs/host-run.log"
with log.open("w", encoding="utf-8") as output:
    child = subprocess.Popen([str(ROOT / "build/host/sc1.exe")], cwd=WORK,
        env=environment, stdout=output, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW)
    timed_out = False
    try:
        code = child.wait(timeout=options.seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()
        code = child.wait()
result = {"exit_code": code, "timeout": timed_out, "limit_seconds": options.seconds, "log": str(log)}
(ROOT / "private/host-run.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
if code and not timed_out:
    raise SystemExit(1)
