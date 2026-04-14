from bs4 import BeautifulSoup

with open('job_detail.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all h3s and their following siblings
h3s = soup.find_all('h3')
print('=== Sections (h3) ===')
for h3 in h3s:
    print(f'\n{h3.get_text(strip=True)}')
    # Look at parent's siblings or children
    parent = h3.parent
    if parent:
        # Find article__content__view__field within same section
        fields = parent.find_all(class_='article__content__view__field')
        for field in fields[:10]:
            text = field.get_text(strip=True, separator=' | ')
            print(f'  Field: {text[:300]}')

# Also look for direct label/value pairs
print('\n=== All article fields ===')
fields = soup.find_all(class_='article__content__view__field')
print(f'Total fields: {len(fields)}')
for i, field in enumerate(fields[:20]):
    text = field.get_text(strip=True, separator=' | ')
    print(f'{i+1}. {text[:200]}')

# Look for metadata table or list
print('\n=== Looking for metadata ===')
for tag in ['table', 'dl', 'ul']:
    elems = soup.find_all(tag)
    print(f'{tag}: {len(elems)}')
    for el in elems[:3]:
        text = el.get_text(strip=True, separator=' | ')[:200]
        classes = el.get('class', [])
        print(f'  classes={classes} text={text}')
