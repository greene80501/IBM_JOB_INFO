from bs4 import BeautifulSoup

with open('rendered_page.html','r',encoding='utf-8') as f:
    html=f.read()

soup = BeautifulSoup(html, 'html.parser')

# Look for the main search results container
# The embedded search component likely has specific classes
containers = soup.find_all(class_=lambda x: x and any(term in ' '.join(x).lower() for term in ['result', 'item', 'card', 'job']))
print(f'Found {len(containers)} elements with result/item/card/job in class')

# Let's look for links to careers.ibm.com/careers/JobDetail
job_links = soup.find_all('a', href=lambda x: x and 'JobDetail' in x)
print(f'\nFound {len(job_links)} JobDetail links')

for i, link in enumerate(job_links[:10]):
    # Traverse up to find the card/container
    parent = link
    for _ in range(5):
        if parent:
            parent = parent.parent
            # Check if this parent contains location or other metadata
            text = parent.get_text(strip=True, separator=' | ')
            if len(text) > 20:
                print(f'\nJob {i+1}: {text[:300]}')
                print('  HREF:', link.get('href'))
                break
