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

# Observe the actual original AXIS property stores, after dead-zone parsing.
write_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    match = re.search(r'void sub_00084AF0\(void\)\n\{.*?\n\}', text, re.S)
    if not match: continue
    write_files.append(path)
    body = match.group()
    if 'SC1_TRACE_AXIS_WRITE(' in body: continue
    store = '    MEMF(edi) = (float)fp_top(); fp_pop(); /* fstp */'
    for label in ('00084E8D','00084EB3','00084EDD','00084F05','00084F1F'):
        start = body.index(f'loc_{label}: ;')
        at = body.index(store, start) + len(store)
        body = body[:at] + f'\n    SC1_TRACE_AXIS_WRITE(0x{label}u, edi, MEM32(edi));' + body[at:]
    declaration = ('#if defined(_WIN32)\n'
        'extern void sc1_trace_axis_write(uint32_t,uint32_t,uint32_t);\n'
        '#define SC1_TRACE_AXIS_WRITE(stage, property, value) sc1_trace_axis_write(stage, property, value)\n'
        '#else\n#define SC1_TRACE_AXIS_WRITE(stage, property, value) ((void)0)\n#endif\n')
    text = text[:match.start()] + body + text[match.end():]
    text = text.replace('#include <math.h>', '#include <math.h>\n' + declaration, 1)
    if declaration not in text: raise RuntimeError('Expected generated math include')
    path.write_bytes(text.encode('utf-8'))
if len(write_files) != 1: raise RuntimeError(f'Expected one original AXIS command body, got {len(write_files)}')

constant_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    marker = 'loc_0002E1E0: ;'
    if marker not in text: continue
    constant_files.append(path)
    hook = marker + ('\n#if defined(_WIN32)\n'
        '    extern void sc1_trace_axis_constant(uint32_t,uint32_t);\n'
        '    sc1_trace_axis_constant(MEM32(esp + 4), MEM32(esp + 8));\n'
        '#endif')
    if hook not in text: path.write_bytes(text.replace(marker, hook, 1).encode('utf-8'))
if len(constant_files) != 1: raise RuntimeError(f'Expected one original float-constant handler, got {len(constant_files)}')

gate_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8')
    match = re.search(r'void sub_0002DFB0\(void\)\n\{.*?\n\}', text, re.S)
    if not match: continue
    gate_files.append(path)
    body = match.group()
    if 'sc1_trace_input_gate(' in body: continue
    store = '    MEM32(edi) = eax;'
    if body.count(store) != 2: raise RuntimeError('Original boolean assignment stores changed')
    body = body.replace(store, store + ('\n#if defined(_WIN32)\n'
        '    extern void sc1_trace_input_gate(uint32_t,uint32_t,uint32_t,uint32_t);\n'
        '    sc1_trace_input_gate(esi, ebp, edi, eax);\n#endif'))
    path.write_bytes((text[:match.start()] + body + text[match.end():]).encode('utf-8'))
if len(gate_files) != 1: raise RuntimeError(f'Expected one original boolean assignment handler, got {len(gate_files)}')

pattern_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text = path.read_text(encoding='utf-8'); marker = 'loc_00033360: ;'
    if marker not in text: continue
    pattern_files.append(path)
    hook = marker + ('\n#if defined(_WIN32)\n'
        '    extern void sc1_trace_pattern_call(uint32_t,uint32_t);\n'
        '    sc1_trace_pattern_call(ecx, MEM32(esp+4));\n#endif')
    if hook not in text: path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))
if len(pattern_files) != 1: raise RuntimeError('Expected one original script execution entry')

invoke_files = []
for path in (root / 'generated').glob('recomp_*.c'):
    text=path.read_text(encoding='utf-8'); marker='loc_00034F00: ;'
    if marker not in text: continue
    invoke_files.append(path)
    hook=marker+ ('\n#if defined(_WIN32)\n'
        '    extern void sc1_trace_pattern_invoke(uint32_t,uint32_t,uint32_t);\n'
        '    sc1_trace_pattern_invoke(ecx,MEM32(esp+4),MEM32(esp+12));\n#endif')
    if hook not in text:path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))
if len(invoke_files)!=1:raise RuntimeError('Expected one original function invocation entry')

# Observe original AI goal dispatch and its first movement-goal branches.
for label,stage,obj,goal in [('0012A1A0',0,'ecx','0'),('00126370',1,'ecx','MEM32(esp+4)'),('00126614',2,'edi','esi'),('0012672C',3,'edi','esi'),('0012675F',4,'edi','esi'),('0012491C',5,'esi','MEM32(esi+0x458)'),('00122E44',6,'ebp','ebx'),('00123993',7,'ebp','ebx'),('00122E4B',8,'ebp','ebx'),('00122FCB',9,'ebp','ebx'),('00123177',10,'ebp','ebx'),('001231FE',11,'ebp','ebx'),('00123270',12,'ebp','ebx'),('0012345B',13,'ebp','ebx'),('00123539',14,'ebp','ebx'),('00123551',15,'ebp','ebx'),('00123B09',16,'ebp','ebx'),('00123C35',17,'ebp','ebx'),('0012404C',18,'ebp','ebx'),('0012415C',19,'ebp','ebx'),('00124233',20,'ebp','ebx')]:
    matches=[]
    for path in (root/'generated').glob('recomp_*.c'):
        text=path.read_text(encoding='utf-8');marker=f'loc_{label}: ;'
        if marker not in text:continue
        matches.append(path)
        text=re.sub(re.escape(marker)+r'\n#if defined\(_WIN32\)\n    extern void sc1_trace_ai_goal\([^\n]*\n    sc1_trace_ai_goal\([^\n]*\n#endif',marker,text)
        hook=marker+f'\n#if defined(_WIN32)\n    extern void sc1_trace_ai_goal(uint32_t,uint32_t,uint32_t,uint32_t);\n    sc1_trace_ai_goal({stage},{obj},{goal},eax);\n#endif'
        if hook not in text:path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))
    if len(matches)!=1:raise RuntimeError(f'Expected one AI goal site {label}')

for label,stage,pawn,params in [('00117B20',0,'ecx','esp+4'),('00117B75',1,'esi','esp+8'),('000C7907',2,'edi','esp+0x18'),('000C79C1',3,'edi','esp+0x18'),('00063810',4,'ecx','esp+4')]:
    for path in (root/'generated').glob('recomp_*.c'):
        text=path.read_text(encoding='utf-8');marker=f'loc_{label}: ;'
        if marker not in text:continue
        hook=marker+f'\n#if defined(_WIN32)\n    extern void sc1_trace_rotation(uint32_t,uint32_t,uint32_t,uint32_t);\n    sc1_trace_rotation({stage},{pawn},{params},eax);\n#endif'
        if hook not in text:path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))

for path in (root/'generated').glob('recomp_*.c'):
    text=path.read_text(encoding='utf-8');marker='loc_000638BF: ;'
    if marker not in text:continue
    hook=marker+'\n#if defined(_WIN32)\n    extern void sc1_trace_turn_result(uint32_t,uint32_t,uint32_t);\n    sc1_trace_turn_result(esp,eax,edx);\n#endif'
    if hook not in text:path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))

for path in (root/'generated').glob('recomp_*.c'):
    text=path.read_text(encoding='utf-8');marker='loc_00065B05: ;'
    if marker not in text:continue
    hook=marker+'\n#if defined(_WIN32)\n    extern void sc1_trace_turn_store(uint32_t,uint32_t,uint32_t);\n    sc1_trace_turn_store(esi,MEM32(esp+0x18),eax);\n#endif'
    if hook not in text:path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))

for label,stage,frame,target in [('0002DE7E',0,'MEM32(esp+0x18)','MEM32(0x2DAC00)'),('0002DFA8',1,'MEM32(esp+0x18)','esi'),('000C7907',2,'esi','esp+0x18')]:
    for path in (root/'generated').glob('recomp_*.c'):
        text=path.read_text(encoding='utf-8');marker=f'loc_{label}: ;'
        if marker not in text:continue
        hook=marker+f'\n#if defined(_WIN32)\n    extern void sc1_trace_rotate_let(uint32_t,uint32_t,uint32_t);\n    sc1_trace_rotate_let({frame},{target},{stage});\n#endif'
        if hook not in text:path.write_bytes(text.replace(marker,hook,1).encode('utf-8'))
