"""Compact read-only disc inventory; the complete filename table stays private."""
import collections
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "Game Files"
files = sorted(p for p in GAME.rglob("*") if p.is_file())
records, critical = [], []
for path in files:
    size = path.stat().st_size
    with path.open("rb") as source:
        source.read(min(size, 64))
        if size:
            source.seek(size - 1)
            source.read(1)
    record = {"path": path.relative_to(GAME).as_posix(), "bytes": size}
    records.append(record)
    if path.suffix.lower() == ".xbe" or record["path"].startswith(("LMaps/000_menu/", "LMaps/001_Training/")) and path.suffix.lower() == ".lin":
        with path.open("rb") as source:
            critical.append({**record, "sha256": hashlib.file_digest(source, "sha256").hexdigest()})
data = (GAME / "default.xbe").read_bytes()
base = struct.unpack_from("<I", data, 0x104)[0]
certificate = struct.unpack_from("<I", data, 0x118)[0] - base
summary = {
    "files": len(files), "bytes": sum(r["bytes"] for r in records),
    "extensions": dict(collections.Counter(p.suffix.lower() for p in files)),
    "region_mask": hex(struct.unpack_from("<I", data, certificate + 0xA0)[0]),
    "symbols": [r["path"] for p, r in zip(files, records) if p.suffix.lower() in (".pdb", ".map", ".dbg", ".sym")],
    "critical": critical,
    "read_check": "first and last byte of every file; full hashes of critical files only"
}
output = ROOT / "private/inventory.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({**summary, "entries": records}, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
