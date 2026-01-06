"""
API Testing Script
Tests all Flask API endpoints
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:5000"


def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_health():
    """Test health endpoint"""
    print_section("Testing GET /health")

    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200, "Health check failed"
        assert response.json()["status"] == "ok", "Status is not ok"

        print("✅ Health check passed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🧪 TikTok Scraper API Test Suite")

    # Check if API is running
    try:
        requests.get(f"{API_BASE}/health", timeout=2)
    except Exception:
        print("\n❌ ERROR: API is not running!")
        print(f"Please start the API first: python run_api.py")
        sys.exit(1)

    # Run health test
    test_health()


if __name__ == "__main__":
    main()
