import csv
import json

with open("ibm_jobs.json", "r", encoding="utf-8") as f:
    all_jobs = json.load(f)

rows = []
all_keys = set()
for job in all_jobs:
    row = dict(job)
    details = row.pop("details", {})
    for k, v in details.items():
        row[f"detail_{k}"] = v
    rows.append(row)
    all_keys.update(row.keys())

core = ["job_id", "title", "category", "level", "location", "detail_url"]
fieldnames = [c for c in core if c in all_keys]
remaining = sorted(all_keys - set(fieldnames))
fieldnames.extend(remaining)

with open("ibm_jobs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Fixed CSV with {len(rows)} rows and {len(fieldnames)} columns")
