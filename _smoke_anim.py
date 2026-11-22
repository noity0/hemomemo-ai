import sys, time; sys.path.insert(0, r'D:\DigitalBrain')
import model.generate as g
out = g.chat_once('hadith batao', meta=True)
text, meta = out if isinstance(out, tuple) else (out, {})
print('FLOW:', meta.get('flow'))
print('ANIM-STAGES:', meta.get('anim_stages'))
anims = meta.get('animation') or []
print('ANIM-COUNT:', len(anims))
for a in anims:
    print('  ANIM:', a.get('stage'), a.get('kind'), a.get('glyph'), 'dur=%.1f' % a.get('duration'))
print('SRC:', meta.get('source'))
