"""
Configuration module for TikTok Political Sentiment Scraper
Centralizes all environment variables and application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Application configuration"""

    # ============================================
    # Supabase Configuration
    # ============================================
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # ============================================
    # OpenAI Configuration
    # ============================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # ============================================
    # Mistral AI Configuration
    # ============================================
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium-latest")
    MISTRAL_MAX_TOKENS = int(os.getenv("MISTRAL_MAX_TOKENS", "1000"))
    MISTRAL_TEMPERATURE = float(os.getenv("MISTRAL_TEMPERATURE", "0.7"))

    # Chat session configuration
    CHAT_SESSION_TIMEOUT = int(os.getenv("CHAT_SESSION_TIMEOUT", "3600"))  # 1 hour in seconds
    MAX_CHAT_HISTORY_LENGTH = int(os.getenv("MAX_CHAT_HISTORY_LENGTH", "50"))  # max messages per session

    # ============================================
    # Apify Configuration (Optional)
    # ============================================
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

    # ============================================
    # API Configuration
    # ============================================
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "5000"))
    API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"

    # ============================================
    # Scraper Configuration
    # ============================================
    SCRAPER_HEADLESS = os.getenv("SCRAPER_HEADLESS", "True").lower() == "true"
    SCRAPER_MAX_VIDEOS = int(os.getenv("SCRAPER_MAX_VIDEOS", "5"))
    SCRAPER_MAX_COMMENTS = int(os.getenv("SCRAPER_MAX_COMMENTS", "20"))

    # ============================================
    # Default Keywords for Sarawak Politics
    # ============================================
    DEFAULT_KEYWORDS = [
        # Politicians
        "Abang Johari",
        "Fadillah Yusof",
        "Abdul Karim Rahman Hamzah",
        "Tiong King Sing",
        "Yii Siew Ling",

        # Political Parties
        "GPS Sarawak",
        "Parti Pesaka Bumiputera Bersatu",
        "Sarawak United Peoples Party",

        # Topics
        "Sarawak politics",
        "Sarawak development",
        "Pan Borneo Highway",
        "MA63 rights",
        "Sarawak autonomous",
        "PCDS Sarawak",
        "Sarawak budget 2025",
        "Sarawak economy",
        "Sarawak infrastructure",

        # Current Events
        "Sarawak election",
        "Sarawak premier",
        "Sarawak rights",
    ]

    # ============================================
    # Database Configuration
    # ============================================
    DB_RETRY_ATTEMPTS = 3
    DB_RETRY_DELAY = 2  # seconds

    # ============================================
    # Analysis Configuration
    # ============================================
    ANALYSIS_BATCH_SIZE = 10  # Number of videos to analyze in one batch
    ANALYSIS_MODEL = "gpt-3.5-turbo"  # OpenAI model for analysis
    ANALYSIS_MAX_TOKENS = 500

    # ============================================
    # API Pagination Configuration
    # ============================================
    MAX_LIMIT = 1000  # Maximum records that can be requested per page

    # ============================================
    # Validation
    # ============================================
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL is not set")
        if not cls.SUPABASE_ANON_KEY:
            errors.append("SUPABASE_ANON_KEY is not set")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            errors.append("SUPABASE_SERVICE_ROLE_KEY is not set")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

    @classmethod
    def get_summary(cls):
        """Get configuration summary for logging"""
        return {
            "supabase_configured": bool(cls.SUPABASE_URL),
            "openai_configured": bool(cls.OPENAI_API_KEY),
            "mistral_configured": bool(cls.MISTRAL_API_KEY),
            "apify_configured": bool(cls.APIFY_API_TOKEN),
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "scraper_headless": cls.SCRAPER_HEADLESS,
            "default_keywords_count": len(cls.DEFAULT_KEYWORDS),
        }
