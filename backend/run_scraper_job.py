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

async def main(keywords: list, max_videos: int, api_key: str = None, headless: bool = True, direct_urls: list = None, provider: str = None):
    """
    Run scraping job for given keywords OR direct URLs

    Args:
        keywords: List of search keywords
        max_videos: Maximum videos per keyword
        api_key: Optional LLM API key (Mistral or OpenAI)
        headless: Run browser in headless mode
        direct_urls: Optional list of direct URLs to scrape
        provider: "mistral" or "openai" (defaults to Config.LLM_PROVIDER)
    """
    # Set provider from config if not specified
    if not provider:
        provider = Config.LLM_PROVIDER

    print("\n" + "="*60)
    print("  TIKTOK SENTIMENT SCRAPER - STARTING JOB")
    print("="*60)
    print(f"  LLM Provider: {provider.upper()}")
    print(f"  Headless Mode: {headless}")
    if direct_urls:
        print(f"  Mode: DIRECT URL SCRAPE ({len(direct_urls)} URLs)")
    elif keywords:
        print(f"  Mode: KEYWORD SEARCH ({len(keywords)} keywords, max {max_videos} videos each)")
    print("="*60 + "\n")

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
    print("\n" + "-"*60)
    print(f"  PHASE 2: LLM ANALYSIS ({provider.upper()})")
    print("-"*60)
    print(f"  Videos to analyze: {total_scraped + 20}")

    analysis_result = None
    try:
        analysis_result = batch_analyze_unanalyzed(db_client, limit=total_scraped + 20, api_key=api_key, provider=provider)

        if analysis_result:
            print(f"\n  [OK] Analysis Complete!")
            print(f"       - Total analyzed: {analysis_result.get('analyzed', 0)}")
            print(f"       - Failed: {analysis_result.get('failed', 0)}")

            # Show summary for each analyzed video
            for r in analysis_result.get('results', [])[:5]:  # Show first 5
                if r.get('status') == 'success':
                    analysis = r.get('analysis', {})
                    print(f"\n  [VIDEO] {r.get('video_id', 'Unknown')[:8]}...")
                    print(f"       Topic: {analysis.get('topic', 'N/A')}")
                    print(f"       Sentiment: {analysis.get('sentiment', 'N/A')} (Score: {analysis.get('score', 'N/A')})")
                    summary = analysis.get('summary', 'N/A')
                    if len(summary) > 100:
                        summary = summary[:100] + "..."
                    print(f"       Summary: {summary}")
    except Exception as e:
        print(f"  [FAIL] Analysis failed: {e}")
        logger.error(f"Analysis failed: {e}")

    print("\n" + "="*60)
    print("  JOB COMPLETE!")
    print(f"  Total Scraped: {total_scraped}")
    print(f"  Total Analyzed: {analysis_result.get('analyzed', 0) if analysis_result else 0}")
    print("="*60 + "\n")

    return {
        "status": "completed",
        "total_scraped": total_scraped,
        "total_analyzed": analysis_result.get('analyzed', 0) if analysis_result else 0,
        "results": results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", type=str, help="Comma-separated keywords")
    parser.add_argument("--urls", type=str, help="Comma-separated URLs for direct scrape")
    parser.add_argument("--max-videos", "--max", type=int, default=5)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--api_key", type=str, default=None, help="LLM API key (Mistral or OpenAI)")
    parser.add_argument("--provider", type=str, default=None, help="LLM provider: 'mistral' or 'openai'")
    parser.add_argument('--visible', action='store_true')

    args = parser.parse_args()

    explicit_key = args.api_key
    provider = args.provider
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    direct_urls = [u.strip() for u in args.urls.split(",")] if args.urls else []

    if not keywords and not direct_urls:
        print(json.dumps({"status": "failed", "error": "No keywords or URLs provided"}))
        sys.exit(1)

    # Run
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    results = asyncio.run(main(keywords, args.max_videos, explicit_key, headless=not args.visible, direct_urls=direct_urls, provider=provider))

    print(json.dumps(results, indent=2))

    # Optionally save to file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

    # Exit with appropriate code (0 only if completed AND scraped > 0)
    is_success = results["status"] == "completed" and results.get("total_scraped", 0) > 0
    sys.exit(0 if is_success else 1)
