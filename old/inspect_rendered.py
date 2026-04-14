import re

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

print(f'HTML length: {len(html)}')

# Check if __next div has content
m = re.search(r'<div id="__next">(.*?)</div>', html, re.DOTALL)
if m:
    print('__next content:', repr(m.group(1)[:500]))
else:
    print('__next not found')

# Check for any text mentioning job or result
if 'result' in html.lower():
    print('Contains result')
if 'job' in html.lower():
    print('Contains job')

# Find all links
links = re.findall(r'href="([^"]+)"', html)
job_links = [l for l in links if 'job' in l.lower()]
print(f'Job links found: {len(job_links)}')
for l in job_links[:10]:
    print(l)
