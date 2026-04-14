import re

with open('main_page.html','r',encoding='utf-8') as f:
    html=f.read()

for term in ['loadHybridCloudWidget', 'loadHybridCloudWidgets', 'instanceId', 'renderFunctionName']:
    if term in html:
        print(f'Found {term}')
        idx = html.find(term)
        print(html[idx-100:idx+300])
        print('---')

# Search for any JSON objects that might be widget configs
json_matches = re.findall(r'\{[^}]*"renderFunctionName"[^}]*\}', html)
print(f'Widget config objects: {len(json_matches)}')
for m in json_matches[:5]:
    print(m)
