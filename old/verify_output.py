import json
from collections import Counter

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total jobs: {len(data)}')

# Check detail errors
errors = [j for j in data if j.get('detail_error')]
print(f'Jobs with detail errors: {len(errors)}')
for j in errors:
    print(f'  {j["id"]}: {j["detail_error"]}')

# Check fields present
all_keys = Counter()
for job in data:
    for k in job.keys():
        all_keys[k] += 1

print('\n=== Field coverage ===')
for k, count in all_keys.most_common():
    print(f'{k}: {count}/{len(data)}')

# Check salary ranges
print('\n=== Salary stats ===')
salaries = [(j['id'], j.get('salary_min'), j.get('salary_max')) for j in data if j.get('salary_min')]
print(f'Jobs with salary data: {len(salaries)}')
for jid, smin, smax in salaries[:10]:
    print(f'  {jid}: ${smin:,} - ${smax:,}')

# Check location data for "Multiple Cities"
print('\n=== Multiple Cities check ===')
multi = [j for j in data if j.get('location_summary') == 'Multiple Cities']
print(f'Jobs with "Multiple Cities": {len(multi)}')
for j in multi[:10]:
    cities = j.get('cities', [])
    states = j.get('states', [])
    print(f'  {j["id"]} {j["title"]} -> cities={cities} states={states}')

# Check date formats
print('\n=== Date samples ===')
for j in data[:10]:
    print(f'  {j["id"]}: posted_at={j.get("posted_at")}')

# Check commission_role values
print('\n=== Commission role values ===')
comm_vals = Counter()
for j in data:
    v = j.get('commission_role')
    comm_vals[str(v)] += 1
for v, c in comm_vals.most_common():
    print(f'  {v}: {c}')

# Check work_type values
print('\n=== Work arrangement values ===')
wt = Counter()
for j in data:
    wt[j.get('work_type', 'NULL')] += 1
for v, c in wt.most_common():
    print(f'  {v}: {c}')
