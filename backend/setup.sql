-- TikTok Political Sentiment Scraper Database Schema
-- Run this in Supabase SQL Editor to create tables

-- ============================================
-- Videos Table
-- ============================================
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tiktok_id TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    author_username TEXT NOT NULL,
    description TEXT,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    hashtags JSONB DEFAULT '[]'::jsonb,
    screenshot_base64 TEXT,
    search_keyword TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Comments Table
-- ============================================
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    author_username TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Sentiment Analysis Table
-- ============================================
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    topic TEXT,
    discussion_points TEXT,
    sentiment TEXT,
    sentiment_score INTEGER,
    key_issues JSONB DEFAULT '[]'::jsonb,
    transcript TEXT,
    summary TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(video_id)
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_videos_tiktok_id ON videos(tiktok_id);
CREATE INDEX IF NOT EXISTS idx_videos_scraped_at ON videos(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_search_keyword ON videos(search_keyword);
CREATE INDEX IF NOT EXISTS idx_videos_author ON videos(author_username);
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author_username);
CREATE INDEX IF NOT EXISTS idx_sentiment_video_id ON sentiment_analysis(video_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_sentiment ON sentiment_analysis(sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiment_score ON sentiment_analysis(sentiment_score DESC);

-- GIN indexes for JSONB columns (enables efficient JSONB queries)
CREATE INDEX IF NOT EXISTS idx_videos_hashtags_gin ON videos USING GIN (hashtags);
CREATE INDEX IF NOT EXISTS idx_sentiment_key_issues_gin ON sentiment_analysis USING GIN (key_issues);

-- ============================================
-- Comments
-- ============================================
COMMENT ON TABLE videos IS 'Stores scraped TikTok video metadata';
COMMENT ON TABLE comments IS 'Stores comments for each video';
COMMENT ON TABLE sentiment_analysis IS 'Stores AI-generated sentiment analysis results';
COMMENT ON COLUMN videos.tiktok_id IS 'Unique TikTok video ID extracted from URL';
COMMENT ON COLUMN videos.hashtags IS 'Array of hashtags as JSONB';
COMMENT ON COLUMN videos.screenshot_base64 IS 'Base64 encoded screenshot of video';
COMMENT ON COLUMN videos.search_keyword IS 'Keyword used to find this video';
COMMENT ON COLUMN sentiment_analysis.sentiment_score IS 'Sentiment score from 1-10';
COMMENT ON COLUMN sentiment_analysis.key_issues IS 'Array of key political issues discussed';
COMMENT ON COLUMN sentiment_analysis.transcript IS 'AI-generated transcript of video content';
COMMENT ON COLUMN sentiment_analysis.summary IS 'AI-generated summary of video and comments';
