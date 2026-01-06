"""
API startup script for TikTok Political Sentiment Scraper
Starts the Flask API server
"""

from api import app
from config import Config
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist (in project root)
    os.makedirs('../logs', exist_ok=True)

    logger.info("Starting TikTok Scraper API...")
    logger.info(f"Host: {Config.API_HOST}")
    logger.info(f"Port: {Config.API_PORT}")
    logger.info(f"Debug: {Config.API_DEBUG}")

    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.API_DEBUG
    )
