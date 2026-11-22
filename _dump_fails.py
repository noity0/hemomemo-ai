import io
txt = io.open(r'D:\Opencode\data\opencode\shell\aa3e2151d6fdd2cf9e07be809ee756ffc0da29e7\sh_final_coding.out', encoding='utf-8', errors='ignore').read()
lines = txt.splitlines()
fails = []
cur = None
for l in lines:
    if l.startswith('  FAIL ['):
        cur = l.strip()
        fails.append((l.strip(), ''))
    elif cur is not None and l.startswith('      -> '):
        fails[-1] = (cur, l.strip())
        cur = None
print('PRINTED-FAILS-COUNT:', len(fails))
for c, d in fails:
    try:
        num, q = c.split('] ', 1)
        qn = q.strip()
    except Exception:
        qn = c
    print('[%s] %s' % (c[6:9], qn[:95]))
    print('    %s' % d[:150].replace(chr(10), ' | '))
