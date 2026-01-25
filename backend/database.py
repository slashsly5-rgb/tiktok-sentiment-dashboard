"""
Database module for TikTok Political Sentiment Scraper
Handles all Supabase database operations
"""

import time
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from config import Config
import logging

# Configure logging
logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase database client with retry logic and error handling"""

    def __init__(self):
        """Initialize Supabase client"""
        Config.validate()
        self.supabase: Client = self._connect_with_retry()

    def _connect_with_retry(self) -> Client:
        """Connect to Supabase with retry logic"""
        for attempt in range(Config.DB_RETRY_ATTEMPTS):
            try:
                key = Config.SUPABASE_SERVICE_ROLE_KEY
                if key:
                    logger.info(f"DEBUG: Using Supabase Key starting with: {key[:5]}...")
                
                client = create_client(
                    Config.SUPABASE_URL,
                    key
                )
                logger.info("Successfully connected to Supabase")
                return client
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < Config.DB_RETRY_ATTEMPTS - 1:
                    time.sleep(Config.DB_RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    raise Exception(f"Failed to connect to Supabase after {Config.DB_RETRY_ATTEMPTS} attempts")

    # ============================================
    # Maintenance Operations
    # ============================================
    def clear_all_data(self) -> bool:
        """
        Delete ALL data from the database (Videos, Comments, Sentiment)
        Used for full reset.
        """
        try:
            # Delete from 'videos' table. Cascade should handle related tables if configured,
            # but explicit deletion is safer if cascade isn't set up.
            # Supabase delete requires a 'where' clause. Using neq "id" to "0000" covers all UUIDs.
            
            logger.warning("EXECUTION DESTRUCTIVE ACTION: Clearing all database tables...")
            
            # 1. Clear Sentiment Analysis (if no cascade)
            self.supabase.table("sentiment_analysis").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            # 2. Clear Comments (if no cascade)
            self.supabase.table("comments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            # 3. Clear Videos
            self.supabase.table("videos").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            logger.info("Database successfully cleared.")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False

    # ============================================
    # Video Operations
    # ============================================

    def insert_video(self, video_data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a video record and return its UUID

        Args:
            video_data: Dictionary containing video metadata

        Returns:
            Video UUID if successful, None otherwise
        """
        try:
            response = self.supabase.table("videos").insert(video_data).execute()
            video_id = response.data[0]["id"]
            logger.info(f"Inserted video {video_data.get('tiktok_id')} with ID {video_id}")
            return video_id
        except Exception as e:
            logger.error(f"Error inserting video: {e}")
            return None

    def update_video(self, video_data: Dict[str, Any]) -> bool:
        """
        Update an existing video record with new stats

        Args:
            video_data: Dictionary containing video metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            tiktok_id = video_data.get('tiktok_id')
            if not tiktok_id:
                return False

            # Fields to update
            update_payload = {
                "views_count": video_data.get("views_count", 0),
                "likes_count": video_data.get("likes_count", 0),
                "shares_count": video_data.get("shares_count", 0),
                "comments_count": video_data.get("comments_count", 0),
                "description": video_data.get("description", ""),
                "author_username": video_data.get("author_username", "Unknown"),
                "scraped_at": datetime.now().isoformat()
            }

            self.supabase.table("videos").update(update_payload).eq("tiktok_id", tiktok_id).execute()
            logger.info(f"Updated video {tiktok_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating video: {e}")
            return False

    def get_video_by_tiktok_id(self, tiktok_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a video already exists by tiktok_id

        Args:
            tiktok_id: TikTok video ID

        Returns:
            Video record if exists, None otherwise
        """
        try:
            response = self.supabase.table("videos").select("*").eq("tiktok_id", tiktok_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error checking video existence: {e}")
            return None

    def get_recent_videos(self, days: int = 7, keyword: Optional[str] = None, limit: int = 100, include_sentiment: bool = False) -> List[Dict[str, Any]]:
        """
        Get recent videos from the database

        Args:
            days: Number of days to look back
            keyword: Optional keyword filter
            limit: Maximum number of videos to return
            include_sentiment: Whether to include sentiment analysis data

        Returns:
            List of video records with optional sentiment data
        """
        try:
            from datetime import datetime, timedelta

            # Use Supabase join syntax to get videos with sentiment in one query
            if include_sentiment:
                query = self.supabase.table("videos").select("*, sentiment_analysis(*)")
            else:
                query = self.supabase.table("videos").select("*")

            # Filter by keyword if provided
            if keyword:
                query = query.eq("search_keyword", keyword)

            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Filter by date and order
            response = query.gte("scraped_at", cutoff_date) \
                            .order("scraped_at", desc=True) \
                            .limit(limit) \
                            .execute()

            videos = response.data
            
            # FAILSAFE: Enforce strict python-side filtering
            # (Just in case DB query ignores filter for some reason)
            if keyword and videos:
                videos = [v for v in videos if v.get("search_keyword") == keyword]

            # Flatten sentiment data if included
            if include_sentiment and videos:
                for video in videos:
                    sentiment_data = video.get('sentiment_analysis')
                    logger.debug(f"Video {video.get('id')}: sentiment_data type={type(sentiment_data)}, value={sentiment_data}")
                    if sentiment_data:
                        # sentiment_analysis is returned as an object (dict), not an array
                        # Supabase returns as a list with one item when using join
                        if isinstance(sentiment_data, list) and len(sentiment_data) > 0:
                            sentiment_data = sentiment_data[0]

                        if isinstance(sentiment_data, dict):
                            video['sentiment'] = sentiment_data.get('sentiment')
                            video['sentiment_score'] = sentiment_data.get('sentiment_score')
                            video['summary'] = sentiment_data.get('discussion_points')  # Use discussion_points
                            video['topic'] = sentiment_data.get('topic')
                            video['key_issues'] = sentiment_data.get('key_issues', [])
                            video['trend_context'] = sentiment_data.get('trend_context', "N/A")
                            video['viral_potential'] = sentiment_data.get('viral_potential', "Low")
                        # Remove the nested object
                        del video['sentiment_analysis']

            return videos
        except Exception as e:
            logger.error(f"Error fetching recent videos: {e}")
            return []

    def get_video_by_id(self, video_id: str, include_comments: bool = False, include_sentiment: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a single video by UUID with optional includes

        Args:
            video_id: Video UUID
            include_comments: Whether to include comments
            include_sentiment: Whether to include sentiment analysis

        Returns:
            Video record with optional comments and sentiment
        """
        try:
            # Get video
            video_response = self.supabase.table("videos").select("*").eq("id", video_id).execute()
            if not video_response.data:
                return None

            video = video_response.data[0]

            # Include comments if requested
            if include_comments:
                comments_response = self.supabase.table("comments").select("*").eq("video_id", video_id).order("created_at", desc=True).execute()
                video["comments"] = comments_response.data
            else:
                video["comments"] = None

            # Include sentiment if requested
            if include_sentiment:
                sentiment_response = self.supabase.table("sentiment_analysis").select("*").eq("video_id", video_id).execute()
                video["sentiment"] = sentiment_response.data[0] if sentiment_response.data else None
            else:
                video["sentiment"] = None

            return video
        except Exception as e:
            logger.error(f"Error fetching video by ID: {e}")
            return None

    def get_sentiment_by_video_id(self, video_id: str, include_video: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get sentiment analysis for a specific video

        Args:
            video_id: Video UUID
            include_video: Whether to include the video details

        Returns:
            Sentiment analysis record with optional video
        """
        try:
            sentiment_response = self.supabase.table("sentiment_analysis").select("*").eq("video_id", video_id).execute()

            if not sentiment_response.data:
                return None

            sentiment = sentiment_response.data[0]

            # Include video if requested
            if include_video:
                video_response = self.supabase.table("videos").select("*").eq("id", video_id).execute()
                sentiment["video"] = video_response.data[0] if video_response.data else None
            else:
                sentiment["video"] = None

            return sentiment
        except Exception as e:
            logger.error(f"Error fetching sentiment by video ID: {e}")
            return None

    def get_complete_video_view(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete view: video + all comments + sentiment in one call

        Args:
            video_id: Video UUID

        Returns:
            Dictionary with video, comments, sentiment, and stats
        """
        try:
            # Get video
            video_response = self.supabase.table("videos").select("*").eq("id", video_id).execute()
            if not video_response.data:
                return None

            video = video_response.data[0]

            # Get comments
            comments_response = self.supabase.table("comments").select("*").eq("video_id", video_id).order("created_at", desc=True).execute()
            comments = comments_response.data

            # Get sentiment
            sentiment_response = self.supabase.table("sentiment_analysis").select("*").eq("video_id", video_id).execute()
            sentiment = sentiment_response.data[0] if sentiment_response.data else None

            return {
                "video": video,
                "comments": comments,
                "sentiment": sentiment,
                "stats": {
                    "comment_count": len(comments),
                    "analyzed": sentiment is not None
                }
            }
        except Exception as e:
            logger.error(f"Error fetching complete video view: {e}")
            return None

    def get_video_with_comments(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a video with its comments (for analysis)
        Legacy method - kept for backward compatibility

        Args:
            video_id: Video UUID

        Returns:
            Video record with comments
        """
        try:
            # Get video
            video_response = self.supabase.table("videos").select("*").eq("id", video_id).execute()
            if not video_response.data:
                return None

            video = video_response.data[0]

            # Get comments
            comments_response = self.supabase.table("comments").select("*").eq("video_id", video_id).execute()
            video["comments"] = comments_response.data

            return video
        except Exception as e:
            logger.error(f"Error fetching video with comments: {e}")
            return None

    def get_unanalyzed_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get videos that haven't been analyzed yet

        Args:
            limit: Maximum number of videos to return

        Returns:
            List of unanalyzed video records
        """
        try:
            # Get all video IDs
            all_videos = self.supabase.table("videos").select("id").execute()
            all_video_ids = [v["id"] for v in all_videos.data]

            # Get analyzed video IDs
            analyzed = self.supabase.table("sentiment_analysis").select("video_id").execute()
            analyzed_ids = [a["video_id"] for a in analyzed.data]

            # Find unanalyzed IDs
            unanalyzed_ids = [vid for vid in all_video_ids if vid not in analyzed_ids]

            if not unanalyzed_ids:
                return []

            # Get full video records
            response = self.supabase.table("videos").select("*").in_("id", unanalyzed_ids[:limit]).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching unanalyzed videos: {e}")
            return []

    # ============================================
    # Comment Operations
    # ============================================

    def get_comments(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get comments with pagination and filtering

        Args:
            filters: Dictionary of filter criteria (video_id, author_username, min_likes, days)
            limit: Maximum number of comments to return (capped at Config.MAX_LIMIT)
            offset: Pagination offset

        Returns:
            Dictionary with 'data' (list of comments) and 'total' (total count)
        """
        try:
            from datetime import datetime, timedelta
            from config import Config

            limit = min(limit, Config.MAX_LIMIT)
            filters = filters or {}

            query = self.supabase.table("comments").select("*", count="exact")

            # Apply filters
            if filters.get('video_id'):
                query = query.eq('video_id', filters['video_id'])

            if filters.get('author_username'):
                query = query.ilike('author_username', f"%{filters['author_username']}%")

            if filters.get('min_likes'):
                query = query.gte('likes_count', filters['min_likes'])

            if filters.get('days'):
                cutoff_date = (datetime.now() - timedelta(days=filters['days'])).isoformat()
                query = query.gte('created_at', cutoff_date)

            # Order and paginate
            response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

            return {
                "data": response.data,
                "total": response.count if hasattr(response, 'count') else len(response.data)
            }
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return {"data": [], "total": 0}

    def get_comment_by_id(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single comment by UUID

        Args:
            comment_id: Comment UUID

        Returns:
            Comment record if found, None otherwise
        """
        try:
            response = self.supabase.table("comments").select("*").eq("id", comment_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching comment by ID: {e}")
            return None

    def get_comments_for_video(self, video_id: str, limit: int = 100, offset: int = 0, min_likes: int = None) -> Dict[str, Any]:
        """
        Get all comments for a specific video

        Args:
            video_id: Video UUID
            limit: Maximum number of comments
            offset: Pagination offset
            min_likes: Minimum likes filter (optional)

        Returns:
            Dictionary with 'data' and 'total'
        """
        try:
            from config import Config
            limit = min(limit, Config.MAX_LIMIT)

            query = self.supabase.table("comments").select("*", count="exact").eq("video_id", video_id)

            if min_likes is not None:
                query = query.gte('likes_count', min_likes)

            response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

            return {
                "data": response.data,
                "total": response.count if hasattr(response, 'count') else len(response.data)
            }
        except Exception as e:
            logger.error(f"Error fetching comments for video: {e}")
            return {"data": [], "total": 0}

    def get_comment_statistics(self, days: int = 7, video_id: str = None) -> Dict[str, Any]:
        """
        Get comment statistics and insights

        Args:
            days: Number of days to look back
            video_id: Optional video ID to filter by

        Returns:
            Dictionary with comment statistics
        """
        try:
            from datetime import datetime, timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Base query
            query = self.supabase.table("comments").select("*").gte("created_at", cutoff_date)

            if video_id:
                query = query.eq("video_id", video_id)

            response = query.execute()
            comments = response.data

            if not comments:
                return {
                    "total_comments": 0,
                    "unique_authors": 0,
                    "avg_likes_per_comment": 0,
                    "total_likes": 0
                }

            # Calculate statistics
            unique_authors = len(set(c.get("author_username") for c in comments))
            total_likes = sum(c.get("likes_count", 0) for c in comments)
            avg_likes = total_likes / len(comments) if comments else 0

            return {
                "total_comments": len(comments),
                "unique_authors": unique_authors,
                "avg_likes_per_comment": round(avg_likes, 2),
                "total_likes": total_likes,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error calculating comment statistics: {e}")
            return {
                "total_comments": 0,
                "unique_authors": 0,
                "avg_likes_per_comment": 0,
                "total_likes": 0
            }

    def get_top_commenters(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most active commenters

        Args:
            days: Number of days to look back
            limit: Maximum number of top commenters to return

        Returns:
            List of top commenters with stats
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            response = self.supabase.table("comments").select("author_username, likes_count").gte("created_at", cutoff_date).execute()

            if not response.data:
                return []

            # Aggregate by author
            author_stats = defaultdict(lambda: {"comment_count": 0, "total_likes": 0})

            for comment in response.data:
                username = comment.get("author_username")
                if username:
                    author_stats[username]["comment_count"] += 1
                    author_stats[username]["total_likes"] += comment.get("likes_count", 0)

            # Convert to list and calculate avg
            top_commenters = []
            for username, stats in author_stats.items():
                avg_likes = stats["total_likes"] / stats["comment_count"] if stats["comment_count"] > 0 else 0
                top_commenters.append({
                    "username": username,
                    "comment_count": stats["comment_count"],
                    "total_likes": stats["total_likes"],
                    "avg_likes": round(avg_likes, 2)
                })

            # Sort by comment count and limit
            top_commenters.sort(key=lambda x: x["comment_count"], reverse=True)
            return top_commenters[:limit]

        except Exception as e:
            logger.error(f"Error getting top commenters: {e}")
            return []

    def insert_comments(self, video_id: str, comments: List[Dict[str, Any]]) -> bool:
        """
        Batch insert comments for a video

        Args:
            video_id: Video UUID
            comments: List of comment dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add video_id to each comment
            comments_with_id = [{"video_id": video_id, **comment} for comment in comments]

            self.supabase.table("comments").insert(comments_with_id).execute()
            logger.info(f"Inserted {len(comments)} comments for video {video_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting comments: {e}")
            return False

    # ============================================
    # Advanced Filtering & Search Operations
    # ============================================

    def search_videos(self, filters: Dict[str, Any] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Multi-criteria video search with incremental query building

        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of videos
            offset: Pagination offset

        Returns:
            Dictionary with 'data' and 'total'
        """
        try:
            from datetime import datetime, timedelta
            from config import Config

            limit = min(limit, Config.MAX_LIMIT)
            filters = filters or {}

            query = self.supabase.table("videos").select("*", count="exact")

            # Apply filters incrementally
            if filters.get('keyword'):
                keyword = filters['keyword']
                query = query.or_(f"description.ilike.%{keyword}%,search_keyword.ilike.%{keyword}%")

            if filters.get('author_username'):
                query = query.eq('author_username', filters['author_username'])

            if filters.get('hashtag'):
                query = query.contains('hashtags', [filters['hashtag']])

            if filters.get('min_views'):
                query = query.gte('views_count', filters['min_views'])

            if filters.get('max_views'):
                query = query.lte('views_count', filters['max_views'])

            if filters.get('min_likes'):
                query = query.gte('likes_count', filters['min_likes'])

            if filters.get('min_comments'):
                query = query.gte('comments_count', filters['min_comments'])

            if filters.get('min_shares'):
                query = query.gte('shares_count', filters['min_shares'])

            if filters.get('date_from'):
                query = query.gte('scraped_at', filters['date_from'])

            if filters.get('date_to'):
                query = query.lte('scraped_at', filters['date_to'])

            # Sorting
            sort_by = filters.get('sort_by', 'scraped_at')
            sort_order = filters.get('sort_order', 'desc')
            desc = (sort_order.lower() == 'desc')

            response = query.order(sort_by, desc=desc).range(offset, offset + limit - 1).execute()

            return {
                "data": response.data,
                "total": response.count if hasattr(response, 'count') else len(response.data)
            }
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return {"data": [], "total": 0}

    def get_videos_by_author(self, username: str, limit: int = 50, offset: int = 0, sort_by: str = "scraped_at") -> Dict[str, Any]:
        """
        Get all videos by specific author with stats

        Args:
            username: Author username
            limit: Maximum videos
            offset: Pagination offset
            sort_by: Sort field

        Returns:
            Dictionary with videos, stats, and total
        """
        try:
            from config import Config
            limit = min(limit, Config.MAX_LIMIT)

            # Get videos
            query = self.supabase.table("videos").select("*", count="exact").eq('author_username', username)
            response = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

            videos = response.data
            total = response.count if hasattr(response, 'count') else len(videos)

            # Calculate stats
            total_views = sum(v.get('views_count', 0) for v in videos)
            total_likes = sum(v.get('likes_count', 0) for v in videos)

            return {
                "data": videos,
                "total": total,
                "stats": {
                    "total_videos": total,
                    "total_views": total_views,
                    "total_likes": total_likes
                }
            }
        except Exception as e:
            logger.error(f"Error getting videos by author: {e}")
            return {"data": [], "total": 0, "stats": {}}

    def get_videos_by_hashtag(self, hashtag: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get videos with specific hashtag (JSONB query)

        Args:
            hashtag: Hashtag to search for
            limit: Maximum videos
            offset: Pagination offset

        Returns:
            Dictionary with 'data' and 'total'
        """
        try:
            from config import Config
            limit = min(limit, Config.MAX_LIMIT)

            # Ensure hashtag starts with #
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"

            query = self.supabase.table("videos").select("*", count="exact")
            response = query.contains('hashtags', [hashtag]).order("scraped_at", desc=True).range(offset, offset + limit - 1).execute()

            return {
                "data": response.data,
                "total": response.count if hasattr(response, 'count') else len(response.data)
            }
        except Exception as e:
            logger.error(f"Error getting videos by hashtag: {e}")
            return {"data": [], "total": 0}

    def get_trending_videos(self, days: int = 7, limit: int = 20, metric: str = "views") -> List[Dict[str, Any]]:
        """
        Get trending videos by engagement rate in recent period

        Args:
            days: Number of days to look back
            limit: Maximum videos
            metric: Metric to sort by (views, likes, engagement_rate)

        Returns:
            List of trending videos with engagement_rate calculated
        """
        try:
            from datetime import datetime, timedelta
            from config import Config

            limit = min(limit, Config.MAX_LIMIT)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            response = self.supabase.table("videos").select("*").gte("scraped_at", cutoff_date).execute()

            videos = response.data

            # Calculate engagement rate for each video
            for video in videos:
                views = video.get('views_count', 0)
                likes = video.get('likes_count', 0)
                comments = video.get('comments_count', 0)
                shares = video.get('shares_count', 0)

                if views > 0:
                    video['engagement_rate'] = round((likes + comments + shares) / views, 4)
                else:
                    video['engagement_rate'] = 0

            # Sort by metric
            if metric == "engagement_rate":
                videos.sort(key=lambda x: x.get('engagement_rate', 0), reverse=True)
            elif metric == "likes":
                videos.sort(key=lambda x: x.get('likes_count', 0), reverse=True)
            else:  # views
                videos.sort(key=lambda x: x.get('views_count', 0), reverse=True)

            return videos[:limit]

        except Exception as e:
            logger.error(f"Error getting trending videos: {e}")
            return []

    def get_analyses_by_sentiment(self, sentiment_type: str, limit: int = 50, offset: int = 0, include_videos: bool = False) -> Dict[str, Any]:
        """
        Filter sentiment analyses by type

        Args:
            sentiment_type: Sentiment type (positive, negative, neutral, mixed)
            limit: Maximum analyses
            offset: Pagination offset
            include_videos: Whether to include video data

        Returns:
            Dictionary with 'data' and 'total'
        """
        try:
            from config import Config
            limit = min(limit, Config.MAX_LIMIT)

            query = self.supabase.table("sentiment_analysis").select("*", count="exact")
            response = query.ilike('sentiment', f"%{sentiment_type}%").order("analyzed_at", desc=True).range(offset, offset + limit - 1).execute()

            analyses = response.data

            # Include videos if requested
            if include_videos and analyses:
                video_ids = [a['video_id'] for a in analyses]
                videos_response = self.supabase.table("videos").select("*").in_('id', video_ids).execute()
                videos_dict = {v['id']: v for v in videos_response.data}

                for analysis in analyses:
                    analysis['video'] = videos_dict.get(analysis['video_id'])

            return {
                "data": analyses,
                "total": response.count if hasattr(response, 'count') else len(analyses)
            }
        except Exception as e:
            logger.error(f"Error getting analyses by sentiment: {e}")
            return {"data": [], "total": 0}

    def get_analyses_by_score_range(self, min_score: float = None, max_score: float = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Filter sentiment by score range

        Args:
            min_score: Minimum sentiment score (1-10)
            max_score: Maximum sentiment score (1-10)
            limit: Maximum analyses
            offset: Pagination offset

        Returns:
            Dictionary with 'data' and 'total'
        """
        try:
            from config import Config
            limit = min(limit, Config.MAX_LIMIT)

            query = self.supabase.table("sentiment_analysis").select("*", count="exact")

            if min_score is not None:
                query = query.gte('sentiment_score', min_score)

            if max_score is not None:
                query = query.lte('sentiment_score', max_score)

            response = query.order("sentiment_score", desc=True).range(offset, offset + limit - 1).execute()

            return {
                "data": response.data,
                "total": response.count if hasattr(response, 'count') else len(response.data)
            }
        except Exception as e:
            logger.error(f"Error getting analyses by score range: {e}")
            return {"data": [], "total": 0}

    # ============================================
    # Sentiment Analysis Operations
    # ============================================

    def insert_sentiment(self, video_id: str, analysis: Dict[str, Any]) -> bool:
        """
        Insert sentiment analysis results for a video

        Args:
            video_id: Video UUID
            analysis: Dictionary containing analysis results

        Returns:
            True if successful, False otherwise
        """
        try:
            analysis_data = {
                "video_id": video_id,
                "topic": analysis.get("topic"),
                "discussion_points": analysis.get("discussion", analysis.get("discussion_points")),
                "sentiment": analysis.get("sentiment"),
                "sentiment_score": int(analysis.get("score", 0)) if analysis.get("score") else None,
                "key_issues": analysis.get("key_issues", []),
                "transcript": analysis.get("transcript"),
                "summary": analysis.get("summary"),
            }

            self.supabase.table("sentiment_analysis").insert(analysis_data).execute()
            logger.info(f"Inserted sentiment analysis for video {video_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting sentiment analysis: {e}")
            return False

    def get_sentiment_overview(self, days: int = 7, keyword: str = None) -> Dict[str, Any]:
        """
        Get aggregated sentiment statistics

        Args:
            days: Number of days to look back
            keyword: Optional search keyword to filter by

        Returns:
            Dictionary with sentiment overview
        """
        try:
            from datetime import datetime, timedelta
            
            # Calculate cutoff date in Python
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get recent videos with sentiment
            query = self.supabase.table("videos") \
                .select("id, search_keyword, views_count") \
                .gte("scraped_at", cutoff_date)
            
            if keyword:
                query = query.eq("search_keyword", keyword)
                
            videos_response = query.execute()

            total_videos = len(videos_response.data)
            video_ids = [v["id"] for v in videos_response.data]

            if not video_ids:
                return {
                    "total_videos": 0,
                    "total_analyzed": 0,
                    "avg_sentiment": 0,
                    "sentiment_breakdown": {},
                    "top_keyword": "N/A",
                    "total_views": 0
                }

            # Get sentiment analysis for these videos
            sentiment_response = self.supabase.table("sentiment_analysis") \
                .select("*") \
                .in_("video_id", video_ids) \
                .execute()

            sentiments = sentiment_response.data
            total_analyzed = len(sentiments)

            # Calculate averages and breakdowns
            sentiment_scores = [s["sentiment_score"] for s in sentiments if s.get("sentiment_score")]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

            # Sentiment breakdown
            sentiment_counts = {}
            for s in sentiments:
                sent_type = s.get("sentiment", "Unknown")
                sentiment_counts[sent_type] = sentiment_counts.get(sent_type, 0) + 1

            # Top keyword
            keyword_counts = {}
            for v in videos_response.data:
                kw = v.get("search_keyword", "Unknown")
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
            top_keyword = max(keyword_counts, key=keyword_counts.get) if keyword_counts else "N/A"

            # Total views
            total_views = sum(v.get("views_count", 0) for v in videos_response.data)

            return {
                "total_videos": total_videos,
                "total_analyzed": total_analyzed,
                "avg_sentiment": round(avg_sentiment, 1),
                "sentiment_breakdown": sentiment_counts,
                "top_keyword": top_keyword,
                "total_views": total_views
            }
        except Exception as e:
            logger.error(f"Error getting sentiment overview: {e}")
            return {
                "total_videos": 0,
                "total_analyzed": 0,
                "avg_sentiment": 0,
                "sentiment_breakdown": {},
                "top_keyword": "Error",
                "total_views": 0
            }

    # ============================================
    # Analytics & Statistics Operations
    # ============================================

    def get_dashboard_analytics(self, days: int = 7, keyword: str = None) -> Dict[str, Any]:
        """
        Comprehensive dashboard data in one call

        Args:
            days: Number of days to look back
            keyword: Optional search keyword to filter by

        Returns:
            Dictionary with video stats, sentiment stats, top authors, top hashtags, top keywords
        """
        try:
            from datetime import datetime, timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get videos
            query = self.supabase.table("videos").select("*").gte("scraped_at", cutoff_date)
            if keyword:
                query = query.eq("search_keyword", keyword)
                
            videos_response = query.execute()
            videos = videos_response.data

            video_stats = {
                "total": len(videos),
                "total_views": sum(v.get('views_count', 0) for v in videos),
                "total_likes": sum(v.get('likes_count', 0) for v in videos),
                "total_comments": sum(v.get('comments_count', 0) for v in videos),
                "total_shares": sum(v.get('shares_count', 0) for v in videos),
                "avg_views_per_video": round(sum(v.get('views_count', 0) for v in videos) / len(videos), 2) if videos else 0
            }

            # Get sentiment stats
            if videos:
                video_ids = [v['id'] for v in videos]
                sentiment_response = self.supabase.table("sentiment_analysis").select("*").in_('video_id', video_ids).execute()
                sentiments = sentiment_response.data

                sentiment_breakdown = {}
                for s in sentiments:
                    sent_type = s.get('sentiment', 'Unknown')
                    sentiment_breakdown[sent_type] = sentiment_breakdown.get(sent_type, 0) + 1

                avg_score = round(sum(s.get('sentiment_score', 0) for s in sentiments) / len(sentiments), 2) if sentiments else 0

                sentiment_stats = {
                    "analyzed_count": len(sentiments),
                    "avg_score": avg_score,
                    "sentiment_breakdown": sentiment_breakdown
                }
            else:
                sentiment_stats = {"analyzed_count": 0, "avg_score": 0, "sentiment_breakdown": {}}

            # Top 5 authors
            top_authors = self.get_top_authors(days, 5, "videos")[:5]

            # Top 10 hashtags
            top_hashtags = self.get_top_hashtags(days, 10)[:10]

            # Keyword performance
            keyword_stats = self.get_keyword_performance(days)[:5]

            return {
                "period_days": days,
                "video_stats": video_stats,
                "sentiment_stats": sentiment_stats,
                "top_authors": top_authors,
                "top_hashtags": top_hashtags,
                "top_keywords": keyword_stats
            }

        except Exception as e:
            logger.error(f"Error getting dashboard analytics: {e}")
            return {}

    def get_top_authors(self, days: int = 30, limit: int = 10, metric: str = "videos") -> List[Dict[str, Any]]:
        """
        Top content creators by metric

        Args:
            days: Number of days to look back
            limit: Maximum authors to return
            metric: Metric to sort by (videos, views, likes, engagement)

        Returns:
            List of top authors with stats
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            videos_response = self.supabase.table("videos").select("*").gte("scraped_at", cutoff_date).execute()
            videos = videos_response.data

            if not videos:
                return []

            # Aggregate by author
            author_stats = defaultdict(lambda: {"video_count": 0, "total_views": 0, "total_likes": 0, "total_engagement": 0})

            for video in videos:
                username = video.get('author_username')
                if username:
                    author_stats[username]["video_count"] += 1
                    author_stats[username]["total_views"] += video.get('views_count', 0)
                    author_stats[username]["total_likes"] += video.get('likes_count', 0)
                    engagement = video.get('likes_count', 0) + video.get('comments_count', 0) + video.get('shares_count', 0)
                    author_stats[username]["total_engagement"] += engagement

            # Convert to list
            top_authors = []
            for username, stats in author_stats.items():
                top_authors.append({
                    "username": username,
                    "video_count": stats["video_count"],
                    "total_views": stats["total_views"],
                    "total_likes": stats["total_likes"],
                    "avg_views": round(stats["total_views"] / stats["video_count"], 2) if stats["video_count"] > 0 else 0
                })

            # Sort by metric
            if metric == "views":
                top_authors.sort(key=lambda x: x["total_views"], reverse=True)
            elif metric == "likes":
                top_authors.sort(key=lambda x: x["total_likes"], reverse=True)
            elif metric == "engagement":
                top_authors.sort(key=lambda x: author_stats[x["username"]]["total_engagement"], reverse=True)
            else:  # videos
                top_authors.sort(key=lambda x: x["video_count"], reverse=True)

            return top_authors[:limit]

        except Exception as e:
            logger.error(f"Error getting top authors: {e}")
            return []

    def get_top_hashtags(self, days: int = 30, limit: int = 20, keyword: str = None) -> List[Dict[str, Any]]:
        """
        Most used hashtags (JSONB aggregation)

        Args:
            days: Number of days to look back
            limit: Maximum hashtags to return
            keyword: Optional search keyword to filter by

        Returns:
            List of top hashtags with stats
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = self.supabase.table("videos").select("hashtags, views_count").gte("scraped_at", cutoff_date)
            
            if keyword:
                query = query.eq("search_keyword", keyword)
                
            videos_response = query.execute()
            videos = videos_response.data

            if not videos:
                return []

            # Aggregate hashtag usage
            hashtag_stats = defaultdict(lambda: {"video_count": 0, "total_views": 0})

            for video in videos:
                hashtags = video.get('hashtags', [])
                views = video.get('views_count', 0)

                if isinstance(hashtags, list):
                    for hashtag in hashtags:
                        hashtag_stats[hashtag]["video_count"] += 1
                        hashtag_stats[hashtag]["total_views"] += views

            # Convert to list
            top_hashtags = []
            for hashtag, stats in hashtag_stats.items():
                top_hashtags.append({
                    "hashtag": hashtag,
                    "video_count": stats["video_count"],
                    "total_views": stats["total_views"],
                    "avg_views": round(stats["total_views"] / stats["video_count"], 2) if stats["video_count"] > 0 else 0
                })

            # Sort by video count
            top_hashtags.sort(key=lambda x: x["video_count"], reverse=True)

            return top_hashtags[:limit]

        except Exception as e:
            logger.error(f"Error getting top hashtags: {e}")
            return []

    def get_keyword_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Performance metrics by search keyword

        Args:
            days: Number of days to look back

        Returns:
            List of keyword performance stats
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            videos_response = self.supabase.table("videos").select("id, search_keyword, views_count").gte("scraped_at", cutoff_date).execute()
            videos = videos_response.data

            if not videos:
                return []

            # Aggregate by keyword
            keyword_stats = defaultdict(lambda: {"video_count": 0, "total_views": 0, "video_ids": []})

            for video in videos:
                keyword = video.get('search_keyword')
                if keyword:
                    keyword_stats[keyword]["video_count"] += 1
                    keyword_stats[keyword]["total_views"] += video.get('views_count', 0)
                    keyword_stats[keyword]["video_ids"].append(video['id'])

            # Get sentiment for each keyword
            keywords_list = []
            for keyword, stats in keyword_stats.items():
                # Get sentiment for videos in this keyword
                video_ids = stats["video_ids"]
                if video_ids:
                    sentiment_response = self.supabase.table("sentiment_analysis").select("sentiment, sentiment_score").in_('video_id', video_ids).execute()
                    sentiments = sentiment_response.data

                    avg_sentiment = round(sum(s.get('sentiment_score', 0) for s in sentiments) / len(sentiments), 2) if sentiments else 0

                    sentiment_dist = defaultdict(int)
                    for s in sentiments:
                        sent_type = s.get('sentiment', 'Unknown')
                        sentiment_dist[sent_type] += 1
                else:
                    avg_sentiment = 0
                    sentiment_dist = {}

                keywords_list.append({
                    "keyword": keyword,
                    "video_count": stats["video_count"],
                    "total_views": stats["total_views"],
                    "avg_sentiment": avg_sentiment,
                    "sentiment_distribution": dict(sentiment_dist)
                })

            # Sort by video count
            keywords_list.sort(key=lambda x: x["video_count"], reverse=True)

            return keywords_list

        except Exception as e:
            logger.error(f"Error getting keyword performance: {e}")
            return []

    def get_sentiment_trends(self, days: int = 30, interval: str = "day") -> Dict[str, Any]:
        """
        Sentiment over time (time-series)

        Args:
            days: Number of days to look back
            interval: Grouping interval (day, week)

        Returns:
            Dictionary with time-series data
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get sentiments with video dates
            videos_response = self.supabase.table("videos").select("id, scraped_at").gte("scraped_at", cutoff_date).execute()
            videos_dict = {v['id']: v['scraped_at'] for v in videos_response.data}

            sentiment_response = self.supabase.table("sentiment_analysis").select("*").in_('video_id', list(videos_dict.keys())).execute()
            sentiments = sentiment_response.data

            # Group by time interval
            time_groups = defaultdict(lambda: {"scores": [], "sentiments": defaultdict(int), "count": 0})

            for sentiment in sentiments:
                video_id = sentiment.get('video_id')
                if video_id in videos_dict:
                    scraped_at = videos_dict[video_id]
                    date_obj = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))

                    if interval == "week":
                        # Group by week
                        week_start = date_obj - timedelta(days=date_obj.weekday())
                        time_key = week_start.strftime("%Y-%m-%d")
                    else:  # day
                        time_key = date_obj.strftime("%Y-%m-%d")

                    time_groups[time_key]["scores"].append(sentiment.get('sentiment_score', 0))
                    sent_type = sentiment.get('sentiment', 'Unknown')
                    time_groups[time_key]["sentiments"][sent_type] += 1
                    time_groups[time_key]["count"] += 1

            # Convert to list
            data_points = []
            for date, data in sorted(time_groups.items()):
                avg_score = round(sum(data["scores"]) / len(data["scores"]), 2) if data["scores"] else 0
                data_points.append({
                    "date": date,
                    "avg_score": avg_score,
                    "video_count": data["count"],
                    "sentiment_breakdown": dict(data["sentiments"])
                })

            return {
                "interval": interval,
                "data_points": data_points
            }

        except Exception as e:
            logger.error(f"Error getting sentiment trends: {e}")
            return {"interval": interval, "data_points": []}

    def get_engagement_stats(self, days: int = 7, group_by: str = None) -> Dict[str, Any]:
        """
        Engagement rate metrics

        Args:
            days: Number of days to look back
            group_by: Optional grouping (author, hashtag, keyword)

        Returns:
            Dictionary with engagement statistics
        """
        try:
            from datetime import datetime, timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            videos_response = self.supabase.table("videos").select("*").gte("scraped_at", cutoff_date).execute()
            videos = videos_response.data

            if not videos:
                return {}

            total_views = sum(v.get('views_count', 0) for v in videos)
            total_likes = sum(v.get('likes_count', 0) for v in videos)
            total_comments = sum(v.get('comments_count', 0) for v in videos)
            total_shares = sum(v.get('shares_count', 0) for v in videos)

            avg_engagement_rate = round((total_likes + total_comments + total_shares) / total_views, 4) if total_views > 0 else 0
            avg_like_rate = round(total_likes / total_views, 4) if total_views > 0 else 0
            avg_comment_rate = round(total_comments / total_views, 4) if total_views > 0 else 0
            avg_share_rate = round(total_shares / total_views, 4) if total_views > 0 else 0

            result = {
                "avg_engagement_rate": avg_engagement_rate,
                "avg_like_rate": avg_like_rate,
                "avg_comment_rate": avg_comment_rate,
                "avg_share_rate": avg_share_rate,
                "total_videos": len(videos),
                "period_days": days
            }

            # Add distribution if group_by is specified
            if group_by and group_by in ['author', 'keyword']:
                from collections import defaultdict

                group_stats = defaultdict(lambda: {"views": 0, "likes": 0, "comments": 0, "shares": 0})

                for video in videos:
                    if group_by == 'author':
                        key = video.get('author_username', 'Unknown')
                    else:  # keyword
                        key = video.get('search_keyword', 'Unknown')

                    group_stats[key]["views"] += video.get('views_count', 0)
                    group_stats[key]["likes"] += video.get('likes_count', 0)
                    group_stats[key]["comments"] += video.get('comments_count', 0)
                    group_stats[key]["shares"] += video.get('shares_count', 0)

                distribution = []
                for key, stats in group_stats.items():
                    views = stats["views"]
                    if views > 0:
                        eng_rate = round((stats["likes"] + stats["comments"] + stats["shares"]) / views, 4)
                    else:
                        eng_rate = 0

                    distribution.append({
                        group_by: key,
                        "engagement_rate": eng_rate,
                        "views": views
                    })

                result["distribution"] = sorted(distribution, key=lambda x: x["engagement_rate"], reverse=True)[:10]

            return result

        except Exception as e:
            logger.error(f"Error getting engagement stats: {e}")
            return {}

    def get_top_issues(self, days: int = 30, limit: int = 20, keyword: str = None) -> List[Dict[str, Any]]:
        """
        Top issues from sentiment key_issues (JSONB aggregation)

        Args:
            days: Number of days to look back
            limit: Maximum issues to return
            keyword: Optional search keyword to filter by

        Returns:
            List of top issues with stats
        """
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get videos in date range
            query = self.supabase.table("videos").select("id").gte("scraped_at", cutoff_date)
            if keyword:
                query = query.eq("search_keyword", keyword)
            
            videos_response = query.execute()
            video_ids = [v['id'] for v in videos_response.data]

            if not video_ids:
                return []

            # Get sentiment analyses
            sentiment_response = self.supabase.table("sentiment_analysis").select("video_id, key_issues, sentiment_score").in_('video_id', video_ids).execute()
            sentiments = sentiment_response.data

            # Aggregate issues
            issue_stats = defaultdict(lambda: {"mention_count": 0, "scores": [], "video_ids": []})

            for sentiment in sentiments:
                key_issues = sentiment.get('key_issues', [])
                score = sentiment.get('sentiment_score', 0)
                video_id = sentiment.get('video_id')

                if isinstance(key_issues, list):
                    for issue in key_issues:
                        # Extract title from issue object or use string directly
                        if isinstance(issue, dict):
                            issue_title = issue.get('title', str(issue))
                        else:
                            issue_title = str(issue)

                        issue_stats[issue_title]["mention_count"] += 1
                        issue_stats[issue_title]["scores"].append(score)
                        if video_id not in issue_stats[issue_title]["video_ids"]:
                            issue_stats[issue_title]["video_ids"].append(video_id)

            # Convert to list
            top_issues = []
            for issue, stats in issue_stats.items():
                avg_sentiment = round(sum(stats["scores"]) / len(stats["scores"]), 2) if stats["scores"] else 0

                # Determine trend based on average sentiment
                # Score > 6: up trend, 4-6: neutral, < 4: down trend
                if avg_sentiment > 6:
                    trend = "up"
                elif avg_sentiment < 4:
                    trend = "down"
                else:
                    trend = "neutral"

                top_issues.append({
                    "issue": issue,
                    "mention_count": stats["mention_count"],
                    "avg_sentiment": avg_sentiment,
                    "video_count": len(stats["video_ids"]),
                    "trend": trend
                })

            # Sort by mention count
            top_issues.sort(key=lambda x: x["mention_count"], reverse=True)

            return top_issues[:limit]

        except Exception as e:
            logger.error(f"Error getting top issues: {e}")
            return []

    # ============================================
    # Report & Navigation Operations
    # ============================================

    def get_unique_keywords(self) -> List[str]:
        """
        Get list of all unique search keywords (Reports)
        
        Returns:
            List of keyword strings
        """
        try:
            # Supabase doesn't support 'distinct' easily in python client directly on select
            # But we can select search_keyword and process in python for small datasets
            # OR use a stored procedure if available.
            # For Project S size, fetching all keywords and converting to set is fine.
            
            response = self.supabase.table("videos").select("search_keyword").execute()
            keywords = set(v.get("search_keyword") for v in response.data if v.get("search_keyword"))
            return sorted(list(keywords))
        except Exception as e:
            logger.error(f"Error getting unique keywords: {e}")
            return []

    # ============================================
    # Bulk Operations
    # ============================================

    def bulk_insert_videos(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk insert videos (for Apify workflow)

        Args:
            videos: List of video dictionaries

        Returns:
            Dictionary with insertion results
        """
        inserted = 0
        skipped = 0
        video_ids = []

        for video in videos:
            # Check if already exists
            existing = self.get_video_by_tiktok_id(video.get("tiktok_id"))
            if existing:
                skipped += 1
                video_ids.append(existing["id"])
            else:
                video_id = self.insert_video(video)
                if video_id:
                    inserted += 1
                    video_ids.append(video_id)

        return {
            "inserted": inserted,
            "skipped": skipped,
            "video_ids": video_ids
        }
