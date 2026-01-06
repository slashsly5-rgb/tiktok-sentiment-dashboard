import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Explicitly load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from database import SupabaseClient

def debug_key_issues():
    print("--- DEBUGGING KEY ISSUES DATA ---")
    try:
        db = SupabaseClient()
        # Fetch last 10 sentiment analyses
        response = db.supabase.table("sentiment_analysis").select("video_id, key_issues").order("analyzed_at", desc=True).limit(10).execute()
        
        data = response.data
        print(f"Fetched {len(data)} records.")
        
        for i, record in enumerate(data):
            issues = record.get('key_issues')
            print(f"\nRecord {i+1}:")
            print(f"  Type: {type(issues)}")
            print(f"  Raw Content: {issues}")
            
            if isinstance(issues, list):
                print(f"  Length: {len(issues)}")
                if len(issues) > 0:
                    print(f"  First item type: {type(issues[0])}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_key_issues()
