import os
from pathlib import Path
from dotenv import load_dotenv

print("=== Debugging Environment Configuration ===")

# 1. Calculate path exactly like config.py
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
env_path = project_root / '.env'

print(f"Current file: {current_file}")
print(f"Project root: {project_root}")
print(f"Expected .env path: {env_path}")

# 2. Check if file exists
if env_path.exists():
    print(f"✅ .env file FOUND at {env_path}")
    print(f"   File size: {env_path.stat().st_size} bytes")
    try:
        content = env_path.read_text(encoding='utf-8')
        print("   File content preview (first 50 chars):")
        print(f"   '{content[:50]}...'")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
else:
    print(f"❌ .env file NOT FOUND at {env_path}")
    print("   Listing project root contents:")
    for item in project_root.iterdir():
        print(f"   - {item.name}")

# 3. Try loading it
print("\n--- Loading .env ---")
load_dotenv(dotenv_path=env_path, override=True)

# 4. Check variables
url = os.getenv("SUPABASE_URL")
anon = os.getenv("SUPABASE_ANON_KEY")

print(f"SUPABASE_URL: {'✅ Set' if url else '❌ Not Set'} ({url})")
print(f"SUPABASE_ANON_KEY: {'✅ Set' if anon else '❌ Not Set'}")

# 5. Check if we need to encode password in DATABASE_URL
db_url = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {'✅ Set' if db_url else '❌ Not Set'}")
if db_url and '[YOUR-PASSWORD]' in db_url:
    print("❌ WARNING: DATABASE_URL still contains placeholder [YOUR-PASSWORD]")

print("===========================================")
input("Press Enter to exit...")
