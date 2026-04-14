from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

field = soup.find('div', class_='article__content__view__field')
header = soup.find('summary', class_='article__header')

for elem, name in [(field, 'field'), (header, 'header')]:
    print(f'=== {name} ancestors ===')
    parent = elem
    for i in range(8):
        parent = parent.parent
        if not parent:
            break
        print(f'  {i}: <{parent.name}> classes={parent.get("class")}')
