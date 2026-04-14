import json

with open('ibm_jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for j in data[:10]:
    print(j['id'], 'cities:', repr(j.get('cities')), 'states:', repr(j.get('states')))
