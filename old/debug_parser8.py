import importlib
import ibm_jobs_scraper
importlib.reload(ibm_jobs_scraper)
from ibm_jobs_scraper import JobDetailParser

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

parser = JobDetailParser(html)
data, err = parser.parse()
print('Error:', err)
print('Keys:', list(data.keys()))
for k in ['life_at_ibm', 'about_ibm', 'equal_opportunity', 'benefits', 'visa_policy', 'compensation_policy']:
    v = data.get(k)
    if v:
        print(k, ':', v.replace('\n', ' ')[:100])
    else:
        print(k, ': MISSING')
