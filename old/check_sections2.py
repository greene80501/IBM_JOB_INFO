from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the main article content
article = soup.find('article') or soup.find('div', class_='article') or soup.body

# Find all h3 and field divs and order them by document position
h3s = article.find_all('h3')
fields = article.find_all('div', class_='article__content__view__field')

all_elems = sorted(h3s + fields, key=lambda e: e.sourceline if hasattr(e, 'sourceline') else 0)

for elem in all_elems:
    if elem.name == 'h3':
        print('SECTION:', elem.get_text(strip=True))
    else:
        label = elem.find('div', class_='article__content__view__field__label')
        if label:
            print('  FIELD:', label.get_text(strip=True))
        else:
            val = elem.find('div', class_='article__content__view__field__value')
            if val:
                text = val.get_text(strip=True)[:80]
                print('  TEXT:', text)
