import urllib.request

def check(url, label, checks):
    try:
        c = urllib.request.urlopen(url, timeout=30).read().decode()
        results = [f"{k}:{v in c}" for k, v in checks.items()]
        print(f"{label}: " + " | ".join(results))
    except Exception as e:
        print(f"{label}: FAIL {e}")

check('https://noity0.github.io/hemomemo-ai/', 'Pages', {
    'v4.2.1': '4.2.1-people',
    '8-JSON-LD': '"Dataset"',
    'AnswerBlocks': 'answer-block',
    'FAQ-Answers': 'faq-answers',
    'Preconnects': 'preconnect',
    'Organization': '"Organization"',
    'Product': '"Product"',
    'Speakable': 'SpeakableSpecification',
    'Article-tag': '<article',
    'Main-tag': '<main',
    'GPTBot': 'GPTBot',
})

check('https://noity0.github.io/hemomemo-ai/robots.txt', 'Robots', {
    'GPTBot': 'GPTBot',
    'ClaudeBot': 'ClaudeBot',
    'Perplexity': 'PerplexityBot',
})

check('https://noity0.github.io/hemomemo-ai/sitemap.xml', 'Sitemap', {
    'hreflang': 'hreflang',
    'image': '<image:',
})
