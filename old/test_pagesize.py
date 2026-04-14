import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Try adding a page size parameter
        url = 'https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States&pageSize=100'
        await page.goto(url, wait_until='load', timeout=60000)
        await page.wait_for_timeout(8000)
        
        html = await page.content()
        soup = __import__('bs4').BeautifulSoup(html, 'html.parser')
        indicator = soup.find(class_='ibm--totalresults__totalresults')
        if indicator:
            print('Indicator:', indicator.get_text(strip=True))
        
        # Count job links
        job_links = soup.find_all('a', href=lambda x: x and 'JobDetail' in x)
        print(f'Job links: {len(job_links)}')
        
        await browser.close()

asyncio.run(main())
