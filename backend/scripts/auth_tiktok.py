import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    print("----------------------------------------------------------------")
    print("  TikTok Login Helper")
    print("----------------------------------------------------------------")
    print("  1. A browser window will open.")
    print("  2. Please Log In to TikTok in that window.")
    print("     (Use QR Code, Phone, or Email - whatever works for you)")
    print("  3. After you are successfully logged in and can see the feed,")
    print("     come back here and press ENTER.")
    print("----------------------------------------------------------------")
    
    async with async_playwright() as p:
        # Launch browser in HEADED mode (visible)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        # Go to login page
        print("Opening TikTok Login page...")
        await page.goto("https://www.tiktok.com/login")
        
        # Wait for user confirmation
        input("\n>>> PRESS ENTER AFTER YOU HAVE LOGGED IN SUCCESSFULLY <<<")
        
        # Save storage state (cookies + local storage)
        # Save to root directory
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        auth_file = os.path.join(root_dir, "auth.json")
        
        await context.storage_state(path=auth_file)
        
        print(f"\nSUCCESS! Authentication saved to: {auth_file}")
        print("You can now close the browser and run the scraper.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
