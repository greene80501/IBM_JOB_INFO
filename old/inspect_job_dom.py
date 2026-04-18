from bs4 import BeautifulSoup

with open('job_detail.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

fields = soup.find_all(class_='article__content__view__field')
print(f'Total fields: {len(fields)}')

for i, field in enumerate(fields[:25]):
    print(f'\n--- Field {i+1} ---')
    print(field.prettify()[:800])
    # Check direct children
    children = list(field.children)
    print(f'Direct children tags: {[c.name for c in children if c.name]}')
