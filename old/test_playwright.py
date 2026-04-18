import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = 'https://www.ibm.com/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_18[1]=Internship&field_keyword_05[0]=United%20States'
        
        # Use load instead of networkidle to avoid timeout from analytics
        await page.goto(url, wait_until='load', timeout=60000)
        # Wait for the search app to render
        await page.wait_for_timeout(8000)
        
        # Try to find job listing elements - let's just dump the HTML and inspect
        html = await page.content()
        with open('rendered_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved rendered_page.html')
        
        # Count elements with job-related text
        cards = await page.query_selector_all('a[href*="/careers/job/"]')
        print(f'Found {len(cards)} job links')
        
        if len(cards) > 0:
            # Get first few links
            for i, card in enumerate(cards[:5]):
                href = await card.get_attribute('href')
                text = await card.inner_text()
                print(f'{i+1}. {href} - {text[:100]}')
        
        await browser.close()

asyncio.run(main())
