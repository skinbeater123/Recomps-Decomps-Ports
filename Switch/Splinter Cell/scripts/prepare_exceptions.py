"""Add native landing frames to recognizable lifted MSVC exception frames.

The generated game code remains private. Guest handlers choose the continuation;
the landing map only lets that address resume inside its owning native frame.
"""
import re
from pathlib import Path

FUNCTION = re.compile(r'void sub_([0-9A-F]{8})\(void\)\n\{(.*?)(?=\n}\n)', re.S)
LABEL = re.compile(r'^loc_([0-9A-F]{8}):', re.M)
SAVE_STACK = '    MEM32(ebp + -16) = esp;'
REGS = ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi', 'esp')


def instrument(text):
    count = 0

    def change(match):
        nonlocal count
        body = match[2]
        if ('MEM32(XBOX_FS_BASE) = esp;' not in body or
                body.count(SAVE_STACK) != 1 or
                not all(f'uint32_t g_{r} = recomp_leaf_ld_{r}()' in body for r in REGS)):
            return match[0]
        labels = list(dict.fromkeys(LABEL.findall(body)))
        if not labels:
            return match[0]
        count += 1
        declaration = ('\n    static const uint32_t sc1_eh_labels[] = {' +
                       ', '.join('0x' + label + 'u' for label in labels) +
                       '};\n    Sc1EhFrame sc1_eh_frame;\n')
        body = declaration + body
        reloads = ' '.join(f'g_{r} = recomp_leaf_ld_{r}();' for r in REGS if r != 'esp')
        cases = '\n'.join(f'        case 0x{label}u: goto loc_{label};' for label in labels)
        landing = '''
    sc1_eh_enter(&sc1_eh_frame, ebp, esp, sc1_eh_labels,
                 sizeof(sc1_eh_labels) / sizeof(sc1_eh_labels[0]));
    if (setjmp(sc1_eh_frame.landing)) {
        ebp = sc1_eh_frame.guest_ebp; g_ebp = ebp; g_seh_ebp = ebp;
        ''' + reloads + '''
        g_esp = sc1_eh_frame.guest_esp;
        switch (sc1_eh_target()) {
''' + cases + '''
        default: abort();
        }
    }
'''
        body = body.replace(SAVE_STACK, SAVE_STACK + landing, 1)
        body = body.replace('return;', '{ sc1_eh_leave(&sc1_eh_frame); return; }')
        return match[0][:match[0].index('{') + 1] + body

    text = FUNCTION.sub(change, text)
    if count:
        text = text.replace('#include <math.h>',
                            '#include <math.h>\n#include "../src/guest_exceptions.h"\n#include <stdlib.h>', 1)
    return text, count


def prepare(staging: Path):
    count = 0
    for path in staging.glob('recomp_*.c'):
        text = path.read_text(encoding='utf-8')
        rewritten, found = instrument(text)
        if found:
            path.write_text(rewritten, encoding='utf-8')
            count += found
    print(f'Prepared {count} recognized guest exception frames', flush=True)
