from bs4 import BeautifulSoup

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Look for pagination elements
pagination = soup.find_all(class_=lambda x: x and any(term in ' '.join(x).lower() for term in ['pagination', 'pager', 'page']))
print(f'Pagination-like elements: {len(pagination)}')
for el in pagination[:10]:
    print('  classes:', el.get('class'))
    print('  text:', el.get_text(strip=True, separator=' ')[:200])

# Look for next/prev buttons
for text in ['Next', 'Previous']:
    elems = soup.find_all(string=lambda s: s and text == s.strip())
    print(f'"{text}" strings: {len(elems)}')
    for elem in elems[:3]:
        parent = elem.parent
        print(f'  Parent tag: {parent.name}, classes: {parent.get("class")}, disabled: {parent.get("disabled")}')

# Check for page number indicators
import re
page_indicators = soup.find_all(string=lambda s: s and re.search(r'\d+\s*[-–]\s*\d+\s+of\s+\d+', s))
print(f'Page indicators: {len(page_indicators)}')
for p in page_indicators:
    print(' ', p.strip())
