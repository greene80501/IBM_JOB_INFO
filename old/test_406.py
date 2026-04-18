import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Try one of the 406 jobs
        url = 'https://careers.ibm.com/careers/JobDetail?jobId=55102&source=WEB_Search_NA'
        await page.goto(url, wait_until='load', timeout=60000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        print('Title:', await page.title())
        print('Length:', len(html))
        if '406' in html or 'Not Acceptable' in html:
            print('GOT 406')
        else:
            print('OK - first 500 chars:', html[:500])
        await browser.close()

asyncio.run(main())
