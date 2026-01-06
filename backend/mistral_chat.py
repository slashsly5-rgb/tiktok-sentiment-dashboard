"""
Mistral AI Chat Service
Handles conversational AI for TikTok sentiment analytics
"""

import os
from mistralai import Mistral
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database import SupabaseClient
from config import Config
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class MistralChatService:
    """
    Mistral AI chat service for analytics insights
    """

    def __init__(self, db_client: SupabaseClient):
        self.db = db_client
        self.api_key = Config.MISTRAL_API_KEY
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not set. Chat service will be disabled.")
            self.client = None
        else:
            self.client = Mistral(api_key=self.api_key)
            logger.info("Mistral AI client initialized successfully")

        # In-memory session storage: {session_id: {"history": [...], "last_activity": datetime}}
        self.sessions = {}

    def _clean_expired_sessions(self):
        """Remove sessions older than CHAT_SESSION_TIMEOUT"""
        now = datetime.now()
        expired = [
            sid for sid, data in self.sessions.items()
            if (now - data["last_activity"]).seconds > Config.CHAT_SESSION_TIMEOUT
        ]
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned expired session {sid}")

    def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create session"""
        self._clean_expired_sessions()

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "last_activity": datetime.now(),
                "created_at": datetime.now()
            }
            logger.info(f"Created new session {session_id}")
        else:
            self.sessions[session_id]["last_activity"] = datetime.now()

        return self.sessions[session_id]

    def _build_context_from_filters(self, filters: Dict[str, Any]) -> str:
        """
        Query database with filters and build context string for Mistral

        Args:
            filters: {
                "days": int (default 30),
                "keywords": List[str] (optional),
                "sentiment": str (optional: positive, negative, neutral)
            }

        Returns:
            Formatted context string with sentiment data
        """
        try:
            days = filters.get("days", 30)
            keywords = filters.get("keywords", [])
            sentiment_filter = filters.get("sentiment")

            # Get videos for the time period
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Query videos
            query = self.db.supabase.table("videos").select("id, description, search_keyword").gte("scraped_at", cutoff_date)

            # Apply keyword filter if provided
            if keywords:
                # For simplicity, filter in Python (can optimize with Supabase filters)
                videos_response = query.execute()
                videos = [
                    v for v in videos_response.data
                    if any(kw.lower() in v.get("search_keyword", "").lower() for kw in keywords)
                ]
            else:
                videos = query.execute().data

            if not videos:
                return f"No videos found in the last {days} days matching the filters."

            video_ids = [v["id"] for v in videos]

            # Get sentiment analyses for these videos
            sentiment_query = self.db.supabase.table("sentiment_analysis").select(
                "video_id, summary, topic, discussion_points, key_issues, sentiment, sentiment_score"
            ).in_("video_id", video_ids)

            # Apply sentiment filter if provided
            if sentiment_filter:
                sentiment_query = sentiment_query.ilike("sentiment", f"%{sentiment_filter}%")

            sentiments = sentiment_query.execute().data

            if not sentiments:
                return f"No sentiment analysis data found for the selected period (last {days} days)."

            # Build context
            context_parts = [
                f"# TikTok Sentiment Analysis Context",
                f"Period: Last {days} days",
                f"Total videos analyzed: {len(sentiments)}",
                f"",
                f"## Aggregated Insights:",
                f""
            ]

            # Aggregate summaries
            all_summaries = [s.get("summary") or s.get("discussion_points") for s in sentiments if s.get("summary") or s.get("discussion_points")]
            if all_summaries:
                context_parts.append("### AI Summaries:")
                for i, summary in enumerate(all_summaries[:10], 1):  # Limit to 10
                    context_parts.append(f"{i}. {summary}")
                context_parts.append("")

            # Aggregate key issues
            all_issues = []
            for s in sentiments:
                issues = s.get("key_issues", [])
                if isinstance(issues, list):
                    for issue in issues:
                        if isinstance(issue, dict):
                            all_issues.append(issue.get("title", str(issue)))
                        else:
                            all_issues.append(str(issue))

            if all_issues:
                issue_counts = Counter(all_issues)
                context_parts.append("### Top Key Issues:")
                for issue, count in issue_counts.most_common(10):
                    context_parts.append(f"- {issue} (mentioned {count} times)")
                context_parts.append("")

            # Aggregate discussion topics
            all_topics = [s.get("topic") for s in sentiments if s.get("topic")]
            if all_topics:
                topic_counts = Counter(all_topics)
                context_parts.append("### Discussion Topics:")
                for topic, count in topic_counts.most_common(5):
                    context_parts.append(f"- {topic} ({count} videos)")
                context_parts.append("")

            # Sentiment distribution
            sentiment_types = [s.get("sentiment") for s in sentiments if s.get("sentiment")]
            if sentiment_types:
                sent_counts = Counter(sentiment_types)
                context_parts.append("### Sentiment Distribution:")
                for sent, count in sent_counts.items():
                    pct = round((count / len(sentiments)) * 100, 1)
                    context_parts.append(f"- {sent}: {count} ({pct}%)")
                context_parts.append("")

            # Average sentiment score
            scores = [s.get("sentiment_score") for s in sentiments if s.get("sentiment_score")]
            if scores:
                avg_score = sum(scores) / len(scores)
                context_parts.append(f"### Average Sentiment Score: {avg_score:.2f}/10")
                context_parts.append("")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error building context: {e}", exc_info=True)
            return f"Error retrieving data: {str(e)}"

    def _truncate_context_if_needed(self, context: str, max_chars: int = 6000) -> str:
        """
        Truncate context to fit within token limits
        Mistral Medium has ~32k context window, we use ~6k chars (~1500 tokens) for context
        """
        if len(context) <= max_chars:
            return context

        logger.warning(f"Context too large ({len(context)} chars), truncating to {max_chars}")
        return context[:max_chars] + "\n\n[Context truncated due to size...]"

    def chat(
        self,
        session_id: str,
        user_message: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send chat message and get Mistral response

        Args:
            session_id: Unique session identifier
            user_message: User's message
            filters: Optional filters for data context (days, keywords, sentiment)

        Returns:
            {
                "response": str,
                "session_id": str,
                "message_count": int,
                "context_used": bool
            }
        """
        if not self.client:
            return {
                "response": "Chat service is not configured. Please set MISTRAL_API_KEY.",
                "error": "service_unavailable",
                "session_id": session_id
            }

        try:
            # Get session
            session = self._get_session(session_id)

            # Build context from filters (if provided)
            context = None
            if filters:
                context = self._build_context_from_filters(filters)
                context = self._truncate_context_if_needed(context)

            # Build messages for Mistral
            messages = []

            # System prompt
            system_prompt = """You are BUMI, an AI assistant specializing in TikTok political sentiment analysis for Sarawak, Malaysia.

You have access to aggregated sentiment analysis data from TikTok videos, including:
- AI-generated summaries of video content and comments
- Key political issues mentioned
- Discussion topics and trends
- Sentiment scores and distributions

Your role is to:
1. Answer questions about sentiment trends, key issues, and public opinion
2. Provide insights based on the data context provided
3. Help users understand political sentiment patterns
4. Be concise, factual, and data-driven
5. Acknowledge when data is limited or unavailable

When data context is provided, use it to give specific, evidence-based answers. When no context is available, provide general guidance on what could be analyzed."""

            messages.append({"role": "system", "content": system_prompt})

            # Add data context if available
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Current data context based on user's filter selection:\n\n{context}"
                })

            # Add conversation history (last N messages)
            history = session["history"][-Config.MAX_CHAT_HISTORY_LENGTH:]
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Call Mistral API
            logger.info(f"Sending request to Mistral for session {session_id}")
            response = self.client.chat.complete(
                model=Config.MISTRAL_MODEL,
                messages=messages,
                max_tokens=Config.MISTRAL_MAX_TOKENS,
                temperature=Config.MISTRAL_TEMPERATURE
            )

            # Extract response
            assistant_message = response.choices[0].message.content

            # Update session history
            session["history"].append({"role": "user", "content": user_message})
            session["history"].append({"role": "assistant", "content": assistant_message})

            # Keep history bounded
            if len(session["history"]) > Config.MAX_CHAT_HISTORY_LENGTH * 2:
                session["history"] = session["history"][-Config.MAX_CHAT_HISTORY_LENGTH * 2:]

            logger.info(f"Successfully generated response for session {session_id}")

            return {
                "response": assistant_message,
                "session_id": session_id,
                "message_count": len(session["history"]) // 2,
                "context_used": context is not None
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "error": "processing_error",
                "session_id": session_id
            }

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get full conversation history for a session"""
        session = self._get_session(session_id)
        return session["history"]

    def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session {session_id}")
            return True
        return False
