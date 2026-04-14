import json

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for job in data[:5]:
    d = job.get('details', {})
    if 'additional_content' in d:
        print('=== Job', job['job_id'], '===')
        print(d['additional_content'][:500])
        print()
