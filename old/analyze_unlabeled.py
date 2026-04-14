import json

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# We need to look at the raw HTML of a few jobs to see the unlabeled field patterns
# But since we only have the parsed data, let's look at the first 200 chars of additional_content
print('=== additional_content first 200 chars for 10 jobs ===')
for job in data[:10]:
    d = job.get('details', {})
    ac = d.get('additional_content', '')
    if ac:
        print(job['job_id'], ':', ac[:200].replace('\n', ' '))
        print()
