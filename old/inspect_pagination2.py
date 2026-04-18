from bs4 import BeautifulSoup

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the text "1 – 30 of 156 items" and look at its parent
indicator = soup.find(string=lambda s: s and '1' in s and '30' in s and '156' in s)
if indicator:
    print('Indicator text:', indicator.strip())
    parent = indicator.parent
    for depth in range(5):
        print(f'Depth {depth}: <{parent.name}> classes={parent.get("class")}')
        print(parent.prettify()[:500])
        parent = parent.parent
        if not parent:
            break
