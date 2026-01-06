"""
Database Migration Script
Updates schema from screenshot_base64 to post_url and adds new columns
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')


def run_migration():
    """Migrate database schema to latest version"""

    print("Database Schema Migration")
    print("=" * 50)

    # Get DATABASE_URL from env
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment")
        return False

    # Connect to PostgreSQL
    print("Connecting to database...")

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        print("[OK] Connected to database")
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        return False

    try:
        print("\nRunning migrations...\n")

        # Migration 1: Rename screenshot_base64 to post_url if it exists
        print("1. Checking for screenshot_base64 column...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'videos'
            AND column_name = 'screenshot_base64'
        """)

        if cursor.fetchone():
            print("   -> Renaming screenshot_base64 to post_url")
            cursor.execute("""
                ALTER TABLE videos
                RENAME COLUMN screenshot_base64 TO post_url
            """)
            print("   [OK] Renamed screenshot_base64 to post_url")
        else:
            print("   [INFO] screenshot_base64 column not found (already migrated or doesn't exist)")

        # Migration 2: Add transcribed_url column if it doesn't exist
        print("\n2. Checking for transcribed_url column...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'videos'
            AND column_name = 'transcribed_url'
        """)

        if not cursor.fetchone():
            print("   -> Adding transcribed_url column")
            cursor.execute("""
                ALTER TABLE videos
                ADD COLUMN transcribed_url TEXT
            """)
            print("   [OK] Added transcribed_url column")
        else:
            print("   [INFO] transcribed_url already exists")

        # Migration 3: Add summary column if it doesn't exist
        print("\n3. Checking for summary column...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'videos'
            AND column_name = 'summary'
        """)

        if not cursor.fetchone():
            print("   -> Adding summary column")
            cursor.execute("""
                ALTER TABLE videos
                ADD COLUMN summary TEXT
            """)
            print("   [OK] Added summary column")
        else:
            print("   [INFO] summary already exists")

        # Migration 4: Add shares_count if it doesn't exist
        print("\n4. Checking for shares_count column...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'videos'
            AND column_name = 'shares_count'
        """)

        if not cursor.fetchone():
            print("   -> Adding shares_count column")
            cursor.execute("""
                ALTER TABLE videos
                ADD COLUMN shares_count BIGINT DEFAULT 0
            """)
            print("   [OK] Added shares_count column")
        else:
            print("   [INFO] shares_count already exists")

        # Migration 5: Add search_keyword if it doesn't exist
        print("\n5. Checking for search_keyword column...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'videos'
            AND column_name = 'search_keyword'
        """)

        if not cursor.fetchone():
            print("   -> Adding search_keyword column")
            cursor.execute("""
                ALTER TABLE videos
                ADD COLUMN search_keyword VARCHAR(255)
            """)
            print("   [OK] Added search_keyword column")
        else:
            print("   [INFO] search_keyword already exists")

        # Migration 6: Update column comments
        print("\n6. Updating column comments...")
        cursor.execute("""
            COMMENT ON COLUMN videos.post_url IS 'Supabase Storage URL for video post/screenshot image'
        """)
        cursor.execute("""
            COMMENT ON COLUMN videos.transcribed_url IS 'Supabase Storage URL for transcription file (JSON/TXT)'
        """)
        cursor.execute("""
            COMMENT ON COLUMN videos.summary IS 'AI-generated summary of video content'
        """)
        cursor.execute("""
            COMMENT ON COLUMN videos.search_keyword IS 'Keyword used to discover this video'
        """)
        print("   [OK] Updated column comments")

        # Commit all changes
        conn.commit()
        print("\n[SUCCESS] All migrations completed successfully!")

        # Verify final schema
        print("\nVerifying final schema...")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'videos'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        print("\n   Videos table columns:")
        for col_name, col_type in columns:
            print(f"   - {col_name}: {col_type}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


if __name__ == "__main__":
    print("\n")
    success = run_migration()
    print("\n" + "=" * 50)

    if success:
        print("[SUCCESS] Schema migration completed!")
        print("\nYour database now has:")
        print("  - post_url (instead of screenshot_base64)")
        print("  - transcribed_url")
        print("  - summary")
        print("  - shares_count")
        print("  - search_keyword")
        sys.exit(0)
    else:
        print("[ERROR] Migration failed - check errors above")
        sys.exit(1)
