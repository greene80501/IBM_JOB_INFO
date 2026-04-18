import json

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

missing = [j for j in data if not j.get('details')]
print('Jobs missing details:', len(missing))
for j in missing[:10]:
    print(' ', j['job_id'], j['title'])
    if 'details_error' in j:
        print('    Error:', j['details_error'])
