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

# Observe the original XDK callback target at its existing indirect call.
call = 'RECOMP_ICALL_SAFE_AT(_icall_target, _icall_esp, 0x0025C9D3u)'
needle = 'SC1_TRACE_XID(_icall_target, ebx); ' + call
files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    if call not in text:
        continue
    files.append(path)
    if needle not in text:
        if text.count(call) != 1:
            raise RuntimeError('Unexpected original XDK callback site')
        declaration = ('#if defined(_WIN32)\n'
            'extern void sc1_trace_xid_callback(uint32_t, uint32_t);\n'
            '#define SC1_TRACE_XID(target, object) sc1_trace_xid_callback(target, object)\n'
            '#else\n#define SC1_TRACE_XID(target, object) ((void)0)\n#endif\n')
        text = text.replace('#include <math.h>', '#include <math.h>\n' + declaration, 1)
        if declaration not in text:
            raise RuntimeError('Expected generated math include')
        path.write_bytes(text.replace(call, needle, 1).encode('utf-8'))
if len(files) != 1:
    raise RuntimeError(f'Expected one original XDK callback site, got {len(files)}')

# Trace the observed JoyY binding handler without changing its original body.
axis_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    match = re.search(r'void sub_00085A40\(void\)\n\{.*?\n\}', text, re.S)
    if not match:
        continue
    axis_files.append(path)
    body = match.group()
    entry = 'loc_00085A40: ;'
    hook = entry + ('\n#if defined(_WIN32)\n'
        '    uint32_t sc1_axis_key = MEM32(esp + 4), sc1_axis_value = MEM32(esp + 8);\n'
        '    extern void sc1_trace_axis_stage(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);\n'
        '#endif')
    if hook not in body:
        if body.count(entry) != 1: raise RuntimeError('Unexpected axis-handler entry')
        body = body.replace(entry, hook, 1)
        for label, value in [('00085A92','MEM32(esp + 0x1C)'), ('00085AA7','0'), ('00085B6F','MEM32(esi + 0xECC)'), ('00085B96','0')]:
            marker = f'loc_{label}: ;'
            if body.count(marker) != 1: raise RuntimeError(f'Unexpected axis-handler label {label}')
            patch = marker + ('\n#if defined(_WIN32)\n'
                f'    sc1_trace_axis_stage(sc1_axis_key, sc1_axis_value, 0x{label}u, {value}, esi);\n'
                '#endif')
            body = body.replace(marker, patch, 1)
        text = text[:match.start()] + body + text[match.end():]
        path.write_bytes(text.encode('utf-8'))
if len(axis_files) != 1:
    raise RuntimeError(f'Expected one original input handler, got {len(axis_files)}')

# Observe the original input-command dispatch when a nonzero axis is active.
exec_call = 'RECOMP_ICALL_SAFE_AT(_icall_target, _icall_esp, 0x000847A5u)'
exec_hook = 'SC1_TRACE_AXIS_EXEC(_icall_target, esi, eax); ' + exec_call
exec_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    if exec_call not in text: continue
    exec_files.append(path)
    if exec_hook not in text:
        if text.count(exec_call) != 1: raise RuntimeError('Unexpected input-command call site')
        decl = ('#if defined(_WIN32)\n'
            'extern void sc1_trace_axis_exec(uint32_t,uint32_t,uint32_t);\n'
            '#define SC1_TRACE_AXIS_EXEC(target, object, command) sc1_trace_axis_exec(target, object, command)\n'
            '#else\n#define SC1_TRACE_AXIS_EXEC(target, object, command) ((void)0)\n#endif\n')
        text = text.replace('#include <math.h>', '#include <math.h>\n' + decl, 1)
        if decl not in text: raise RuntimeError('Expected generated math include')
        path.write_bytes(text.replace(exec_call, exec_hook, 1).encode('utf-8'))
if len(exec_files) != 1: raise RuntimeError(f'Expected one input-command call, got {len(exec_files)}')
