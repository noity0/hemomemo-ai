# _test_canvas_chat.ps1 ke pyar-se: python-side canvas-chat draw-test
import os, sys, importlib.util
spec = importlib.util.spec_from_file_location("hemomemo_app", r"D:\DigitalBrain\app\hemomemo_app.py")
m = importlib.util.module_from_spec(spec)
sys.modules["hemomemo_app"] = m
spec.loader.exec_module(m)          # no mainloop (sirf import)
import tkinter as tk

app = m.HemomemoApp()
app.withdraw()                       # offscreen
app.update_idletasks()

# 1) user-bubble
app._bubble("Assalam-o-Alaikum! circle ka area nikalna hai r=5", "user")
app.update_idletasks()
# 2) AI-bubble WITH code-fence
ai = ("Ji! Area = pi r^2.\n\n"
      "```python\n"
      "import math\n"
      "r = 5\n"
      "area = math.pi * r ** 2\n"
      "print('Area:', round(area, 2))\n"
      "```\n"
      "Jawab: 78.54 (approx). Koi aur sawal?")
app._bubble(ai, "ai")
app.update_idletasks()
print("code-bubble items=%s | y-cursor=%s" % (len(app.chat.find_all()), app._cb_y))
# 3) chip
app._chip({"source": "local-numpy", "intent": "math", "verify": "3-checks"})
app.update_idletasks()
# 4) think on/off
app._think_start(); app.update_idletasks()
app._think_stage("📚 ilm"); app.update_idletasks()
app._think_stop();  app.update_idletasks()
# 5) welcome + clear + rerender
app._chat_clear(); app.update_idletasks()
app._hist_load();  app.update_idletasks()
app._cb_on_resize(); app.update()
# counts
items = len(app.chat.find_all())
sr = app.chat.cget("scrollregion")
app.destroy()
print("CANVAS-TEST-PASS | items=%s | scrollregion=%s" % (items, str(sr)[:80]))
