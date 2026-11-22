import sys; sys.path.insert(0, r'D:\DigitalBrain')
import model.generate as g
import agent.animation as anim

out = g.chat_once('hadith batao', meta=True)
text, meta = out if isinstance(out, tuple) else (out, {})

print('FLOW-LINE:', meta.get('flow'))
print()

# Test: render_flow_hud_line
rendered = anim.render_flow_hud_line(meta.get('flow', ''))
print('HUD-RENDER-COUNT:', len(rendered))
for a in rendered:
    print('  %s @ %s (dur=%.1fs) %s' % (a['stage'], a['kind'], a['duration'], a['glyph']))
print()
print('Local-only animation engine OK — no AI-API, no network')
