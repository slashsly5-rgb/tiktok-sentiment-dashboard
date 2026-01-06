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

from scraper import scrape_and_save
from database import SupabaseClient
from analyzer import batch_analyze_unanalyzed
from config import Config
import logging

# Configure logging
# Configure logging to STDOUT for dashboard capture
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s', 
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)


async def main(keywords: list, max_videos: int):
    """
    Run scraping job for given keywords

    Args:
        keywords: List of search keywords
        max_videos: Maximum videos per keyword

    Returns:
        Results dictionary
    """
    # Pre-flight: Ensure browsers are installed (Critical for Cloud)
    logger.info("Verifying Playwright browsers...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        logger.info("Browser installation check complete.")
    except Exception as e:
        logger.error(f"Failed to install browsers: {e}")

    logger.info(f"Starting scraping job for keywords: {keywords}")
    logger.info(f"Max videos per keyword: {max_videos}")

    if not os.getenv("OPENAI_API_KEY"):
         logger.error("CRITICAL: OPENAI_API_KEY not found in environment!")
    else:
         logger.info("OPENAI_API_KEY found.")

    # Debug Environment Injection
    logger.info(f"DEBUG: os.environ SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'NOT_SET')}")
    key_check = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    logger.info(f"DEBUG: os.environ SUPABASE_KEY: {'[PRESENT]' if key_check else '[MISSING]'}")

    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        logger.info(f"DEBUG: os.environ OPENAI_KEY Length: {len(openai_key)}")
        logger.info(f"DEBUG: os.environ OPENAI_KEY Suffix: ...{openai_key[-5:]}")
    else:
        logger.info("DEBUG: os.environ OPENAI_KEY: [MISSING]")
    
    from config import Config
    logger.info(f"DEBUG: Config.SUPABASE_URL: {Config.SUPABASE_URL}")
    logger.info(f"DEBUG: Config.SUPABASE_KEY: {'[PRESENT]' if Config.SUPABASE_SERVICE_ROLE_KEY else '[MISSING]'}")

    # Initialize database client
    try:
        db_client = SupabaseClient()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "results": []
        }

    results = []

    # Process each keyword
    for keyword in keywords:
        try:
            logger.info(f"Processing keyword: {keyword}")
            result = await scrape_and_save(keyword, max_videos, db_client, headless=True)
            results.append(result)
            logger.info(f"Completed {keyword}: {result['scraped']} scraped, {result['skipped']} skipped")
        except Exception as e:
            logger.error(f"Error processing keyword '{keyword}': {e}")
            results.append({
                "keyword": keyword,
                "error": str(e),
                "scraped": 0,
                "skipped": 0,
                "video_ids": []
            })

    # Calculate totals
    total_scraped = sum(r.get("scraped", 0) for r in results)
    total_skipped = sum(r.get("skipped", 0) for r in results)
    total_video_ids = []
    for r in results:
        total_video_ids.extend(r.get("video_ids", []))

    # Run Analysis on new videos
    logger.info("Starting analysis of new videos...")
    try:
        # Pass the explicit_key to batch_analyze_unanalyzed
        analysis_result = batch_analyze_unanalyzed(db_client, limit=total_scraped + 20, openai_api_key=openai_api_key) # Analyze newly scraped + backlog
        logger.info(f"Analysis complete: {analysis_result['analyzed']} analyzed")
        
        # Add analysis stats to summary
        for r in results:
            r['analyzed_count'] = analysis_result['analyzed']
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

    summary = {
        "status": "completed",
        "total_keywords": len(keywords),
        "total_scraped": total_scraped,
        "total_skipped": total_skipped,
        "total_videos": len(total_video_ids),
        "video_ids": total_video_ids,
        "results": results
    }

    logger.info(f"Job completed: {total_scraped} videos scraped, {total_skipped} skipped")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TikTok scraping job")
    parser.add_argument(
        "--keywords",
        type=str,
        required=True,
        help="Comma-separated list of keywords to search"
    )
        # Pass the explicit_key to batch_analyze_unanalyzed
        analysis_result = batch_analyze_unanalyzed(db_client, limit=total_scraped + 20, openai_api_key=explicit_key) # Analyze newly scraped + backlog
        logger.info(f"Analysis complete: {analysis_result['analyzed']} analyzed")
        
        # Add analysis stats to summary
        for r in results:
            r['analyzed_count'] = analysis_result['analyzed']
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

    summary = {
        "status": "completed",
        "total_keywords": len(keywords),
        "total_scraped": total_scraped,
        "total_skipped": total_skipped,
        "total_videos": len(total_video_ids),
        "video_ids": total_video_ids,
        "results": results
    }

    logger.info(f"Job completed: {total_scraped} videos scraped, {total_skipped} skipped")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TikTok scraping job")
    parser.add_argument(
        "--keywords",
        type=str,
        required=True,
        help="Comma-separated list of keywords to search"
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=Config.SCRAPER_MAX_VIDEOS,
        help=f"Maximum videos per keyword (default: {Config.SCRAPER_MAX_VIDEOS})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (optional)"
    )
    parser.add_argument("--openai_key", type=str, default=None, help="Explicit OpenAI API Key")

    args = parser.parse_args()

    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(",")]
    explicit_key = args.openai_key

    # Log which key is being used for OpenAI
    if explicit_key:
        logger.info(f"DEBUG: Using Explicit CLI OpenAI Key ending in ...{explicit_key[-5:]}")
    else:
        logger.info("DEBUG: Using Environment OpenAI API Key")

    # Run async main
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Pass implicit key to main
    results = asyncio.run(main(keywords, args.max_videos, explicit_key))

    # Print results as JSON
    print(json.dumps(results, indent=2))

    # Optionally save to file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

    # Exit with appropriate code (0 only if completed AND scraped > 0)
    is_success = results["status"] == "completed" and results.get("total_scraped", 0) > 0
    sys.exit(0 if is_success else 1)
