"""Install an optional host-only observation at original AActor::execMove entry."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
found = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    if not re.search(r'void sub_000C7550\(void\)\s*\{', text):
        continue
    found.append(path)
    marker = 'loc_000C7550: ;'
    hook = marker + '\n#if defined(_WIN32)\n    extern void sc1_trace_exec_move(uint32_t);\n    sc1_trace_exec_move(g_ecx);\n#endif'
    if hook not in text:
        if text.count(marker) != 1:
            raise RuntimeError('Unexpected original execMove label')
        path.write_bytes(text.replace(marker, hook, 1).encode('utf-8'))
if len(found) != 1:
    raise RuntimeError(f'Expected one original execMove body, got {len(found)}')
