from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Get all interesting elements in document order
all_fields = soup.find_all('div', class_='article__content__view__field')
all_details = soup.find_all('details')
all_headers = soup.find_all('summary', class_='article__header')

all_elems = sorted(
    [(e, 'FIELD') for e in all_fields] + 
    [(e, 'DETAILS') for e in all_details] + 
    [(e, 'HEADER') for e in all_headers],
    key=lambda x: x[0].sourceline if x[0].sourceline else 0
)

for elem, kind in all_elems:
    if kind == 'FIELD':
        label = elem.find('div', class_='article__content__view__field__label')
        text = label.get_text(strip=True) if label else elem.get_text(strip=True)[:40]
        print(f'{kind}: {text}')
    elif kind == 'HEADER':
        h3 = elem.find('h3')
        text = h3.get_text(strip=True) if h3 else 'UNKNOWN'
        print(f'{kind}: {text}')
    else:
        h3 = elem.find('h3')
        text = h3.get_text(strip=True) if h3 else 'UNKNOWN'
        print(f'{kind}: {text}')
