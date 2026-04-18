from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all fields and see if they have a parent details element
fields = soup.find_all('div', class_='article__content__view__field')
for field in fields:
    label = field.find('div', class_='article__content__view__field__label')
    if label:
        label_text = label.get_text(strip=True)
        # Find nearest ancestor details
        parent_details = field.find_parent('details')
        if parent_details:
            h3 = parent_details.find('h3')
            section = h3.get_text(strip=True) if h3 else 'UNKNOWN'
        else:
            section = 'NO DETAILS PARENT'
        print(f'FIELD: {label_text} -> SECTION: {section}')
