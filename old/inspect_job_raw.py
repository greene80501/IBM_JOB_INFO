from bs4 import BeautifulSoup

with open('job_detail.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Look for iframes
iframes = soup.find_all('iframe')
print(f'Iframes: {len(iframes)}')
for iframe in iframes:
    print('  src:', iframe.get('src'))

# Look for all h2, h3, h4 elements
print('\n--- Headers ---')
for tag in ['h2', 'h3', 'h4']:
    elems = soup.find_all(tag)
    print(f'{tag}s: {len(elems)}')
    for el in elems[:5]:
        print(f'  {el.get_text(strip=True)}')

# Look for all divs with text content > 100 chars
print('\n--- Large text divs ---')
for div in soup.find_all('div'):
    text = div.get_text(strip=True)
    if len(text) > 200 and len(text) < 800:
        # Check if it looks like a job description
        if any(word in text.lower() for word in ['responsibilities', 'requirements', 'qualifications', 'description', 'overview', 'ibm']):
            classes = div.get('class', [])
            print(f'Classes: {classes}')
            print(f'Text: {text[:400]}')
            print('---')

# Search for specific IBM job detail patterns
print('\n--- Pattern search ---')
import re
patterns = ['Job Description', 'Required Technical and Professional Expertise', 'Preferred Technical and Professional Expertise', 'Your Role and Responsibilities', 'Introduction', 'About Business Unit']
for pattern in patterns:
    if pattern in html:
        print(f'Found: {pattern}')
