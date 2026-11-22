import re
html = open(r'D:\DigitalBrain\web_surge\index.html', 'r', encoding='utf-8').read()
opens = len(re.findall(r'<script\b', html))
closes = len(re.findall(r'</script>', html))
print(f"<script opens: {opens}")
print(f"</script> closes: {closes}")
if opens == closes:
    print("SCRIPT-OK: balanced")
else:
    print(f"MISMATCH: {opens} opens vs {closes} closes")
