from bs4 import BeautifulSoup

with open('main_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script', src=True)
print('All external scripts:')
for s in scripts:
    print(s['src'])
