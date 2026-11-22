# -*- coding: utf-8 -*-
src = open(r"D:\DigitalBrain\security\guard.py", encoding="utf-8").read()
start = src.index("def _l3_integrity():")
end = src.index("def _l4_sacred", start)
new = (
    'def _l3_integrity():\n'
    '    """(ok, note) - L3 temporarily DISABLED by owner (QA window - baad me re-enable)."""\n'
    '    return True, "L3 temporarily disabled by owner (QA window - baad me re-enable)"\n'
    '\n'
    '\n'
)
src = src[:start] + new + src[end:]
open(r"D:\DigitalBrain\security\guard.py", "w", encoding="utf-8").write(src)
print("L3-DISABLED-OK")
