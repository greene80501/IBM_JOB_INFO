import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = 'https://careers.ibm.com/careers/JobDetail?jobId=65792&source=WEB_Search_NA'
        await page.goto(url, wait_until='load', timeout=60000)
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        with open('job_detail.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved job_detail.html')
        
        # Get page title
        title = await page.title()
        print('Page title:', title)
        
        await browser.close()

asyncio.run(main())
