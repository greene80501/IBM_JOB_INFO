from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the commission field
for field in soup.find_all('div', class_='article__content__view__field'):
    label = field.find('div', class_='article__content__view__field__label')
    if label:
        text = label.get_text(separator=' ', strip=True)
        lower = text.lower()
        if 'commission' in lower:
            print('Found label:', repr(text))
            print('Lower:', repr(lower))
            value = field.find('div', class_='article__content__view__field__value')
            if value:
                print('Value:', repr(value.get_text(strip=True)))
