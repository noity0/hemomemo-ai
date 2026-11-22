# -*- coding: utf-8 -*-
"""Config me OWNER ki key set (donO opencode.json) — bat wale code-path jaisa."""
import json

KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"
assert KEY.startswith("hemo") and len(KEY) > 20, "key format ghalat"

for path in (r"D:\Opencode\config\opencode\opencode.json",
             r"C:\Users\user\.config\opencode\opencode.json"):
    d = json.load(open(path, encoding="utf-8"))
    d["provider"]["hemomemo"]["options"]["apiKey"] = KEY
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    h = json.load(open(path, encoding="utf-8"))["provider"]["hemomemo"]
    print(path, "->", h["options"]["baseURL"], "|",
          h["options"]["apiKey"][:14] + "(hidden)",
          "| freellmapi:", "freellmapi" in json.load(open(path,
                                                          encoding="utf-8"))["provider"])
