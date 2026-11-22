import urllib.request

checks = [
    ('https://hemomemo-ai.netlify.app/', 'index', None),
    ('https://hemomemo-ai.netlify.app/robots.txt', 'robots', None),
    ('https://hemomemo-ai.netlify.app/sitemap.xml', 'sitemap', None),
]

for url, label, _ in checks:
    try:
        c = urllib.request.urlopen(url).read().decode()
        if label == 'index':
            v421 = c.count('4.2.1-people')
            about = 'Hemomemo AI Kya Hai' in c
            jsonld = c.count('ld+json')
            bc = 'BreadcrumbList' in c
            wa = 'WebApplication' in c
            print(f'{label}: 4.2.1={v421} About={about} JSON-LD={jsonld} Breadcrumb={bc} WebApp={wa}')
        elif label == 'robots':
            print(f'{label}: Googlebot={"Googlebot" in c}')
        elif label == 'sitemap':
            print(f'{label}: <loc> count={c.count("<loc>")}')
    except Exception as e:
        print(f'{label}: FAIL {e}')
