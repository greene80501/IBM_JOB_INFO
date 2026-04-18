import re, json

with open('main_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    print('Found __NEXT_DATA__')
    print(json.dumps(data, indent=2)[:5000])
else:
    print('__NEXT_DATA__ not found via regex')
    if '__NEXT_DATA__' in html:
        print('But __NEXT_DATA__ string exists elsewhere')
        idx = html.find('__NEXT_DATA__')
        print(html[idx-200:idx+500])
    else:
        print('__NEXT_DATA__ not present in HTML at all')
