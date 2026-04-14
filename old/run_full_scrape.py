import asyncio
from ibm_jobs_scraper import IBMJobScraper

async def main():
    scraper = IBMJobScraper(
        start_url="https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States",
        output_json="ibm_jobs.json",
        output_csv="ibm_jobs.csv",
        delay_seconds=0.8,
        concurrency=6,
    )
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
