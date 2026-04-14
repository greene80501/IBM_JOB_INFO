from bs4 import BeautifulSoup

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Search for all buttons and links after the job listings container
results_container = soup.find(id='ibm-hits-wrapper')
if results_container:
    # Get all next siblings
    next_elems = []
    sibling = results_container.next_sibling
    while sibling:
        if sibling.name:
            next_elems.append(sibling)
        sibling = sibling.next_sibling
    print(f'Siblings after results: {len(next_elems)}')
    for el in next_elems:
        print(f'<{el.name}> classes={el.get("class")} text={el.get_text(strip=True)[:200]}')

# Also look within the parent for pagination
parent = results_container.parent if results_container else None
if parent:
    print('\n--- Parent contents ---')
    for child in parent.children:
        if child.name:
            print(f'<{child.name}> classes={child.get("class")}')

# Look for any nav or buttons with numbers
print('\n--- Number buttons ---')
import re
for btn in soup.find_all(['button', 'a', 'li']):
    text = btn.get_text(strip=True)
    if text.isdigit() or text in ['Next', 'Previous', '»', '«']:
        print(f'{btn.name}: "{text}" classes={btn.get("class")}')
