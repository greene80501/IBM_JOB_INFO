from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

main = soup.find('main')
details_in_main = main.find_all('details') if main else []
print('Details in main:', len(details_in_main))

# Check if any details are outside main
all_details = soup.find_all('details')
outside = [d for d in all_details if d not in details_in_main]
print('Details outside main:', len(outside))

# Also check section js_views
section = soup.find('section', class_='js_views')
if section:
    print('Fields in section:', len(section.find_all('div', class_='article__content__view__field')))
    print('Headers in section:', len(section.find_all('summary', class_='article__header')))
    print('Details in section:', len(section.find_all('details')))
