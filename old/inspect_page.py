import requests, re, json

url = 'https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States'
r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'})
text = r.text

# Look for any URLs containing api, search, job, career
api_urls = re.findall(r'https?://[^\s"\'<>]+', text)
job_apis = [u for u in api_urls if any(x in u.lower() for x in ['job','career','search','api']) and 'ibm' in u.lower()]
print('Job/Career/API URLs found:')
for u in set(job_apis):
    print(u)

# Look for data attributes in HTML
data_attrs = re.findall(r'data-[a-z-]+=', text)
unique_attrs = sorted(set(data_attrs))
print('\nData attributes (sample):')
for a in unique_attrs[:30]:
    print(a)

# Check for inline JSON in scripts with job data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', text, re.DOTALL)
for i, script in enumerate(scripts):
    if 'job' in script.lower() or 'search' in script.lower() or 'career' in script.lower():
        if len(script) > 5000:
            print(f'\nScript {i} is long ({len(script)} chars), checking for JSON...')
            try:
                jsons = re.findall(r'\{[\s\S]*?"title"[\s\S]*?\}', script)
                print(f'  Found {len(jsons)} potential JSON objects with title')
                if jsons:
                    print(jsons[0][:500])
            except Exception as e:
                pass

# Also save HTML for inspection
with open('main_page.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('\nSaved main_page.html')
