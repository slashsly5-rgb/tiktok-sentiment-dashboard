"""
Standalone script to run TikTok scraping job
Called by the API or can be run manually for testing

Usage:
    python run_scraper_job.py --keywords "keyword1,keyword2" --max-videos 5
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from scraper import scrape_and_save, scrape_direct_urls
from database import SupabaseClient
from analyzer import batch_analyze_unanalyzed
from config import Config
import logging

# Configure logging to STDOUT for dashboard capture
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s', 
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

async def main(keywords: list, max_videos: int, openai_api_key: str = None, headless: bool = True, direct_urls: list = None):
    """
    Run scraping job for given keywords OR direct URLs
    """
    # ... (Browser check same as before) ...
    logger.info("Verifying Playwright browsers...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except: pass

    # Initialize database client
    try:
        db_client = SupabaseClient()
    except Exception as e:
        return {"status": "failed", "error": str(e)}

    results = []
    total_scraped = 0
    total_skipped = 0
    
    # CASE 1: Direct URLs
    if direct_urls:
         logger.info(f"Starting DIRECT SCRAPE for {len(direct_urls)} URLs...")
         try:
             result = await scrape_direct_urls(direct_urls, db_client, headless=headless)
             results.append(result)
         except Exception as e:
             logger.error(f"Direct scrape failed: {e}")
             
    # CASE 2: Keyword Search
    elif keywords:
        logger.info(f"Starting KEYWORD SCRAPE for: {keywords}")
        for keyword in keywords:
            try:
                result = await scrape_and_save(keyword, max_videos, db_client, headless=headless)
                results.append(result)
            except Exception as e:
                logger.error(f"Keyword scrape failed: {e}")

    # Calculate totals
    total_scraped = sum(r.get("scraped", 0) for r in results)
    total_skipped = sum(r.get("skipped", 0) for r in results)
    total_video_ids = []
    for r in results:
        total_video_ids.extend(r.get("video_ids", []))

    # Run Analysis
    logger.info("Starting analysis of new videos...")
    try:
        analysis_result = batch_analyze_unanalyzed(db_client, limit=total_scraped + 20, openai_api_key=openai_api_key) 
    except: pass

    return {
        "status": "completed",
        "total_scraped": total_scraped,
        "results": results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", type=str, help="Comma-separated keywords")
    parser.add_argument("--urls", type=str, help="Comma-separated URLs for direct scrape")
    parser.add_argument("--max-videos", type=int, default=5)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--openai_key", type=str, default=None)
    parser.add_argument('--visible', action='store_true')

    args = parser.parse_args()

    explicit_key = args.openai_key
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    direct_urls = [u.strip() for u in args.urls.split(",")] if args.urls else []
    
    if not keywords and not direct_urls:
        print(json.dumps({"status": "failed", "error": "No keywords or URLs provided"}))
        sys.exit(1)

    # Run
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    results = asyncio.run(main(keywords, args.max_videos, explicit_key, headless=not args.visible, direct_urls=direct_urls))

    print(json.dumps(results, indent=2))

    # Optionally save to file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

    # Exit with appropriate code (0 only if completed AND scraped > 0)
    is_success = results["status"] == "completed" and results.get("total_scraped", 0) > 0
    sys.exit(0 if is_success else 1)
