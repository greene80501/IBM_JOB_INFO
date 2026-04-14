import json

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for job in data:
    d = job.get('details', {})
    if len(d) == 2:
        print('Job', job['job_id'], 'keys:', list(d.keys()))
        print('  Values:', {k: v[:80] for k, v in d.items()})
        break
