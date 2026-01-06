"""
Flask API for TikTok Political Sentiment Scraper
Provides HTTP endpoints for n8n workflow orchestration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import uuid
import asyncio
import sys
import re
from datetime import datetime
from typing import Dict, Any
import logging

from config import Config
from database import SupabaseClient
from scraper import scrape_and_save
from analyzer import Analyzer
from mistral_chat import MistralChatService
from transform import (
    transform_video,
    transform_videos,
    transform_comment,
    transform_comments,
    transform_sentiment,
    transform_sentiments,
    transform_complete_video_view,
    transform_dashboard_analytics,
    transform_sentiment_overview,
    transform_keys_to_camel,
    transform_pagination_response
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Job storage (in-memory for MVP)
jobs = {}

# Database client
try:
    db = SupabaseClient()
    logger.info("Database client initialized")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    db = None

# Mistral chat service
try:
    if db:
        chat_service = MistralChatService(db)
        logger.info("Mistral chat service initialized")
    else:
        chat_service = None
        logger.warning("Chat service disabled - database not available")
except Exception as e:
    logger.error(f"Failed to initialize chat service: {e}")
    chat_service = None


# ============================================
# Helper Functions
# ============================================

# UUID validation regex
UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)

def is_valid_uuid(uuid_str):
    """Validate UUID format"""
    if not uuid_str:
        return False
    return bool(UUID_REGEX.match(str(uuid_str)))


def paginated_response(data, total, offset=0, limit=50, data_key="items"):
    """
    Create a consistent paginated response

    Args:
        data: List of items for current page
        total: Total number of items available
        offset: Current offset
        limit: Items per page
        data_key: Key name for the data array in response

    Returns:
        Flask JSON response with pagination metadata
    """
    return jsonify({
        "count": len(data),
        "total": total,
        "offset": offset,
        "limit": limit,
        data_key: data
    })


def run_async_in_thread(coro):
    """Run async coroutine in a new thread"""
    def run():
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    thread = threading.Thread(target=run)
    thread.start()
    return thread


async def scrape_job(job_id: str, keywords: list, max_videos: int, analyze: bool):
    """Background scraping job"""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()

        results = []
        all_video_ids = []

        # Scrape each keyword
        for keyword in keywords:
            logger.info(f"Job {job_id}: Scraping keyword '{keyword}'")
            result = await scrape_and_save(keyword, max_videos, db)
            results.append(result)
            all_video_ids.extend(result.get("video_ids", []))

            jobs[job_id]["progress"] = {
                "keywords_processed": len(results),
                "total_keywords": len(keywords),
                "videos_scraped": sum(r.get("scraped", 0) for r in results)
            }

        # Analyze if requested
        if analyze and all_video_ids:
            logger.info(f"Job {job_id}: Analyzing {len(all_video_ids)} videos")
            jobs[job_id]["status"] = "analyzing"

            analyzer = Analyzer()
            analyzed_count = 0

            for video_id in all_video_ids:
                try:
                    video = db.get_video_with_comments(video_id)
                    if video:
                        comments = [c["comment_text"] for c in video.get("comments", [])]
                        analysis = analyzer.analyze_video(
                            comments,
                            video.get("description", ""),
                            video.get("hashtags", [])
                        )
                        db.insert_sentiment(video_id, analysis)
                        analyzed_count += 1
                except Exception as e:
                    logger.error(f"Error analyzing video {video_id}: {e}")

            jobs[job_id]["analyzed_count"] = analyzed_count

        # Mark as completed
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["results"] = {
            "total_scraped": sum(r.get("scraped", 0) for r in results),
            "total_skipped": sum(r.get("skipped", 0) for r in results),
            "video_ids": all_video_ids,
            "keyword_results": results
        }

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


async def analyze_job(job_id: str, video_ids: list = None):
    """Background analysis job"""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()

        # Get videos to analyze
        if video_ids:
            videos_to_analyze = video_ids
        else:
            unanalyzed = db.get_unanalyzed_videos(limit=Config.ANALYSIS_BATCH_SIZE)
            videos_to_analyze = [v["id"] for v in unanalyzed]

        if not videos_to_analyze:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["results"] = {"analyzed_count": 0, "message": "No videos to analyze"}
            return

        analyzer = Analyzer()
        analyzed_count = 0
        failed_count = 0

        for i, video_id in enumerate(videos_to_analyze):
            try:
                video = db.get_video_with_comments(video_id)
                if video:
                    comments = [c["comment_text"] for c in video.get("comments", [])]
                    analysis = analyzer.analyze_video(
                        comments,
                        video.get("description", ""),
                        video.get("hashtags", [])
                    )
                    db.insert_sentiment(video_id, analysis)
                    analyzed_count += 1

                    jobs[job_id]["progress"] = {
                        "analyzed": analyzed_count,
                        "total": len(videos_to_analyze),
                        "failed": failed_count
                    }
            except Exception as e:
                logger.error(f"Error analyzing video {video_id}: {e}")
                failed_count += 1

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["results"] = {
            "analyzed_count": analyzed_count,
            "failed_count": failed_count,
            "total": len(videos_to_analyze)
        }

        logger.info(f"Analysis job {job_id} completed: {analyzed_count} analyzed, {failed_count} failed")

    except Exception as e:
        logger.error(f"Analysis job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


# ============================================
# API Endpoints
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database_connected": db is not None,
        "config": Config.get_summary()
    })


@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Trigger scraping job

    Body:
        {
            "keywords": ["keyword1", "keyword2"],
            "max_videos_per_keyword": 5,
            "analyze": true
        }
    """
    try:
        data = request.json

        keywords = data.get("keywords", [])
        max_videos = data.get("max_videos_per_keyword", Config.SCRAPER_MAX_VIDEOS)
        analyze = data.get("analyze", False)

        if not keywords:
            return jsonify({"error": "Keywords are required"}), 400

        if not db:
            return jsonify({"error": "Database not available"}), 500

        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "id": job_id,
            "type": "scrape",
            "status": "pending",
            "keywords": keywords,
            "max_videos": max_videos,
            "analyze": analyze,
            "created_at": datetime.now().isoformat(),
            "progress": {}
        }

        # Start job in background
        run_async_in_thread(scrape_job(job_id, keywords, max_videos, analyze))

        logger.info(f"Started scrape job {job_id} for keywords: {keywords}")

        return jsonify({
            "job_id": job_id,
            "status": "started",
            "keywords": keywords
        }), 202

    except Exception as e:
        logger.error(f"Error starting scrape job: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/scrape/status/<job_id>', methods=['GET'])
def scrape_status(job_id):
    """Get job status and progress"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(jobs[job_id])


@app.route('/videos', methods=['GET'])
def get_videos():
    """
    Get recent videos from database

    Query params:
        - limit: int (default 50)
        - days: int (default 30, use 0 for all videos)
        - keyword: str (optional)
        - include_sentiment: bool (default false) - include sentiment analysis data
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 30, type=int)
        keyword = request.args.get('keyword', None)
        include_sentiment = request.args.get('include_sentiment', 'false').lower() == 'true'

        logger.info(f"Fetching videos: limit={limit}, days={days}, keyword={keyword}, include_sentiment={include_sentiment}")

        if not db:
            logger.error("Database client not available")
            return jsonify({"error": "Database not available"}), 500

        videos = db.get_recent_videos(days=days, keyword=keyword, limit=limit, include_sentiment=include_sentiment)
        logger.info(f"Retrieved {len(videos)} videos from database")

        # Transform to camelCase for frontend
        transformed_videos = transform_videos(videos)

        return jsonify({
            "count": len(transformed_videos),
            "videos": transformed_videos
        })

    except Exception as e:
        logger.error(f"Error fetching videos: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/sentiment/overview', methods=['GET'])
def sentiment_overview():
    """
    Get sentiment statistics

    Query params:
        - days: int (default 30, use 0 for all time)
    """
    try:
        days = request.args.get('days', 30, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        overview = db.get_sentiment_overview(days=days)

        # Transform to camelCase for frontend
        transformed_overview = transform_sentiment_overview(overview)

        return jsonify(transformed_overview)

    except Exception as e:
        logger.error(f"Error fetching sentiment overview: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Trigger analysis for specific video IDs or all unanalyzed

    Body:
        {
            "video_ids": ["uuid1", "uuid2"],  // optional
            "analyze_all_unanalyzed": true    // if video_ids not provided
        }
    """
    try:
        data = request.json or {}

        video_ids = data.get("video_ids")
        analyze_all = data.get("analyze_all_unanalyzed", False)

        if not video_ids and not analyze_all:
            return jsonify({"error": "Provide video_ids or set analyze_all_unanalyzed to true"}), 400

        if not db:
            return jsonify({"error": "Database not available"}), 500

        # Create analysis job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "id": job_id,
            "type": "analyze",
            "status": "pending",
            "video_ids": video_ids,
            "analyze_all": analyze_all,
            "created_at": datetime.now().isoformat(),
            "progress": {}
        }

        # Start job in background
        run_async_in_thread(analyze_job(job_id, video_ids))

        logger.info(f"Started analysis job {job_id}")

        return jsonify({
            "job_id": job_id,
            "status": "started"
        }), 202

    except Exception as e:
        logger.error(f"Error starting analysis job: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/bulk', methods=['POST'])
def bulk_insert_videos():
    """
    Bulk insert videos (for Apify workflow)

    Body: [
        {
            "tiktok_id": "123",
            "url": "https://...",
            "author_username": "user",
            "description": "...",
            "views_count": 1000,
            ...
        }
    ]
    """
    try:
        videos = request.json

        if not isinstance(videos, list):
            return jsonify({"error": "Body must be an array of video objects"}), 400

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.bulk_insert_videos(videos)

        logger.info(f"Bulk insert: {result['inserted']} inserted, {result['skipped']} skipped")

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error bulk inserting videos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    return jsonify({
        "count": len(jobs),
        "jobs": list(jobs.values())
    })


# ============================================
# Individual Resource Retrieval Endpoints
# ============================================

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video_by_id(video_id):
    """
    Get single video by UUID with optional includes

    Query params:
        - include_comments: bool (default false)
        - include_sentiment: bool (default false)
    """
    try:
        if not is_valid_uuid(video_id):
            return jsonify({"error": "Invalid video ID format"}), 400

        include_comments = request.args.get('include_comments', 'false').lower() == 'true'
        include_sentiment = request.args.get('include_sentiment', 'false').lower() == 'true'

        if not db:
            return jsonify({"error": "Database not available"}), 500

        video = db.get_video_by_id(video_id, include_comments, include_sentiment)

        if not video:
            return jsonify({"error": "Video not found"}), 404

        # Transform to camelCase for frontend
        transformed_video = transform_video(video)

        return jsonify({"video": transformed_video})

    except Exception as e:
        logger.error(f"Error fetching video: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/tiktok/<tiktok_id>', methods=['GET'])
def get_video_by_tiktok_id_endpoint(tiktok_id):
    """
    Get video by TikTok ID (public ID, not UUID)

    Query params:
        - include_comments: bool (default false)
        - include_sentiment: bool (default false)
    """
    try:
        if not db:
            return jsonify({"error": "Database not available"}), 500

        # First get by tiktok_id
        video = db.get_video_by_tiktok_id(tiktok_id)

        if not video:
            return jsonify({"error": "Video not found"}), 404

        # Check if includes are requested
        include_comments = request.args.get('include_comments', 'false').lower() == 'true'
        include_sentiment = request.args.get('include_sentiment', 'false').lower() == 'true'

        if include_comments or include_sentiment:
            # Re-fetch with includes
            video = db.get_video_by_id(video['id'], include_comments, include_sentiment)

        # Transform to camelCase for frontend
        transformed_video = transform_video(video)

        return jsonify({"video": transformed_video})

    except Exception as e:
        logger.error(f"Error fetching video by TikTok ID: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/sentiment/<video_id>', methods=['GET'])
def get_sentiment_endpoint(video_id):
    """
    Get sentiment analysis for specific video

    Query params:
        - include_video: bool (default false)
    """
    try:
        if not is_valid_uuid(video_id):
            return jsonify({"error": "Invalid video ID format"}), 400

        include_video = request.args.get('include_video', 'false').lower() == 'true'

        if not db:
            return jsonify({"error": "Database not available"}), 500

        sentiment = db.get_sentiment_by_video_id(video_id, include_video)

        if not sentiment:
            return jsonify({"error": "Sentiment analysis not found for this video"}), 404

        # Transform to camelCase for frontend
        transformed_sentiment = transform_sentiment(sentiment)

        return jsonify({"sentiment": transformed_sentiment})

    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<video_id>/complete', methods=['GET'])
def get_complete_video(video_id):
    """
    Get complete view: video + all comments + sentiment in one request
    """
    try:
        if not is_valid_uuid(video_id):
            return jsonify({"error": "Invalid video ID format"}), 400

        if not db:
            return jsonify({"error": "Database not available"}), 500

        complete_view = db.get_complete_video_view(video_id)

        if not complete_view:
            return jsonify({"error": "Video not found"}), 404

        # Transform to camelCase for frontend
        transformed_view = transform_complete_video_view(complete_view)

        return jsonify(transformed_view)

    except Exception as e:
        logger.error(f"Error fetching complete video view: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================
# Comments API Endpoints
# ============================================

@app.route('/api/comments', methods=['GET'])
def get_comments_list():
    """
    Get all comments with pagination and filtering

    Query params:
        - limit: int (default 100, max 1000)
        - offset: int (default 0)
        - video_id: str (optional UUID filter)
        - author_username: str (optional string filter)
        - min_likes: int (optional minimum likes)
        - days: int (optional - last N days)
    """
    try:
        limit = min(request.args.get('limit', 100, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)

        filters = {}
        if request.args.get('video_id'):
            video_id = request.args.get('video_id')
            if not is_valid_uuid(video_id):
                return jsonify({"error": "Invalid video_id format"}), 400
            filters['video_id'] = video_id

        if request.args.get('author_username'):
            filters['author_username'] = request.args.get('author_username')

        if request.args.get('min_likes'):
            filters['min_likes'] = request.args.get('min_likes', type=int)

        if request.args.get('days'):
            filters['days'] = request.args.get('days', type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.get_comments(filters, limit, offset)

        # Transform to camelCase for frontend
        transformed_comments = transform_comments(result["data"])

        return jsonify({
            "count": len(transformed_comments),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "comments": transformed_comments
        })

    except Exception as e:
        logger.error(f"Error fetching comments: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/comments/<comment_id>', methods=['GET'])
def get_comment(comment_id):
    """
    Get single comment by UUID
    """
    try:
        if not is_valid_uuid(comment_id):
            return jsonify({"error": "Invalid comment ID format"}), 400

        if not db:
            return jsonify({"error": "Database not available"}), 500

        comment = db.get_comment_by_id(comment_id)

        if not comment:
            return jsonify({"error": "Comment not found"}), 404

        # Transform to camelCase for frontend
        transformed_comment = transform_comment(comment)

        return jsonify({"comment": transformed_comment})

    except Exception as e:
        logger.error(f"Error fetching comment: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/<video_id>/comments', methods=['GET'])
def get_video_comments(video_id):
    """
    Get all comments for a specific video

    Query params:
        - limit: int (default 100)
        - offset: int (default 0)
        - min_likes: int (optional)
    """
    try:
        if not is_valid_uuid(video_id):
            return jsonify({"error": "Invalid video ID format"}), 400

        limit = min(request.args.get('limit', 100, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)
        min_likes = request.args.get('min_likes', type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.get_comments_for_video(video_id, limit, offset, min_likes)

        # Transform to camelCase for frontend
        transformed_comments = transform_comments(result["data"])

        return jsonify({
            "videoId": video_id,
            "count": len(transformed_comments),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "comments": transformed_comments
        })

    except Exception as e:
        logger.error(f"Error fetching video comments: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/comments/stats', methods=['GET'])
def get_comment_stats():
    """
    Get comment statistics

    Query params:
        - days: int (default 7)
        - video_id: str (optional UUID)
    """
    try:
        days = request.args.get('days', 7, type=int)
        video_id = request.args.get('video_id')

        if video_id and not is_valid_uuid(video_id):
            return jsonify({"error": "Invalid video_id format"}), 400

        if not db:
            return jsonify({"error": "Database not available"}), 500

        stats = db.get_comment_statistics(days, video_id)

        # Transform to camelCase for frontend
        transformed_stats = transform_keys_to_camel(stats)

        return jsonify(transformed_stats)

    except Exception as e:
        logger.error(f"Error fetching comment stats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/comments/top-commenters', methods=['GET'])
def get_top_commenters_endpoint():
    """
    Get most active commenters

    Query params:
        - days: int (default 30)
        - limit: int (default 10)
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        top_commenters = db.get_top_commenters(days, limit)

        # Transform to camelCase for frontend
        transformed_commenters = transform_keys_to_camel(top_commenters)

        return jsonify({
            "periodDays": days,
            "count": len(transformed_commenters),
            "topCommenters": transformed_commenters
        })

    except Exception as e:
        logger.error(f"Error fetching top commenters: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================
# Analytics Endpoints
# ============================================

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics_endpoint():
    """
    Comprehensive dashboard data in one call

    Query params:
        - days: int (default 7)
    """
    try:
        days = request.args.get('days', 7, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        analytics = db.get_dashboard_analytics(days)

        # Transform to camelCase for frontend
        transformed_analytics = transform_dashboard_analytics(analytics)

        return jsonify(transformed_analytics)

    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/top-authors', methods=['GET'])
def get_top_authors_analytics_endpoint():
    """
    Top content creators by metric

    Query params:
        - days: int (default 30)
        - limit: int (default 10)
        - metric: str (videos, views, likes, engagement - default videos)
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        metric = request.args.get('metric', 'videos')

        if not db:
            return jsonify({"error": "Database not available"}), 500

        top_authors = db.get_top_authors(days, limit, metric)

        # Transform to camelCase for frontend
        transformed_authors = transform_keys_to_camel(top_authors)

        return jsonify({
            "periodDays": days,
            "metric": metric,
            "count": len(transformed_authors),
            "topAuthors": transformed_authors
        })

    except Exception as e:
        logger.error(f"Error fetching top authors: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/top-hashtags', methods=['GET'])
def get_top_hashtags_analytics_endpoint():
    """
    Most used hashtags

    Query params:
        - days: int (default 30)
        - limit: int (default 20)
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 20, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        top_hashtags = db.get_top_hashtags(days, limit)

        # Transform to camelCase for frontend
        transformed_hashtags = transform_keys_to_camel(top_hashtags)

        return jsonify({
            "periodDays": days,
            "count": len(transformed_hashtags),
            "topHashtags": transformed_hashtags
        })

    except Exception as e:
        logger.error(f"Error fetching top hashtags: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/keyword-performance', methods=['GET'])
def get_keyword_performance_endpoint():
    """
    Performance metrics by search keyword

    Query params:
        - days: int (default 30)
    """
    try:
        days = request.args.get('days', 30, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        keywords = db.get_keyword_performance(days)

        # Transform to camelCase for frontend
        transformed_keywords = transform_keys_to_camel(keywords)

        return jsonify({
            "periodDays": days,
            "count": len(transformed_keywords),
            "keywords": transformed_keywords
        })

    except Exception as e:
        logger.error(f"Error fetching keyword performance: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/sentiment-trends', methods=['GET'])
def get_sentiment_trends_endpoint():
    """
    Sentiment over time (time-series)

    Query params:
        - days: int (default 30)
        - interval: str (day, week - default day)
    """
    try:
        days = request.args.get('days', 30, type=int)
        interval = request.args.get('interval', 'day')

        if not db:
            return jsonify({"error": "Database not available"}), 500

        trends = db.get_sentiment_trends(days, interval)

        # Transform to camelCase for frontend
        transformed_trends = transform_keys_to_camel(trends)

        return jsonify(transformed_trends)

    except Exception as e:
        logger.error(f"Error fetching sentiment trends: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/engagement-stats', methods=['GET'])
def get_engagement_stats_endpoint():
    """
    Engagement rate metrics

    Query params:
        - days: int (default 7)
        - group_by: str (optional: author, keyword)
    """
    try:
        days = request.args.get('days', 7, type=int)
        group_by = request.args.get('group_by')

        if not db:
            return jsonify({"error": "Database not available"}), 500

        stats = db.get_engagement_stats(days, group_by)

        # Transform to camelCase for frontend
        transformed_stats = transform_keys_to_camel(stats)

        return jsonify(transformed_stats)

    except Exception as e:
        logger.error(f"Error fetching engagement stats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/top-issues', methods=['GET'])
def get_top_issues_endpoint():
    """
    Most discussed issues from sentiment key_issues

    Query params:
        - days: int (default 30)
        - limit: int (default 20)
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 20, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        top_issues = db.get_top_issues(days, limit)

        # Transform to camelCase for frontend
        transformed_issues = transform_keys_to_camel(top_issues)

        return jsonify({
            "periodDays": days,
            "count": len(transformed_issues),
            "topIssues": transformed_issues
        })

    except Exception as e:
        logger.error(f"Error fetching top issues: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================
# Advanced Filtering & Search Endpoints
# ============================================

@app.route('/api/videos/search', methods=['GET'])
def search_videos_endpoint():
    """
    Advanced multi-criteria video search

    Query params:
        - keyword: str (search in description, search_keyword)
        - author_username: str
        - hashtag: str
        - min_views, max_views, min_likes, min_comments, min_shares: int
        - date_from, date_to: str (ISO format)
        - sort_by: str (default scraped_at)
        - sort_order: str (asc/desc, default desc)
        - limit: int (default 50)
        - offset: int (default 0)
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)

        filters = {}
        for key in ['keyword', 'author_username', 'hashtag', 'date_from', 'date_to', 'sort_by', 'sort_order']:
            if request.args.get(key):
                filters[key] = request.args.get(key)

        for key in ['min_views', 'max_views', 'min_likes', 'min_comments', 'min_shares']:
            if request.args.get(key):
                filters[key] = request.args.get(key, type=int)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.search_videos(filters, limit, offset)

        # Transform to camelCase for frontend
        transformed_videos = transform_videos(result["data"])

        return jsonify({
            "count": len(transformed_videos),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "filtersApplied": filters,
            "videos": transformed_videos
        })

    except Exception as e:
        logger.error(f"Error searching videos: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/by-author/<username>', methods=['GET'])
def get_videos_by_author_endpoint(username):
    """
    Get all videos by specific author with stats

    Query params:
        - limit: int (default 50)
        - offset: int (default 0)
        - sort_by: str (default scraped_at)
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)
        sort_by = request.args.get('sort_by', 'scraped_at')

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.get_videos_by_author(username, limit, offset, sort_by)

        # Transform to camelCase for frontend
        transformed_videos = transform_videos(result["data"])
        transformed_stats = transform_keys_to_camel(result["stats"])

        return jsonify({
            "authorUsername": username,
            "count": len(transformed_videos),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "stats": transformed_stats,
            "videos": transformed_videos
        })

    except Exception as e:
        logger.error(f"Error fetching videos by author: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/by-hashtag/<hashtag>', methods=['GET'])
def get_videos_by_hashtag_endpoint(hashtag):
    """
    Get videos with specific hashtag

    Query params:
        - limit: int (default 50)
        - offset: int (default 0)
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.get_videos_by_hashtag(hashtag, limit, offset)

        # Transform to camelCase for frontend
        transformed_videos = transform_videos(result["data"])

        return jsonify({
            "hashtag": hashtag if hashtag.startswith('#') else f"#{hashtag}",
            "count": len(transformed_videos),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "videos": transformed_videos
        })

    except Exception as e:
        logger.error(f"Error fetching videos by hashtag: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/videos/trending', methods=['GET'])
def get_trending_videos_endpoint():
    """
    Get trending videos by engagement rate

    Query params:
        - days: int (default 7)
        - limit: int (default 20)
        - metric: str (views, likes, engagement_rate - default views)
    """
    try:
        days = request.args.get('days', 7, type=int)
        limit = min(request.args.get('limit', 20, type=int), Config.MAX_LIMIT)
        metric = request.args.get('metric', 'views')

        if not db:
            return jsonify({"error": "Database not available"}), 500

        trending_videos = db.get_trending_videos(days, limit, metric)

        # Transform to camelCase for frontend
        transformed_videos = transform_videos(trending_videos)

        return jsonify({
            "periodDays": days,
            "metric": metric,
            "count": len(transformed_videos),
            "trendingVideos": transformed_videos
        })

    except Exception as e:
        logger.error(f"Error fetching trending videos: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/sentiment/by-type/<sentiment_type>', methods=['GET'])
def get_sentiment_by_type_endpoint(sentiment_type):
    """
    Filter sentiment analyses by type

    Path params:
        - sentiment_type: positive, negative, neutral, mixed

    Query params:
        - limit: int (default 50)
        - offset: int (default 0)
        - include_videos: bool (default false)
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)
        include_videos = request.args.get('include_videos', 'false').lower() == 'true'

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.get_analyses_by_sentiment(sentiment_type, limit, offset, include_videos)

        # Transform to camelCase for frontend
        transformed_analyses = transform_sentiments(result["data"])

        return jsonify({
            "sentimentType": sentiment_type,
            "count": len(transformed_analyses),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "analyses": transformed_analyses
        })

    except Exception as e:
        logger.error(f"Error fetching sentiment by type: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/sentiment/by-score', methods=['GET'])
def get_sentiment_by_score_endpoint():
    """
    Filter sentiment by score range

    Query params:
        - min_score: float (1-10)
        - max_score: float (1-10)
        - limit: int (default 50)
        - offset: int (default 0)
    """
    try:
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        limit = min(request.args.get('limit', 50, type=int), Config.MAX_LIMIT)
        offset = max(request.args.get('offset', 0, type=int), 0)

        if not db:
            return jsonify({"error": "Database not available"}), 500

        result = db.get_analyses_by_score_range(min_score, max_score, limit, offset)

        # Transform to camelCase for frontend
        transformed_analyses = transform_sentiments(result["data"])

        return jsonify({
            "scoreRange": f"{min_score or 1}-{max_score or 10}",
            "count": len(transformed_analyses),
            "total": result["total"],
            "offset": offset,
            "limit": limit,
            "analyses": transformed_analyses
        })

    except Exception as e:
        logger.error(f"Error fetching sentiment by score: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================
# Chat AI Assistant Endpoints
# ============================================

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    Send message to AI chat assistant with optional data context

    Body:
        {
            "session_id": "uuid-string",  // Required
            "message": "User question",    // Required
            "filters": {                   // Optional
                "days": 30,
                "keywords": ["keyword1"],
                "sentiment": "positive"
            }
        }

    Returns:
        {
            "response": "AI response",
            "session_id": "uuid-string",
            "message_count": 5,
            "context_used": true
        }
    """
    try:
        if not chat_service:
            return jsonify({"error": "Chat service not available"}), 503

        data = request.json

        if not data:
            return jsonify({"error": "Request body required"}), 400

        session_id = data.get("session_id")
        message = data.get("message")
        filters = data.get("filters")

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400

        if not message or not message.strip():
            return jsonify({"error": "message is required and cannot be empty"}), 400

        # Validate filters if provided
        if filters and not isinstance(filters, dict):
            return jsonify({"error": "filters must be an object"}), 400

        logger.info(f"Chat request - session: {session_id}, message length: {len(message)}, filters: {filters}")

        # Call chat service
        result = chat_service.chat(session_id, message, filters)

        # Check for errors
        if "error" in result:
            status_code = 503 if result["error"] == "service_unavailable" else 500
            return jsonify(result), status_code

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history_endpoint(session_id):
    """
    Get conversation history for a session

    Returns:
        {
            "session_id": "uuid",
            "history": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "message_count": 10
        }
    """
    try:
        if not chat_service:
            return jsonify({"error": "Chat service not available"}), 503

        history = chat_service.get_conversation_history(session_id)

        return jsonify({
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        })

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/clear/<session_id>', methods=['DELETE'])
def clear_chat_endpoint(session_id):
    """
    Clear conversation history for a session

    Returns:
        {"success": true}
    """
    try:
        if not chat_service:
            return jsonify({"error": "Chat service not available"}), 503

        success = chat_service.clear_session(session_id)

        return jsonify({
            "success": success,
            "message": "Session cleared" if success else "Session not found"
        })

    except Exception as e:
        logger.error(f"Error clearing chat: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================
# Main
# ============================================

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)

    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.API_DEBUG
    )
