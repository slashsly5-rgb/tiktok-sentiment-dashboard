"""
Database Setup Script
Initializes Supabase database with required tables by executing setup.sql
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_sql_file(file_path: str) -> str:
    """Read SQL setup file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def execute_sql_migration(sql_content: str) -> bool:
    """Execute SQL migration using PostgreSQL connection"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.error("✗ DATABASE_URL not found in .env file")
        return False

    try:
        # Connect to PostgreSQL
        logger.info("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info("✓ Connected to database")

        # Execute SQL
        logger.info("Executing SQL migration...")
        cursor.execute(sql_content)

        logger.info("✓ SQL migration executed successfully")

        # Close connection
        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        logger.error(f"✗ PostgreSQL error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def verify_tables() -> bool:
    """Verify that tables were created successfully"""
    database_url = os.getenv("DATABASE_URL")

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        logger.info("\nVerifying tables...")

        # Check for each table
        tables = ["videos", "comments", "sentiment_analysis"]
        for table in tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """)
            exists = cursor.fetchone()[0]

            if exists:
                logger.info(f"✓ '{table}' table exists")
            else:
                logger.error(f"✗ '{table}' table not found")
                return False

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return False


def setup_database():
    """Initialize database tables"""
    logger.info("="*60)
    logger.info("  TikTok Scraper - Database Setup")
    logger.info("="*60)
    logger.info("")

    # Read SQL file
    sql_file = Path(__file__).parent.parent / "setup.sql"
    if not sql_file.exists():
        logger.error(f"✗ SQL file not found: {sql_file}")
        return False

    sql_content = read_sql_file(sql_file)
    logger.info(f"✓ SQL file loaded: {sql_file}")

    # Execute migration
    success = execute_sql_migration(sql_content)

    if not success:
        logger.error("\n❌ Database migration failed!")
        logger.info("\nYou can manually run the migration:")
        logger.info("1. Open Supabase dashboard: https://app.supabase.com")
        logger.info("2. Navigate to SQL Editor")
        logger.info(f"3. Copy and paste contents of: {sql_file}")
        logger.info("4. Execute the SQL")
        return False

    # Verify tables
    if verify_tables():
        logger.info("\n" + "="*60)
        logger.info("✅ Database setup completed successfully!")
        logger.info("="*60)
        logger.info("\nYou can now:")
        logger.info("1. Start the API: python run_api.py")
        logger.info("2. Start the dashboard: streamlit run app.py")
        logger.info("3. Run a test scrape: python run_scraper_job.py --keywords \"Sarawak\" --max-videos 2")
        return True
    else:
        logger.error("\n❌ Table verification failed!")
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
