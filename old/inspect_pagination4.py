from bs4 import BeautifulSoup

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all pagination page links
pages = soup.find_all('a', class_='cds--pagination-nav__page')
print(f'Page links found: {len(pages)}')
for p in pages:
    print(f'  Page {p.get_text(strip=True)}: classes={p.get("class")}')

# Check if there's an overflow menu indicating more pages
overflow = soup.find_all(class_='cds--pagination-nav__list-item')
print(f'Pagination items: {len(overflow)}')
for item in overflow:
    print(f'  {item.get_text(strip=True)} classes={item.get("class")}')
