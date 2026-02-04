
import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Mock user agent to avoid immediate block
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
        
        url = "https://www.tiktok.com/@catslapa_/video/7595476244653788447"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(5) # Wait for hydration
        except Exception as e:
            print(f"Navigation error: {e}")
            
        print("\n--- META TAGS ---")
        meta_desc = await page.query_selector('meta[name="description"]')
        if meta_desc:
            content = await meta_desc.get_attribute('content')
            print(f"Meta Description: {content}")
        else:
            print("No meta description found.")
            
        print("\n--- DOM STATS ---")
        # Try generic stats containers
        stats = await page.evaluate("""() => {
            const data = {};
            // Try all data-e2e attributes related to stats
            const els = document.querySelectorAll('[data-e2e]');
            els.forEach(el => {
                const attr = el.getAttribute('data-e2e');
                if (attr.includes('count') || attr.includes('view') || attr.includes('like') || attr.includes('share') || attr.includes('comment')) {
                     data[attr] = el.innerText;
                }
            });
            return data;
        }""")
        print(f"Found Stats Elements: {stats}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
