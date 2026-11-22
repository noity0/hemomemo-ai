import urllib.request
import json

# IndexNow submission for both domains
submissions = [
    {
        "host": "noity0.github.io",
        "key": "b1bbdf2eb4384065893293c6c0f241b7",
        "keyLocation": "noity0.github.io/hemomemo-ai/b1bbdf2eb4384065893293c6c0f241b7.txt",
        "urlList": [
            "noity0.github.io/hemomemo-ai/",
            "noity0.github.io/hemomemo-ai/#about",
            "noity0.github.io/hemomemo-ai/#download",
            "noity0.github.io/hemomemo-ai/#demo",
            "noity0.github.io/hemomemo-ai/#sawal-jawab",
            "noity0.github.io/hemomemo-ai/sitemap.xml"
        ]
    },
    {
        "host": "hemomemo-ai.netlify.app",
        "key": "f443cfc6059d4f109a48c6145cbb72f7",
        "keyLocation": "hemomemo-ai.netlify.app/f443cfc6059d4f109a48c6145cbb72f7.txt",
        "urlList": [
            "hemomemo-ai.netlify.app/",
            "hemomemo-ai.netlify.app/#about",
            "hemomemo-ai.netlify.app/#download",
            "hemomemo-ai.netlify.app/#demo",
            "hemomemo-ai.netlify.app/#sawal-jawab",
            "hemomemo-ai.netlify.app/sitemap.xml"
        ]
    }
]

for s in submissions:
    body = json.dumps(s).encode('utf-8')
    req = urllib.request.Request(
        'https://api.indexnow.org/indexnow',
        data=body,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST'
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        print(f"[{s['host']}] Status: {resp.status} - {resp.read().decode()[:200]}")
    except Exception as e:
        print(f"[{s['host']}] FAIL: {e}")

print("INDEXNOW-DONE")
