from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find h3 and go up to see parent structure
h3 = soup.find('h3')
if h3:
    parent = h3.parent
    print('h3 parent:', parent.name, parent.get('class'))
    grandparent = parent.parent
    print('h3 grandparent:', grandparent.name, grandparent.get('class'))
    
    # Show all children of grandparent
    print('\nChildren of grandparent:')
    for child in grandparent.children:
        if child.name:
            print(' ', child.name, child.get('class'))

# Find one field and go up
field = soup.find('div', class_='article__content__view__field')
if field:
    parent = field.parent
    print('\nfield parent:', parent.name, parent.get('class'))
    grandparent = parent.parent
    print('field grandparent:', grandparent.name, grandparent.get('class'))
