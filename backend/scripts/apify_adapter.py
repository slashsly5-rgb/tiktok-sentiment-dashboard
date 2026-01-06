"""
Apify Data Adapter
Transforms Apify TikTok scraper output to our database schema
"""

from typing import Dict, Any, List


def transform_apify_to_schema(apify_data: Dict[str, Any], search_keyword: str = None) -> Dict[str, Any]:
    """
    Transform Apify TikTok scraper output to our database schema

    Apify format:
    {
        "id": "1234567890",
        "text": "Video description...",
        "authorMeta": {"name": "username"},
        "webVideoUrl": "https://...",
        "playCount": 12000,
        "diggCount": 450,
        "shareCount": 20,
        "commentCount": 89,
        "hashtags": [{"name": "politics"}]
    }

    Our schema:
    {
        "tiktok_id": "1234567890",
        "url": "https://...",
        "author_username": "username",
        "description": "...",
        "views_count": 12000,
        "likes_count": 450,
        "shares_count": 20,
        "comments_count": 89,
        "hashtags": ["politics"],
        "screenshot_base64": None,
        "search_keyword": "keyword"
    }

    Args:
        apify_data: Raw data from Apify TikTok scraper
        search_keyword: Optional search keyword to add

    Returns:
        Transformed data matching our database schema
    """
    return {
        "tiktok_id": apify_data.get("id"),
        "url": apify_data.get("webVideoUrl"),
        "author_username": apify_data.get("authorMeta", {}).get("name", "Unknown"),
        "description": apify_data.get("text", ""),
        "views_count": apify_data.get("playCount", 0),
        "likes_count": apify_data.get("diggCount", 0),
        "shares_count": apify_data.get("shareCount", 0),
        "comments_count": apify_data.get("commentCount", 0),
        "hashtags": [h.get("name") for h in apify_data.get("hashtags", [])],
        "screenshot_base64": None,  # Apify doesn't capture screenshots by default
        "search_keyword": search_keyword
    }


def transform_batch(apify_results: List[Dict[str, Any]], search_keyword: str = None) -> List[Dict[str, Any]]:
    """
    Transform a batch of Apify results

    Args:
        apify_results: List of raw Apify data
        search_keyword: Optional search keyword to add to all

    Returns:
        List of transformed data
    """
    return [transform_apify_to_schema(item, search_keyword) for item in apify_results]


# Example usage
if __name__ == "__main__":
    # Example Apify data
    sample_apify_data = {
        "id": "7123456789012345678",
        "text": "Breaking: New infrastructure project announced for Sarawak! #Sarawak #Development",
        "authorMeta": {
            "name": "sarawak_news",
            "verified": True
        },
        "webVideoUrl": "https://www.tiktok.com/@sarawak_news/video/7123456789012345678",
        "playCount": 15420,
        "diggCount": 892,
        "shareCount": 45,
        "commentCount": 127,
        "hashtags": [
            {"name": "Sarawak"},
            {"name": "Development"}
        ]
    }

    # Transform
    transformed = transform_apify_to_schema(sample_apify_data, "Sarawak development")

    print("Transformed data:")
    import json
    print(json.dumps(transformed, indent=2))
