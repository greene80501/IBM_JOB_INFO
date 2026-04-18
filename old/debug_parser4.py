from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all details elements and see if they contain fields
details = soup.find_all('details')
print('Total details:', len(details))
for i, d in enumerate(details):
    h3 = d.find('h3')
    title = h3.get_text(strip=True) if h3 else 'NO H3'
    fields = d.find_all('div', class_='article__content__view__field')
    print(f'Details {i} ({title}): {len(fields)} fields')
    for f in fields[:3]:
        label = f.find('div', class_='article__content__view__field__label')
        if label:
            print('  labeled:', label.get_text(strip=True))
        else:
            val = f.find('div', class_='article__content__view__field__value')
            if val:
                print('  unlabeled:', val.get_text(strip=True)[:60])
