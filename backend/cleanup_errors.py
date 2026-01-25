
import os
import sys
from dotenv import load_dotenv

# Add backend to path to import database/config
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from database import SupabaseClient

def cleanup_errors():
    print("Connecting to Supabase...")
    db = SupabaseClient()
    
    print("Searching for failed analyses (Sentiment = 'Error' or Topic = 'Analysis Error')...")
    
    # 1. Get all videos to check (inefficient but safe for small dataset)
    # Supabase-py doesn't always support complex delete filters easily in one go, 
    # but let's try to find them first.
    
    # Actually, we can just use the table reference directly if exposed, 
    # but SupabaseClient wraps it. 
    # Let's add a cleanup method to SupabaseClient or just access the client directly.
    
    try:
        count = 0 
        # Fetch ERRORS from SENTIMENT_ANALYSIS table (Correct table)
        print("Scanning 'sentiment_analysis' table for Error items...")
        
        # 1. Check for literal 'Error' sentiment
        response = db.supabase.table("sentiment_analysis").select("*").eq("sentiment", "Error").execute()
        errors = response.data
        print(f"Found {len(errors)} records with sentiment='Error'.")
        
        if errors:
            ids = [v['id'] for v in errors]
            for sid in ids:
                 db.supabase.table("sentiment_analysis").delete().eq("id", sid).execute()
                 count += 1
            print("Deleted sentiment='Error' batch.")

        # 2. Check for 'Analysis Error' topic
        response2 = db.supabase.table("sentiment_analysis").select("*").eq("topic", "Analysis Error").execute()
        errors2 = response2.data
        # Filter out duplicates if any overlap
        errors2 = [e for e in errors2 if e['id'] not in [x['id'] for x in errors]]
        
        print(f"Found {len(errors2)} records with topic='Analysis Error'.")
        if errors2:
            ids2 = [v['id'] for v in errors2]
            for sid in ids2:
                db.supabase.table("sentiment_analysis").delete().eq("id", sid).execute()
                count += 1
            print("Deleted topic='Analysis Error' batch.")

        print(f"Cleanup complete. Total records deleted: {count}")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup_errors()
