from bs4 import BeautifulSoup

with open('job_detail.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Print basic structure info
print(f'HTML length: {len(html)}')

# Look for common job detail fields
fields = {
    'title': soup.find('title'),
    'h1': soup.find('h1'),
    'h2': soup.find('h2'),
}

for name, elem in fields.items():
    if elem:
        print(f'{name}: {elem.get_text(strip=True)}')

# Look for job description
# Often in specific divs or sections
print('\n--- Looking for description containers ---')
for cls in ['job-description', 'description', 'jd', 'details', 'content', 'main']:
    elems = soup.find_all(class_=lambda x: x and cls in ' '.join(x).lower())
    if elems:
        print(f'Found {len(elems)} elements with class containing "{cls}"')
        for el in elems[:2]:
            text = el.get_text(strip=True, separator='\n')[:500]
            print(f'  Sample text: {text}')

# Look for structured data
print('\n--- Looking for JSON-LD ---')
scripts = soup.find_all('script', type='application/ld+json')
for s in scripts:
    print(s.string[:1000] if s.string else 'empty')

# Look for specific text patterns like "Location", "Category", etc.
print('\n--- Looking for metadata labels ---')
for label in ['Location:', 'Category:', 'Job type:', 'Schedule:', 'Position type:', 'Country:', 'City:', 'State:', 'Zip Code:', 'Req ID:', 'Job ID:']:
    if label in html:
        # Find the element containing this label
        elem = soup.find(string=lambda text: text and label in text)
        if elem:
            parent = elem.parent
            print(f'{label} found in {parent.name}, text: {parent.get_text(strip=True)[:200]}')
