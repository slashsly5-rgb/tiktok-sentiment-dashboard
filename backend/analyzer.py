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
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found. Analysis will be skipped.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

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
        
        Please provide:
        1. Video Topic: What is this video mainly about? (Infer from description/hashtags)
        2. Key Discussion Points: What are the main things people are saying or debating in the comments?
        3. Overall Sentiment: (Positive, Negative, Neutral, Mixed)
        4. Sentiment Score: (1-10, where 10 is extremely positive)
        
        Format the output exactly as follows:
        Topic: [Topic]
        Discussion: [Key points]
        Sentiment: [Sentiment]
        Score: [Score]
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            content = response.choices[0].message.content
            
            # Simple parsing
            result = {}
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith("Topic:"): result['topic'] = line.replace("Topic:", "").strip()
                if line.startswith("Discussion:"): result['discussion'] = line.replace("Discussion:", "").strip()
                if line.startswith("Sentiment:"): result['sentiment'] = line.replace("Sentiment:", "").strip()
                if line.startswith("Score:"): 
                    score_str = line.replace("Score:", "").strip()
                    # Extract just the number
                    import re
                    match = re.search(r'\d+', score_str)
                    if match:
                        result['score'] = match.group(0)
                    else:
                        result['score'] = "5" # Default to neutral if confusing
            
            # Match key_issues to discussion if matched
            if 'discussion' in result and result['discussion'] != "N/A":
                 # Split by newlines or commas if multiple points exist
                 points = [p.strip('- ').strip() for p in result['discussion'].split('\n') if p.strip()]
                 if len(points) == 1 and ',' in points[0]:
                     points = [p.strip() for p in points[0].split(',')]
                 result['key_issues'] = points
            else:
                 result['key_issues'] = []

            return result
        except Exception as e:
            print(f"Error analyzing video: {e}")
            return {"topic": "Error", "discussion": "Error", "sentiment": "Error", "score": "0", "key_issues": []}


def analyze_from_database(video_id: str, db_client: SupabaseClient) -> Optional[Dict[str, Any]]:
    """
    Analyze a video already in database

    Args:
        video_id: Video UUID
        db_client: Database client instance

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
        analyzer = Analyzer()
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


def batch_analyze_unanalyzed(db_client: SupabaseClient, limit: int = 10) -> Dict[str, Any]:
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
                analysis = analyze_from_database(video_id, db_client)
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
