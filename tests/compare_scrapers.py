
import asyncio
import logging
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from scraper import scrape_video_via_apify, TikTokScraper, scrape_video_via_http
from config import Config

# Configure logging
logging.basicConfig(level=logging.WARNING)

async def compare_scrapers(url):
    print(f"Target URL: {url}")
    print("-" * 50)
    
    # Run Normal Scraper
    print("Running Normal Scraper...")
    normal_data = None
    try:
        # Try HTTP first (simulate normal flow)
        normal_data = await scrape_video_via_http(url)
        if not normal_data or (normal_data.get('stats', {}).get('likes', 0) == 0 and not normal_data.get('description')):
             print("HTTP failed/incomplete. Trying Browser...")
             scraper = TikTokScraper(headless=True)
             await scraper.start()
             normal_data = await scraper.scrape_video_details(url)
             await scraper.stop()
    except Exception as e:
        print(f"Normal Scraper Failed: {e}")
        
    print(f"Normal Data: {json.dumps(normal_data, indent=2, default=str)}")
    print("-" * 50)

    # Run Apify Scraper
    print("Running Apify Scraper...")
    apify_data = await scrape_video_via_apify(url)
    print(f"Apify Data: {json.dumps(apify_data, indent=2, default=str)}")
    print("-" * 50)
    
    # Comparison Logic (if both exist)
    if normal_data and apify_data:
        print("Comparison:")
        keys = set(normal_data.keys()) | set(apify_data.keys())
        match = True
        for k in keys:
            v1 = normal_data.get(k)
            v2 = apify_data.get(k)
            # Rough check
            if k == 'stats':
                 # Deep compare
                 s1 = v1 or {}
                 s2 = v2 or {}
                 for sk in ['views', 'likes', 'shares', 'comments']:
                     if s1.get(sk, 0) != s2.get(sk, 0):
                         print(f"Stats mismatch for {sk}: Normal={s1.get(sk)}, Apify={s2.get(sk)}")
                         match = False
            elif v1 != v2:
                # Allow minor differences
                if isinstance(v1, list) and isinstance(v2, list):
                    if len(v1) != len(v2):
                        print(f"Mismatch {k}: len(Normal)={len(v1)}, len(Apify)={len(v2)}")
                else:
                    print(f"Mismatch {k}: Normal={v1}, Apify={v2}")
        
        if match:
            print("Payloads match closely!")
    else:
        print("Cannot compare - one or both scrapers failed.")


if __name__ == "__main__":
    url = "https://www.tiktok.com/@susancrawford6741/video/7484302854369515038"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    asyncio.run(compare_scrapers(url))
