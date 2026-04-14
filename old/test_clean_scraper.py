import asyncio
import json
from ibm_jobs_scraper import IBMJobScraper

async def main():
    scraper = IBMJobScraper(
        start_url="https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States",
        output_json="test_clean.json",
        output_csv="test_clean.csv",
        limit_pages=1,
        limit_jobs=5,
        delay_seconds=1.5,
        concurrency=3,
    )
    await scraper.run()

    with open("test_clean.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nScraped {len(data)} jobs")
    for job in data:
        print(f"\n--- Job {job['id']} ---")
        print(f"Title: {job['title']}")
        print(f"Official Title: {job.get('official_title')}")
        print(f"Category: {job['category']}")
        print(f"Career Level: {job.get('career_level')}")
        print(f"Department: {job.get('department')}")
        print(f"Location Summary: {job.get('location_summary')}")
        print(f"Cities: {job.get('cities')}")
        print(f"States: {job.get('states')}")
        print(f"Country: {job.get('country')}")
        print(f"Work Type: {job.get('work_type')}")
        print(f"Salary: {job.get('salary_min')} - {job.get('salary_max')}")
        print(f"Posted: {job.get('posted_at')}")
        print(f"Detail Error: {job.get('detail_error')}")
        # Show a few text keys
        for k in ['intro', 'responsibilities', 'about_business', 'life_at_ibm', 'visa_policy']:
            v = job.get(k)
            if v:
                preview = v.replace('\n', ' ')[:120]
                print(f"{k}: {preview}...")

if __name__ == "__main__":
    asyncio.run(main())
