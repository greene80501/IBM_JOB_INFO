from ibm_jobs_scraper import JobDetailParser

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

parser = JobDetailParser(html)
data, err = parser.parse()
print('Error:', err)
print('Keys:', list(data.keys()))
for k, v in data.items():
    if isinstance(v, list):
        print(k, ':', v)
    else:
        preview = str(v).replace('\n', ' ')[:100]
        print(k, ':', preview)
