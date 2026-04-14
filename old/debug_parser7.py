from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
root = soup.find("main") or soup

fields = root.find_all("div", class_="article__content__view__field")
headers = root.find_all("summary", class_="article__header")
elems = sorted(fields + headers, key=lambda e: e.sourceline if e.sourceline else 0)

print('Total elems:', len(elems))
for elem in elems:
    if elem.name == 'summary':
        h3 = elem.find('h3')
        print('HEADER:', h3.get_text(strip=True) if h3 else 'NO H3')
    else:
        label = elem.find('div', class_='article__content__view__field__label')
        if label:
            print('  labeled:', label.get_text(strip=True))
        else:
            val = elem.find('div', class_='article__content__view__field__value')
            text = val.get_text(strip=True)[:40] if val else 'NO VALUE'
            print('  unlabeled:', text)
