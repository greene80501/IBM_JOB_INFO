from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all article__header elements
headers = soup.find_all('summary', class_='article__header')
print('Headers found:', len(headers))

for header in headers:
    h3 = header.find('h3')
    section_name = h3.get_text(strip=True) if h3 else 'UNKNOWN'
    print('\nSECTION:', section_name)
    
    # The content might be the next sibling of the parent details element
    parent = header.parent
    if parent and parent.name == 'details':
        # Find the content div inside this details
        content = parent.find('div', class_='article__content')
        if content:
            fields = content.find_all('div', class_='article__content__view__field')
            for field in fields:
                label = field.find('div', class_='article__content__view__field__label')
                value = field.find('div', class_='article__content__view__field__value')
                if label and value:
                    print('  FIELD:', label.get_text(strip=True), '->', value.get_text(strip=True)[:60])
                elif value:
                    print('  TEXT:', value.get_text(strip=True)[:60])
