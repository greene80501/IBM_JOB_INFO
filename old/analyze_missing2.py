import json

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count jobs where details dict exists but has fewer than expected keys
for job in data:
    d = job.get('details', {})
    if len(d) < 10:
        print(job['job_id'], 'has', len(d), 'detail keys')
        print('  Title:', job['title'])
        if 'details_error' in job:
            print('  Error:', job['details_error'])
