import asyncio
import json
from ibm_jobs_scraper import IBMJobScraper

async def main():
    scraper = IBMJobScraper(
        start_url="https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States",
        output_json="test_jobs.json",
        output_csv="test_jobs.csv",
        limit_pages=1,
        limit_jobs=3,
        delay_seconds=2.0,
    )
    await scraper.run()
    
    # Print results
    with open("test_jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\nScraped {len(data)} jobs")
    for job in data:
        print(f"\nJob ID: {job['job_id']}")
        print(f"Title: {job['title']}")
        print(f"Category: {job['category']}")
        print(f"Level: {job['level']}")
        print(f"Location: {job['location']}")
        details = job.get('details', {})
        print(f"Detail keys: {list(details.keys())[:10]}")

if __name__ == "__main__":
    asyncio.run(main())
