import re

with open('main_page.html','r',encoding='utf-8') as f:
    html=f.read()

# Find all script src
srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
print('Relevant script srcs:')
for src in srcs:
    if any(x in src.lower() for x in ['career','search','widget','hybrid','next','chunk']):
        print(src)

# Also search for any URL patterns in all inline scripts that might be API endpoints
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
urls = set()
for script in scripts:
    found = re.findall(r'https?://[^\s"\'<>]+', script)
    urls.update(found)

print('\nPotential API URLs:')
for u in urls:
    if any(x in u.lower() for x in ['api','search','career','job','json']):
        print(u)
