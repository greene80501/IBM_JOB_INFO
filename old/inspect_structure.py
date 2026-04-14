from bs4 import BeautifulSoup

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')
job_links = soup.find_all('a', href=lambda x: x and 'JobDetail' in x)

# Look at the HTML structure around the first job link
first_link = job_links[0]
print('First job link HTML:')
print(first_link.prettify()[:800])
print('\n--- Parents ---')
parent = first_link
for depth in range(1, 6):
    parent = parent.parent
    print(f'Depth {depth}: <{parent.name}> classes={parent.get("class")} id={parent.get("id")}')
    print(parent.prettify()[:600])
    print()
