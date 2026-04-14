import json
from collections import Counter

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Total jobs:', len(data))

# Analyze all detail keys
all_keys = Counter()
for job in data:
    for k in job.get('details', {}).keys():
        all_keys[k] += 1

print('\n=== All detail fields ===')
for k, count in all_keys.most_common():
    print(k + ':', count)

# Look at salary fields
print('\n=== Salary samples ===')
for job in data[:20]:
    d = job.get('details', {})
    min_sal = d.get('projected_minimum_salary_per_year', '')
    max_sal = d.get('projected_maximum_salary_per_year', '')
    if min_sal or max_sal:
        print(job['job_id'], ': min=', min_sal, ' max=', max_sal, sep='')

# Look at encoding issues
print('\n=== Encoding issues check ===')
for job in data[:10]:
    d = job.get('details', {})
    for k, v in list(d.items())[:10]:
        if '�' in str(v):
            print(job['job_id'], k, ':', v[:100])

# Look at location fields
print('\n=== Location samples ===')
for job in data[:10]:
    d = job.get('details', {})
    city = d.get('city_township_village', '')
    state = d.get('state_province', '')
    country = d.get('country', '')
    if city or state or country:
        print(job['job_id'], ': city=', city, ' | state=', state, ' | country=', country, sep='')

# Look at all values for specific fields to understand variety
print('\n=== Employment type values ===')
vals = Counter()
for job in data:
    v = job.get('details', {}).get('employment_type', '')
    vals[v] += 1
for v, c in vals.most_common():
    print(' ', repr(v), ':', c)

print('\n=== Contract type values ===')
vals = Counter()
for job in data:
    v = job.get('details', {}).get('contract_type', '')
    vals[v] += 1
for v, c in vals.most_common():
    print(' ', repr(v), ':', c)

print('\n=== Work arrangement values ===')
vals = Counter()
for job in data:
    v = job.get('details', {}).get('work_arrangement', '')
    vals[v] += 1
for v, c in vals.most_common():
    print(' ', repr(v), ':', c)

print('\n=== Position type values ===')
vals = Counter()
for job in data:
    v = job.get('details', {}).get('position_type', '')
    vals[v] += 1
for v, c in vals.most_common():
    print(' ', repr(v), ':', c)

print('\n=== Date posted samples ===')
for job in data[:10]:
    v = job.get('details', {}).get('date_posted', '')
    if v:
        print(' ', job['job_id'], ':', repr(v))
