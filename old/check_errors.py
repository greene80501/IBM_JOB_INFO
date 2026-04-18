import json
with open('ibm_jobs.json','r',encoding='utf-8') as f:
    data=json.load(f)
errors=[j for j in data if 'details_error' in j]
print(f'Jobs with detail errors: {len(errors)}')
for e in errors:
    print(f'  Job {e["job_id"]}: {e["details_error"]}')
