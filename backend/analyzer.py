import os
from typing import Dict, Any, List, Optional
from database import SupabaseClient
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self, api_key=None, provider="mistral"):
        """
        Initialize Analyzer with either Mistral or OpenAI, with automatic fallback.

        Args:
            api_key: Optional explicit API key
            provider: "mistral" (default) or "openai"

        Fallback order: Mistral -> OpenAI
        """
        self.provider = provider.lower()
        self.client = None
        self.fallback_client = None  # For automatic fallback
        self.fallback_provider = None

        if self.provider == "mistral":
            # Use Mistral AI as primary
            from mistralai import Mistral
            from config import Config

            self.api_key = api_key or Config.MISTRAL_API_KEY or os.getenv("MISTRAL_API_KEY")
            self.model = Config.MISTRAL_MODEL

            if self.api_key:
                suffix = self.api_key[-5:] if len(self.api_key) > 5 else "SHORT"
                logger.info(f"Analyzer initialized with Mistral AI (key: ...{suffix})")
                print(f"       LLM Primary: Mistral (key: ...{suffix})")
                self.client = Mistral(api_key=self.api_key)

                # Setup OpenAI as fallback
                self._setup_openai_fallback(Config)
            else:
                logger.warning("MISTRAL_API_KEY not found. Trying OpenAI fallback...")
                print("       [!] MISTRAL_API_KEY not found. Trying OpenAI fallback...")
                # Fall through to OpenAI
                self.provider = "openai"
                self._init_openai(api_key)

        elif self.provider == "openai":
            self._init_openai(api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'mistral' or 'openai'")

    def _init_openai(self, api_key=None):
        """Initialize OpenAI as primary provider"""
        from openai import OpenAI
        from config import Config

        self.api_key = api_key or Config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.org_id = "org-Ac4M8r2L9ygbPiJVGyZ2fKaF"

        if self.api_key:
            suffix = self.api_key[-5:] if len(self.api_key) > 5 else "SHORT"
            logger.info(f"Analyzer initialized with OpenAI (key: ...{suffix})")
            print(f"       LLM Primary: OpenAI (key: ...{suffix})")
            self.client = OpenAI(api_key=self.api_key, organization=self.org_id)
        else:
            logger.warning("OPENAI_API_KEY not found. Analysis will be skipped.")
            print("       [!] OPENAI_API_KEY not found. Analysis will be skipped.")

    def _setup_openai_fallback(self, Config):
        """Setup OpenAI as fallback provider"""
        try:
            from openai import OpenAI
            openai_key = Config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            if openai_key:
                suffix = openai_key[-5:] if len(openai_key) > 5 else "SHORT"
                self.fallback_client = OpenAI(api_key=openai_key, organization="org-Ac4M8r2L9ygbPiJVGyZ2fKaF")
                self.fallback_provider = "openai"
                print(f"       LLM Fallback: OpenAI ready (key: ...{suffix})")
        except Exception as e:
            logger.warning(f"Could not setup OpenAI fallback: {e}")

    def analyze_video(self, comments, description, hashtags, stats: Dict[str, Any] = None):
        if not self.client:
            logger.warning("OpenAI client not initialized. Returning N/A results.")
            return {"summary": "N/A", "sentiment": "N/A", "topic": "N/A", "discussion_points": "N/A"}

        comments_text = "\n".join(comments) if comments else "No comments available."
        hashtags_text = ", ".join(hashtags) if hashtags else "No hashtags."

        # Format stats for context
        stats_text = "N/A"
        if stats:
            stats_text = f"Views: {stats.get('views_count', 0)}, Likes: {stats.get('likes_count', 0)}, Shares: {stats.get('shares_count', 0)}"

        # Check if we have meaningful data to analyze
        has_comments = comments and len(comments) > 0
        has_description = description and len(description.strip()) > 0

        if not has_comments:
            logger.warning(f"No comments available for analysis. Description length: {len(description) if description else 0}")

        # Construct different instructions based on whether we have comments
        if has_comments:
            summary_instruction = "Synthesize the provided User Comments into a detailed narrative. The comments are likely in Bahasa Melayu/Malay; translate the gist and summarize their sentiment in English. Identify major themes, agreements, disagreements, and quote at least 2 distinct user opinions (translated if in Malay)."
            discussion_instruction = "Extract 5-7 distinct words/slang/phrases used in the comments (NO hashtags)"
        else:
            summary_instruction = "Since no comments are available, provide a brief analysis based on the video description, hashtags, and stats. Analyze the likely public sentiment this video would generate based on the topic. Explain what people might say about this. Keep it under 100 words."
            discussion_instruction = "Extract 3-5 relevant keywords from the description that people would likely discuss (NO hashtags)"

        prompt = f"""
        Analyze this TikTok video based on the following data:

        Stats: {stats_text}
        Description: {description}
        Hashtags: {hashtags_text}
        User Comments:
        {comments_text}

        Return a JSON object with exactly these fields:
        {{
            "topic": "The main subject or title of the video (Max 5 words)",
            "summary": "{summary_instruction} Do NOT mention hashtags in the summary.",
            "key_issues": ["Main Key Insight 1", "Main Key Insight 2", "Critical Observation"],
            "trend_context": "Explanation of why this is trending. Use stats to justify viral potential.",
            "viral_potential": "High, Medium, or Low",
            "discussion_points": ["{discussion_instruction}"],
            "sentiment": "Positive, Negative, Neutral, or Mixed",
            "sentiment_score": 5  // Integer between 1 (Very Negative) and 10 (Very Positive)
        }}

        CRITICAL SENTIMENT RULES:
        1. If the video covers deaths, shootings, arrests, violence, or severe conflict, Sentiment MUST be "Negative" (Score 1-3).
        2. If the video is about political controversy, protest, or public outrage, Sentiment MUST be "Negative" or "Mixed" (Score 2-5).
        3. Do NOT label news about tragic events as "Positive" even if the reporting is neutral.
        4. "Positive" is reserved for uplifting, happy, or successful content.
        """

        try:
            import json
            content = None
            used_fallback = False

            # Call LLM based on provider (with automatic fallback)
            try:
                if self.provider == "mistral":
                    # Mistral API call
                    chat_response = self.client.chat.complete(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    content = chat_response.choices[0].message.content
                else:  # openai
                    # OpenAI API call
                    chat_response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo-1106",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=450
                    )
                    content = chat_response.choices[0].message.content

            except Exception as primary_error:
                # Primary LLM failed - try fallback
                logger.warning(f"Primary LLM ({self.provider}) failed: {primary_error}")
                print(f"       [!] {self.provider.upper()} failed: {str(primary_error)[:50]}")

                if self.fallback_client and self.fallback_provider == "openai":
                    print(f"       [FALLBACK] Trying OpenAI...")
                    logger.info("Attempting OpenAI fallback...")
                    try:
                        chat_response = self.fallback_client.chat.completions.create(
                            model="gpt-3.5-turbo-1106",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                                {"role": "user", "content": prompt}
                            ],
                            response_format={"type": "json_object"},
                            max_tokens=450
                        )
                        content = chat_response.choices[0].message.content
                        used_fallback = True
                        print(f"       [OK] OpenAI fallback successful!")
                    except Exception as fallback_error:
                        logger.error(f"Fallback LLM also failed: {fallback_error}")
                        print(f"       [FAIL] OpenAI fallback also failed: {str(fallback_error)[:50]}")
                        raise primary_error  # Re-raise original error
                else:
                    raise  # No fallback available

            # Parse JSON response
            if not content:
                raise ValueError("Empty response from LLM")

            data = json.loads(content)
            
            # Helper to safely get list or string
            issues = data.get("key_issues", [])
            if isinstance(issues, str): issues = [issues]
            
            # FORCE ALIGNMENT: Ensure Score matches Label to prevent Dashboard mismatches
            sent_label = data.get("sentiment", "Neutral")
            score = data.get("score", 5)
            
            try:
                score = int(score)
            except:
                score = 5

            if sent_label == "Positive" and score < 7: score = 8
            elif sent_label == "Negative" and score > 4: score = 2
            elif sent_label == "Neutral" and (score < 4 or score > 6): score = 5
            
            return {
                "topic": data.get("topic", "N/A"),
                "summary": data.get("summary", "No summary available."), # Added Summary Field
                "discussion": "; ".join(data.get("discussion_points", [])), # String for DB 'discussion' text
                "key_issues": issues, # List for UI
                "trend_context": data.get("trend_context", "No trend context available."),
                "viral_potential": data.get("viral_potential", "Low"),
                "sentiment": sent_label,
                "score": str(score)
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


def analyze_from_database(video_id: str, db_client: SupabaseClient, api_key: str = None, provider: str = "mistral") -> Optional[Dict[str, Any]]:
    """
    Analyze a video already in database

    Args:
        video_id: Video UUID
        db_client: Database client instance
        api_key: Optional explicit API key
        provider: "mistral" (default) or "openai"

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

        # Extract stats
        stats = {
            "views_count": video.get("views_count", 0),
            "likes_count": video.get("likes_count", 0),
            "shares_count": video.get("shares_count", 0)
        }

        # Run analysis
        analyzer = Analyzer(api_key=api_key, provider=provider)
        analysis = analyzer.analyze_video(comments, description, hashtags, stats=stats)

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


def batch_analyze_unanalyzed(db_client: SupabaseClient, limit: int = 10, api_key: str = None, provider: str = "mistral") -> Dict[str, Any]:
    """
    Analyze videos without sentiment data

    Args:
        db_client: Database client instance
        limit: Maximum number of videos to analyze
        api_key: Optional explicit API key
        provider: "mistral" (default) or "openai"

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
                analysis = analyze_from_database(video_id, db_client, api_key=api_key, provider=provider)
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
