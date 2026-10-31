"""Retain the original VM float-greater body across its shared flags tail.

The disassembler labels 0x30006 independently, immediately after TEST AH,41.
A C call to that label loses the local flags. Translate the complete original
entry through both RET 8 instructions; retain every existing dispatch symbol.
"""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]

def prepare(directory):
 sys.path.insert(0,str(ROOT/'private/codegen'))
 from tools.recomp import config
 from tools.recomp.translator import FunctionTranslator
 xbe=ROOT/'Game Files/default.xbe'
 config.configure_from_xbe(str(xbe))
 functions=json.loads((ROOT/'private/disasm/functions.json').read_text(encoding='utf-8'))
 db={int(f['start'],16):dict(f,end=int(f['end'],16)) for f in functions}
 start,end=0x2ff90,0x30023
 translator=FunctionTranslator(xbe.read_bytes(),db)
 info=dict(db[start],end=end,size=end-start)
 recovered=translator.translate_function(start,info)
 if not recovered or 'loc_00030008:' not in recovered or 'if (TEST_NZ(_fa, _fb)) goto loc_00030017;' not in recovered:
  raise RuntimeError('Original float comparison did not retain its flags consumer')
 if 'sub_00030006();' in recovered:raise RuntimeError('Shared comparison tail remains split')
 found=[]
 for path in Path(directory).glob('recomp_*.c'):
  text=path.read_text(encoding='utf-8')
  match=re.search(r'void sub_0002FF90\(void\)\n\{.*?\n\}',text,re.S)
  if not match:continue
  found.append(path)
  text=text[:match.start()]+recovered.rstrip()+text[match.end():]
  if text!=path.read_text(encoding='utf-8'):path.write_bytes(text.encode('utf-8'))
 if len(found)!=1:raise RuntimeError('Expected one original float-greater entry')

if __name__=='__main__':prepare(ROOT/'generated')
