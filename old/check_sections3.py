from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find h3s
h3s = soup.find_all('h3')
print(f'h3s found: {len(h3s)}')
for h in h3s:
    print('H3:', h.get_text(strip=True))
    # Show parent class
    print('  Parent:', h.parent.name, h.parent.get('class'))
    # Show next sibling
    nxt = h.find_next_sibling()
    if nxt:
        print('  Next sibling:', nxt.name, nxt.get('class'))
