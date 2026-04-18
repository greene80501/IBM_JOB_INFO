from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# The page seems to have article sections
# Let's find the container that holds both headers and fields
main = soup.find('div', class_='article__content') or soup.find('main') or soup.body

# Find all article_header__text and article__content__view__field elements
headers = main.find_all('div', class_='article__header__text')
fields = main.find_all('div', class_='article__content__view__field')

print('Headers:', len(headers))
print('Fields:', len(fields))

# Each header might be followed by fields until the next header
all_elems = sorted(headers + fields, key=lambda e: e.sourceline if e.sourceline else 0)

current_section = 'UNKNOWN'
for elem in all_elems:
    if 'article__header__text' in (elem.get('class') or []):
        h3 = elem.find('h3')
        if h3:
            current_section = h3.get_text(strip=True)
            print('\nSECTION:', current_section)
    else:
        label = elem.find('div', class_='article__content__view__field__label')
        value = elem.find('div', class_='article__content__view__field__value')
        if label and value:
            print('  FIELD:', label.get_text(strip=True), '->', value.get_text(strip=True)[:60])
        elif value:
            print('  TEXT:', value.get_text(strip=True)[:60])
