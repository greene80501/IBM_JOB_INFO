from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

main = soup.find('main')
if main:
    print('Fields in main:', len(main.find_all('div', class_='article__content__view__field')))
    print('Headers in main:', len(main.find_all('summary', class_='article__header')))
else:
    print('No main found')
