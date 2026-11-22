from html.parser import HTMLParser
import re

html = open(r'D:\DigitalBrain\web_surge\index.html', 'r', encoding='utf-8').read()

# Remove ALL script blocks (JSON-LD + app.js)
html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)

class HTMLValidator(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr'}
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"Mismatched </{tag}> - stack top: {self.stack[-1] if self.stack else 'empty'}")

v = HTMLValidator()
v.feed(html_clean)
if v.errors:
    for e in v.errors[:10]:
        print("ERROR:", e)
elif v.stack:
    print("UNCLOSED:", v.stack)
else:
    print("HTML-STRUCTURE-OK: all tags balanced (scripts excluded)")
