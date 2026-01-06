import os
from openai import OpenAI
from typing import Dict, Any, List, Optional
from database import SupabaseClient
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.org_id = "org-Ac4M8r2L9ygbPiJVGyZ2fKaF" # Forces "Aidju Digital" org
        
        # DEBUG: Trace where the key came from
        if self.api_key:
            suffix = self.api_key[-5:] if len(self.api_key) > 5 else "SHORT"
            source = "EXPLICIT" if api_key else "ENV_FALLBACK"
            logger.info(f"DEBUG: Analyzer initialized with key ...{suffix} from {source}")
        else:
            logger.warning("DEBUG: Analyzer initialized with NO KEY")

        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found. Analysis will be skipped.")
            self.client = None
        else:
            # Explicitly pass organization ID to ensure credits are used
            self.client = OpenAI(api_key=self.api_key, organization=self.org_id)

    def analyze_video(self, comments, description, hashtags):
        if not self.client:
            return {"summary": "N/A", "sentiment": "N/A", "topic": "N/A", "discussion_points": "N/A"}

        comments_text = "\n".join(comments) if comments else "No comments available."
        hashtags_text = ", ".join(hashtags) if hashtags else "No hashtags."
        
        prompt = f"""
        Analyze this TikTok video based on the following data:
        
        Description: {description}
        Hashtags: {hashtags_text}
        User Comments:
        {comments_text}
        
        Return a JSON object with exactly these fields:
        {{
            "topic": "Short summary of the video topic",
            "discussion_points": ["Point 1", "Point 2", "Point 3"],
            "sentiment": "Positive, Negative, Neutral, or Mixed",
            "score": 1-10 (integer)
        }}
        """

        try:
            import json
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106", # Supports JSON mode
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=350
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            
            return {
                "topic": data.get("topic", "N/A"),
                "discussion": "; ".join(data.get("discussion_points", [])), # String for DB 'discussion' text
                "key_issues": data.get("discussion_points", []), # List for UI
                "sentiment": data.get("sentiment", "Neutral"),
                "score": str(data.get("score", 5))
            }

        except Exception as e:
            print(f"Error analyzing video: {e}")
            return {
                "topic": "Analysis Error", 
                "discussion": str(e), 
                "sentiment": "Error", 
                "score": "0", 
                "key_issues": []
            }


def analyze_from_database(video_id: str, db_client: SupabaseClient, openai_api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a video already in database

    Args:
        video_id: Video UUID
        db_client: Database client instance
        openai_api_key: Optional explicit API key

    Returns:
        Analysis result dictionary if successful, None otherwise
    """
    try:
        # Fetch video with comments from database
        video = db_client.get_video_with_comments(video_id)
        if not video:
            logger.error(f"Video {video_id} not found in database")
            return None

        # Extract data for analysis
        comments = [c["comment_text"] for c in video.get("comments", [])]
        description = video.get("description", "")
        hashtags = video.get("hashtags", [])

        # Run analysis
        analyzer = Analyzer(api_key=openai_api_key)
        analysis = analyzer.analyze_video(comments, description, hashtags)

        # Save sentiment to database
        success = db_client.insert_sentiment(video_id, analysis)

        if success:
            logger.info(f"Successfully analyzed and saved sentiment for video {video_id}")
            return analysis
        else:
            logger.error(f"Failed to save sentiment for video {video_id}")
            return None

    except Exception as e:
        logger.error(f"Error analyzing video {video_id} from database: {e}")
        return None


def batch_analyze_unanalyzed(db_client: SupabaseClient, limit: int = 10, openai_api_key: str = None) -> Dict[str, Any]:
    """
    Analyze videos without sentiment data

    Args:
        db_client: Database client instance
        limit: Maximum number of videos to analyze

    Returns:
        Dictionary with analysis results
    """
    try:
        # Query unanalyzed videos
        unanalyzed = db_client.get_unanalyzed_videos(limit=limit)

        if not unanalyzed:
            logger.info("No unanalyzed videos found")
            return {
                "total": 0,
                "analyzed": 0,
                "failed": 0,
                "results": []
            }

        logger.info(f"Found {len(unanalyzed)} unanalyzed videos")

        analyzed_count = 0
        failed_count = 0
        results = []

        for video in unanalyzed:
            video_id = video["id"]
            try:
                analysis = analyze_from_database(video_id, db_client, openai_api_key=openai_api_key)
                if analysis:
                    analyzed_count += 1
                    results.append({
                        "video_id": video_id,
                        "status": "success",
                        "analysis": analysis
                    })
                else:
                    failed_count += 1
                    results.append({
                        "video_id": video_id,
                        "status": "failed",
                        "error": "Analysis returned None"
                    })
            except Exception as e:
                failed_count += 1
                logger.error(f"Error analyzing video {video_id}: {e}")
                results.append({
                    "video_id": video_id,
                    "status": "failed",
                    "error": str(e)
                })

        logger.info(f"Batch analysis complete: {analyzed_count} analyzed, {failed_count} failed")

        return {
            "total": len(unanalyzed),
            "analyzed": analyzed_count,
            "failed": failed_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return {
            "total": 0,
            "analyzed": 0,
            "failed": 0,
            "error": str(e),
            "results": []
        }
