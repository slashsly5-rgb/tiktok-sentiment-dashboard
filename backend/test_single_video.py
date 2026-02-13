"""
Test script for the single-video scrape+analyze API endpoint.
Run with: python test_single_video.py [tiktok_url]

Tests:
1. API endpoint is reachable
2. Invalid URL returns error
3. Valid TikTok URL returns expected response structure
4. Response fields match what Streamlit/React frontends expect
"""

import sys
import os
import json
import time
import requests

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Determine API URL
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "5000")))
API_HOST = os.getenv("API_HOST", "127.0.0.1")
BASE_URL = os.getenv("BACKEND_URL", f"http://{API_HOST}:{API_PORT}")
ENDPOINT = f"{BASE_URL}/api/scrape/single-video"

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"


def test_health():
    """Test 1: Check if API is reachable"""
    print(f"\n{'='*60}")
    print("TEST 1: API Health Check")
    print(f"{'='*60}")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print(f"  {PASS} API is reachable at {BASE_URL}")
            return True
        else:
            print(f"  {FAIL} API returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} Cannot connect to {BASE_URL}")
        print(f"  -> Start the Flask API first: python api.py")
        return False
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
        return False


def test_missing_url():
    """Test 2: POST without URL should return 400"""
    print(f"\n{'='*60}")
    print("TEST 2: Missing URL Validation")
    print(f"{'='*60}")
    try:
        resp = requests.post(ENDPOINT, json={}, timeout=10)
        if resp.status_code == 400:
            data = resp.json()
            if data.get("status") == "failed" and "URL" in data.get("error", ""):
                print(f"  {PASS} Returns 400 with proper error message")
                return True
            else:
                print(f"  {FAIL} Returns 400 but wrong error format: {data}")
                return False
        else:
            print(f"  {FAIL} Expected 400, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
        return False


def test_invalid_url():
    """Test 3: Non-TikTok URL should return 400"""
    print(f"\n{'='*60}")
    print("TEST 3: Invalid URL Validation")
    print(f"{'='*60}")
    try:
        resp = requests.post(ENDPOINT, json={"url": "https://google.com"}, timeout=10)
        if resp.status_code == 400:
            data = resp.json()
            if data.get("status") == "failed":
                print(f"  {PASS} Non-TikTok URL rejected with proper error")
                return True
        print(f"  {FAIL} Expected 400 rejection, got {resp.status_code}")
        return False
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
        return False


def test_valid_url(url):
    """Test 4: Valid TikTok URL should return scraped data"""
    print(f"\n{'='*60}")
    print("TEST 4: Valid TikTok URL - Full Pipeline")
    print(f"{'='*60}")
    print(f"  URL: {url}")
    print(f"  Endpoint: {ENDPOINT}")
    print(f"  (This may take 30-120 seconds...)")

    try:
        start = time.time()
        resp = requests.post(ENDPOINT, json={"url": url}, timeout=180)
        elapsed = time.time() - start
        print(f"  Response time: {elapsed:.1f}s")
        print(f"  Status code: {resp.status_code}")

        data = resp.json()
        print(f"  Response status: {data.get('status')}")
        print(f"  Steps completed: {len(data.get('steps', []))}")

        # Print step details
        for step in data.get("steps", []):
            s_num = step.get("step", "?")
            s_name = step.get("name", "?")
            s_status = step.get("status", "?")
            s_detail = step.get("detail", "")
            s_dur = step.get("duration", 0)
            icon = {"success": "OK", "failed": "XX", "skipped": ">>", "exists": "==", "updated": "UP"}.get(s_status, "??")
            print(f"    [{icon}] Step {s_num}: {s_name} - {s_detail} ({s_dur}s)")

        if data.get("status") in ("completed", "partial"):
            print(f"\n  {PASS} Pipeline completed with status: {data['status']}")
        else:
            print(f"\n  {FAIL} Pipeline failed: {data.get('error')}")
            return False

        # Validate response structure for frontends
        return validate_response_structure(data)

    except requests.exceptions.Timeout:
        print(f"  {FAIL} Request timed out after 180s")
        return False
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
        return False


def validate_response_structure(data):
    """Test 5: Validate response matches frontend expectations"""
    print(f"\n{'='*60}")
    print("TEST 5: Response Structure Validation")
    print(f"{'='*60}")

    errors = []

    # Top-level fields
    for field in ["status", "video_id", "tiktok_id", "steps", "video", "total_duration"]:
        if field not in data:
            errors.append(f"Missing top-level field: {field}")

    video = data.get("video", {})
    if not video:
        errors.append("video object is empty or missing")
        for e in errors:
            print(f"  {FAIL} {e}")
        return False

    # Video fields (camelCase - expected by both Streamlit and React)
    video_fields = ["authorUsername", "description", "viewsCount", "likesCount", "commentsCount", "sharesCount"]
    for field in video_fields:
        if field not in video:
            errors.append(f"Missing video field: {field}")
        else:
            print(f"  {PASS} video.{field} = {repr(video[field])[:60]}")

    # Sentiment object
    sentiment = video.get("sentiment")
    if sentiment is None:
        errors.append("video.sentiment is missing (analysis may have failed)")
    else:
        sentiment_fields = ["sentiment", "sentimentScore", "summary"]
        for field in sentiment_fields:
            if field in sentiment:
                print(f"  {PASS} video.sentiment.{field} = {repr(sentiment[field])[:60]}")
            else:
                errors.append(f"Missing sentiment field: {field}")

        # Optional sentiment fields
        for field in ["keyIssues", "discussionPoints", "topic"]:
            if field in sentiment:
                print(f"  {PASS} video.sentiment.{field} = {repr(sentiment[field])[:60]}")

    # Steps array
    steps = data.get("steps", [])
    if len(steps) < 6:
        errors.append(f"Expected at least 6 steps, got {len(steps)}")

    if errors:
        print(f"\n  Errors found ({len(errors)}):")
        for e in errors:
            print(f"  {FAIL} {e}")
        return False
    else:
        print(f"\n  {PASS} All response fields validated successfully!")
        return True


def main():
    print("=" * 60)
    print("SINGLE VIDEO API ENDPOINT TEST SUITE")
    print("=" * 60)
    print(f"Target: {ENDPOINT}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check API is running
    if not test_health():
        print(f"\n{'='*60}")
        print("ABORTED: Flask API not running")
        print(f"Start it with: cd backend && python api.py")
        print(f"{'='*60}")
        sys.exit(1)

    # Run validation tests
    results = {
        "Missing URL": test_missing_url(),
        "Invalid URL": test_invalid_url(),
    }

    # Full pipeline test with a real URL
    test_url = None
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # Default test URL (popular TikTok video)
        test_url = "https://www.tiktok.com/@khaborakyat/video/7436755283629279494"

    if test_url:
        results["Full Pipeline"] = test_valid_url(test_url)
    else:
        print(f"\n  {SKIP} No test URL provided. Pass a URL as argument.")

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        print(f"  {PASS if result else FAIL} {name}")
    print(f"\n  {passed}/{total} tests passed")
    print(f"{'='*60}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
