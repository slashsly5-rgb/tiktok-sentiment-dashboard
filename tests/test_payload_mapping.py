
import asyncio
import json
import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from scraper import scrape_video_via_apify

# Sample Apify Response
MOCK_APIFY_RESPONSE = [
    {
        "id": "7484302854369515038",
        "text": "This is a sample description #test #viral",
        "createTime": 1710000000,
        "authorMeta": {
            "id": "12345",
            "name": "susancrawford6741",
            "nickName": "Susan Crawford",
            "verified": False,
            "signature": "Hello",
            "avatar": "https://p16.tiktokcdn.com/avatar.jpg"
        },
        "videoMeta": {
            "height": 1080,
            "width": 576,
            "duration": 60,
            "coverUrl": "https://p16.tiktokcdn.com/cover.jpg",
            "definition": "720p",
            "format": "mp4"
        },
        "diggCount": 1500,
        "shareCount": 200,
        "playCount": 50000,
        "commentCount": 45,
        "hashtags": [
            {"id": "1", "name": "test", "title": "test", "cover": ""},
            {"id": "2", "name": "viral", "title": "viral", "cover": ""}
        ]
    }
]

class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data

class MockAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, url, json=None):
        return MockResponse(201, MOCK_APIFY_RESPONSE)

async def test_mapping():
    print("Testing Apify Payload Mapping with Mock Data...")
    
    # Patch httpx.AsyncClient with our simple Mock class
    with patch('httpx.AsyncClient', side_effect=MockAsyncClient):
        url = "https://www.tiktok.com/@susancrawford6741/video/7484302854369515038"
        result = await scrape_video_via_apify(url)
        
        print("\nMapped Result:")
        print(json.dumps(result, indent=2))
        
        if not result:
            print("FAILED: Result is None")
            return

        # Verify structure matches backend expectations
        expected_keys = ['url', 'description', 'author', 'thumbnail', 'stats', 'hashtags', 'comments']
        missing_keys = [k for k in expected_keys if k not in result]
        
        if missing_keys:
            print(f"FAILED: Missing keys: {missing_keys}")
        else:
            print("SUCCESS: All top-level keys present.")
            
        # Verify Stats
        stats = result['stats']
        if (stats['views'] == 50000 and 
            stats['likes'] == 1500 and 
            stats['shares'] == 200 and 
            stats['comments'] == 45):
            print("SUCCESS: Stats mapped correctly.")
        else:
            print(f"FAILED: Stats mismatch: {stats}")
            
        # Verify Hashtags
        expected_hashtags = ['test', 'viral']
        # The scraper extracts: [h.get('name') for h in item.get('hashtags', [])]
        if result['hashtags'] == expected_hashtags:
            print("SUCCESS: Hashtags mapped correctly.")
        else:
            print(f"FAILED: Hashtags mismatch: {result['hashtags']}")
        
        # Verify Author
        if result['author'] == "susancrawford6741":
             print("SUCCESS: Author mapped correctly.")
        else:
             print(f"FAILED: Author mismatch: {result['author']}")

if __name__ == "__main__":
    asyncio.run(test_mapping())
