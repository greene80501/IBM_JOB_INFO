from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

article = soup.find("article") or soup.find("main") or soup.body
print('Article tag:', article.name if article else None)
print('Article classes:', article.get('class') if article else None)

fields_in_article = article.find_all("div", class_="article__content__view__field") if article else []
fields_in_soup = soup.find_all("div", class_="article__content__view__field")
headers_in_article = article.find_all("summary", class_="article__header") if article else []
headers_in_soup = soup.find_all("summary", class_="article__header")

print('Fields in article:', len(fields_in_article))
print('Fields in soup:', len(fields_in_soup))
print('Headers in article:', len(headers_in_article))
print('Headers in soup:', len(headers_in_soup))
