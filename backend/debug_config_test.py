import os
print("Running debug config test...")

# Mock Streamlit secrets just in case import fails without it being installed but it should be fine
try:
    from config import Config
    print("Config imported successfully.")
    print(f"SUPABASE_URL: {Config.SUPABASE_URL}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {Config.SUPABASE_SERVICE_ROLE_KEY}")
    print(f"Config.validate(): {Config.validate()}")
except Exception as e:
    print(f"Error importing or using Config: {e}")
