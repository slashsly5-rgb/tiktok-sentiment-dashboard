import time
import json
import os
import sys
import subprocess
import schedule
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("monitor.log")
    ]
)
logger = logging.getLogger("AutoMonitor")

CONFIG_FILE = "monitor_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Config file {CONFIG_FILE} not found!")
        return None
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def run_job():
    config = load_config()
    if not config: return

    keywords = config.get("keywords", [])
    max_videos = config.get("max_videos_per_keyword", 5)
    
    logger.info(f"🚀 Starting Automated Monitor Run for {len(keywords)} keywords...")
    
    for keyword in keywords:
        logger.info(f"🔎 Scanning keyword: {keyword}")
        try:
            # Call the scraper job
            cmd = [sys.executable, "run_scraper_job.py", "--keywords", keyword, "--max", str(max_videos)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                logger.info(f"✅ Finished {keyword}")
                # Log a summary line from the output if possible
                for line in result.stdout.split('\n'):
                    if "Saved" in line or "Found" in line:
                        logger.info(f"   [Scraper Output] {line.strip()}")
            else:
                logger.error(f"❌ Error scraping {keyword}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Exception running job for {keyword}: {e}")
            
    logger.info("💤 Monitor Run Complete. Waiting for next schedule...")

def main():
    logger.info("🤖 TIktok Sentiment Monitor Started")
    
    # Try to install schedule if not present (simple hack)
    try:
        import schedule
    except ImportError:
        logger.info("Installing 'schedule' library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
        import schedule

    config = load_config()
    if not config:
        logger.error("Invalid config. Exiting.")
        return

    # Schedule Logic
    interval = config.get("interval_hours", 24)
    start_time = config.get("start_time", "09:00")
    
    # Schedule daily at specific time
    schedule.every().day.at(start_time).do(run_job)
    
    # Also run immediately on start? Optional. Let's ask user or just run once.
    # For now, let's run once on startup to verify.
    run_job()
    
    logger.info(f"📅 Scheduled to run every day at {start_time}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
