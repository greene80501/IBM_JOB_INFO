import requests

url = 'https://careers.ibm.com/careers/JobDetail?jobId=55102&source=WEB_Search_NA'

headers_list = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.ibm.com/careers/search',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.ibm.com/careers/search',
        'DNT': '1',
        'Connection': 'keep-alive',
    },
]

for i, headers in enumerate(headers_list):
    r = requests.get(url, headers=headers)
    print(f'Test {i+1}: status={r.status_code}')
    if r.status_code == 200:
        print('  OK! len=', len(r.text))
    else:
        print('  Failed:', r.text[:200])
