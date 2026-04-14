import re

with open('main_page.html','r',encoding='utf-8') as f:
    html=f.read()

next_files = re.findall(r'/_next/[^"\'<>\s]+', html)
print('Next.js static files:')
for f in set(next_files):
    print(f)

scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print('\nFetch/axios calls:')
for script in scripts:
    if 'fetch(' in script or 'axios' in script:
        lines = script.split('\n')
        for line in lines:
            if 'fetch(' in line or 'axios' in line:
                print(line.strip()[:300])
