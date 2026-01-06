"""
Field Transformation Utilities
Converts database snake_case fields to frontend camelCase fields
"""

from typing import Dict, List, Any, Optional


# ============================================
# DATABASE SCHEMA DOCUMENTATION
# ============================================

"""
VIDEOS TABLE FIELDS (Database snake_case -> Frontend camelCase):
- id -> id (UUID)
- tiktok_id -> tiktokId (string)
- url -> url (string)
- author_username -> authorUsername (string)
- description -> description (string)
- post_url -> postUrl (string, Supabase Storage URL)
- transcribed_url -> transcribedUrl (string, Supabase Storage URL)
- summary -> summary (string, AI-generated summary)
- screenshot_base64 -> screenshotBase64 (string, base64 encoded)
- views_count -> viewsCount (number)
- likes_count -> likesCount (number)
- shares_count -> sharesCount (number)
- comments_count -> commentsCount (number)
- hashtags -> hashtags (array)
- search_keyword -> searchKeyword (string)
- scraped_at -> scrapedAt (timestamp)
- created_at -> createdAt (timestamp)

COMMENTS TABLE FIELDS (Database snake_case -> Frontend camelCase):
- id -> id (UUID)
- video_id -> videoId (UUID)
- text -> text (string)
- comment_text -> commentText (string)
- author_username -> authorUsername (string)
- likes_count -> likesCount (number)
- created_at -> createdAt (timestamp)

SENTIMENT_ANALYSIS TABLE FIELDS (Database snake_case -> Frontend camelCase):
- id -> id (UUID)
- video_id -> videoId (UUID)
- overall_sentiment -> overallSentiment (string: positive/negative/neutral/mixed)
- sentiment -> sentiment (string: positive/negative/neutral/mixed)
- sentiment_score -> sentimentScore (number: 1-10)
- topic -> topic (string)
- discussion_points -> discussionPoints (string)
- key_issues -> keyIssues (array)
- transcript -> transcript (string)
- summary -> summary (string)
- analyzed_at -> analyzedAt (timestamp)
"""


# ============================================
# FIELD MAPPING DEFINITIONS
# ============================================

VIDEO_FIELD_MAP = {
    "id": "id",
    "tiktok_id": "tiktokId",
    "url": "url",
    "author_username": "authorUsername",
    "description": "description",
    "post_url": "postUrl",
    "transcribed_url": "transcribedUrl",
    "summary": "summary",
    "screenshot_base64": "screenshotBase64",
    "views_count": "viewsCount",
    "likes_count": "likesCount",
    "shares_count": "sharesCount",
    "comments_count": "commentsCount",
    "hashtags": "hashtags",
    "search_keyword": "searchKeyword",
    "scraped_at": "scrapedAt",
    "created_at": "createdAt",
    # Computed fields
    "engagement_rate": "engagementRate",
    # Sentiment fields (when flattened from sentiment_analysis join)
    "sentiment": "sentiment",
    "sentiment_score": "sentimentScore",
    "topic": "topic",
    "key_issues": "keyIssues"
}

COMMENT_FIELD_MAP = {
    "id": "id",
    "video_id": "videoId",
    "text": "text",
    "comment_text": "commentText",
    "author_username": "authorUsername",
    "likes_count": "likesCount",
    "created_at": "createdAt"
}

SENTIMENT_FIELD_MAP = {
    "id": "id",
    "video_id": "videoId",
    "overall_sentiment": "overallSentiment",
    "sentiment": "sentiment",
    "sentiment_score": "sentimentScore",
    "topic": "topic",
    "discussion_points": "discussionPoints",
    "key_issues": "keyIssues",
    "transcript": "transcript",
    "summary": "summary",
    "analyzed_at": "analyzedAt"
}


# ============================================
# TRANSFORMATION FUNCTIONS
# ============================================

def transform_video(video: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a single video record from database format to frontend format

    Args:
        video: Video record with snake_case fields

    Returns:
        Video record with camelCase fields
    """
    if not video:
        return None

    transformed = {}

    for db_field, frontend_field in VIDEO_FIELD_MAP.items():
        if db_field in video:
            transformed[frontend_field] = video[db_field]

    # Parse hashtags from JSON string to array of tag names
    if "hashtags" in transformed:
        import json
        hashtags_value = transformed["hashtags"]
        if isinstance(hashtags_value, str):
            try:
                # Parse JSON string
                parsed = json.loads(hashtags_value)
                if isinstance(parsed, list):
                    # Extract tag names from objects like [{"id":"123","name":"tag"}]
                    transformed["hashtags"] = [tag.get("name", tag) if isinstance(tag, dict) else tag for tag in parsed]
                else:
                    transformed["hashtags"] = []
            except (json.JSONDecodeError, AttributeError):
                transformed["hashtags"] = []
        elif not isinstance(hashtags_value, list):
            transformed["hashtags"] = []

    # Handle nested sentiment data if present
    if "sentiment" in video and isinstance(video["sentiment"], dict):
        transformed["sentiment"] = transform_sentiment(video["sentiment"])
    elif "sentiment" in video and isinstance(video["sentiment"], list):
        # Handle array of sentiments (shouldn't happen but just in case)
        transformed["sentiment"] = [transform_sentiment(s) for s in video["sentiment"]] if video["sentiment"] else None

    # Handle nested comments if present
    if "comments" in video:
        if isinstance(video["comments"], list):
            transformed["comments"] = [transform_comment(c) for c in video["comments"]]
        else:
            transformed["comments"] = video["comments"]  # None or already transformed

    return transformed


def transform_comment(comment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a single comment record from database format to frontend format

    Args:
        comment: Comment record with snake_case fields

    Returns:
        Comment record with camelCase fields
    """
    if not comment:
        return None

    transformed = {}

    for db_field, frontend_field in COMMENT_FIELD_MAP.items():
        if db_field in comment:
            transformed[frontend_field] = comment[db_field]

    # Normalize text field - prefer comment_text over text
    if "commentText" not in transformed and "text" in transformed:
        transformed["commentText"] = transformed["text"]

    return transformed


def transform_sentiment(sentiment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a single sentiment record from database format to frontend format

    Args:
        sentiment: Sentiment record with snake_case fields

    Returns:
        Sentiment record with camelCase fields
    """
    if not sentiment:
        return None

    transformed = {}

    for db_field, frontend_field in SENTIMENT_FIELD_MAP.items():
        if db_field in sentiment:
            transformed[frontend_field] = sentiment[db_field]

    # Normalize sentiment field - prefer overall_sentiment if both exist
    if "overallSentiment" in transformed and "sentiment" not in transformed:
        transformed["sentiment"] = transformed["overallSentiment"]
    elif "sentiment" not in transformed and "overallSentiment" not in transformed:
        # Neither field exists
        pass

    # Include video if nested
    if "video" in sentiment:
        transformed["video"] = transform_video(sentiment["video"]) if sentiment["video"] else None

    return transformed


def transform_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform a list of video records

    Args:
        videos: List of video records with snake_case fields

    Returns:
        List of video records with camelCase fields
    """
    if not videos:
        return []
    return [transform_video(v) for v in videos]


def transform_comments(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform a list of comment records

    Args:
        comments: List of comment records with snake_case fields

    Returns:
        List of comment records with camelCase fields
    """
    if not comments:
        return []
    return [transform_comment(c) for c in comments]


def transform_sentiments(sentiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform a list of sentiment records

    Args:
        sentiments: List of sentiment records with snake_case fields

    Returns:
        List of sentiment records with camelCase fields
    """
    if not sentiments:
        return []
    return [transform_sentiment(s) for s in sentiments]


# ============================================
# STATISTICS & ANALYTICS TRANSFORMATIONS
# ============================================

def transform_keys_to_camel(obj: Any) -> Any:
    """
    Recursively transform all dictionary keys from snake_case to camelCase
    Handles nested dictionaries, lists, and primitive types

    Args:
        obj: Object to transform (dict, list, or primitive)

    Returns:
        Transformed object with camelCase keys
    """
    if isinstance(obj, dict):
        return {snake_to_camel(k): transform_keys_to_camel(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [transform_keys_to_camel(item) for item in obj]
    else:
        return obj


def snake_to_camel(snake_str: str) -> str:
    """
    Convert snake_case string to camelCase

    Args:
        snake_str: String in snake_case format

    Returns:
        String in camelCase format

    Examples:
        >>> snake_to_camel("hello_world")
        'helloWorld'
        >>> snake_to_camel("video_count")
        'videoCount'
        >>> snake_to_camel("avg_sentiment_score")
        'avgSentimentScore'
    """
    components = snake_str.split('_')
    # Keep the first component as-is, capitalize the rest
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    Convert camelCase string to snake_case

    Args:
        camel_str: String in camelCase format

    Returns:
        String in snake_case format

    Examples:
        >>> camel_to_snake("helloWorld")
        'hello_world'
        >>> camel_to_snake("videoCount")
        'video_count'
    """
    import re
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str).lower()


# ============================================
# COMPLEX OBJECT TRANSFORMATIONS
# ============================================

def transform_complete_video_view(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform complete video view (video + comments + sentiment + stats)

    Args:
        data: Complete video view with nested objects

    Returns:
        Transformed complete video view
    """
    if not data:
        return None

    return {
        "video": transform_video(data.get("video")),
        "comments": transform_comments(data.get("comments", [])),
        "sentiment": transform_sentiment(data.get("sentiment")),
        "stats": transform_keys_to_camel(data.get("stats", {}))
    }


def transform_dashboard_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform dashboard analytics data

    Args:
        data: Dashboard analytics with various nested structures

    Returns:
        Transformed dashboard analytics with camelCase keys
    """
    if not data:
        return {}

    return {
        "periodDays": data.get("period_days"),
        "videoStats": transform_keys_to_camel(data.get("video_stats", {})),
        "sentimentStats": transform_keys_to_camel(data.get("sentiment_stats", {})),
        "topAuthors": transform_keys_to_camel(data.get("top_authors", [])),
        "topHashtags": transform_keys_to_camel(data.get("top_hashtags", [])),
        "topKeywords": transform_keys_to_camel(data.get("top_keywords", []))
    }


def transform_sentiment_overview(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform sentiment overview statistics

    Args:
        data: Sentiment overview data

    Returns:
        Transformed sentiment overview with camelCase keys
    """
    return transform_keys_to_camel(data)


def transform_pagination_response(data: List[Dict[str, Any]],
                                  total: int,
                                  offset: int,
                                  limit: int,
                                  transform_fn,
                                  data_key: str = "items") -> Dict[str, Any]:
    """
    Create a paginated response with transformed data

    Args:
        data: List of items to transform
        total: Total number of items available
        offset: Current offset
        limit: Items per page
        transform_fn: Function to transform each item
        data_key: Key name for the data array in response

    Returns:
        Paginated response with camelCase fields
    """
    return {
        "count": len(data),
        "total": total,
        "offset": offset,
        "limit": limit,
        data_key: [transform_fn(item) for item in data] if data else []
    }
