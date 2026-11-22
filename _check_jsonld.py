import json, re
html = open(r'D:\DigitalBrain\web_surge\index.html', 'r', encoding='utf-8').read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print(f'Found {len(blocks)} JSON-LD blocks')
for i, b in enumerate(blocks):
    try:
        d = json.loads(b)
        if '@type' in d:
            t = d['@type']
        elif '@graph' in d:
            t = 'graph: ' + ', '.join(g.get('@type','?') for g in d['@graph'])
        else:
            t = 'unknown'
        print(f'  [{i}] {t} - VALID')
    except json.JSONDecodeError as e:
        print(f'  [{i}] INVALID: {e}')
