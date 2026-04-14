from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the article content container
container = soup.find('div', class_='article__content__view')
if not container:
    print('No article__content__view found')
    # Try to find the main content area
    container = soup.body

# Iterate direct children or all children in order
for elem in container.children:
    if not elem.name:
        continue
    if elem.name == 'h3':
        print('H3:', elem.get_text(strip=True))
    elif 'article__content__view__field' in (elem.get('class') or []):
        label = elem.find('div', class_='article__content__view__field__label')
        if label:
            print('  FIELD:', label.get_text(strip=True))
        else:
            # Show first 80 chars of value
            val = elem.find('div', class_='article__content__view__field__value')
            if val:
                text = val.get_text(strip=True)[:80]
                print('  UNLABELED:', text)
