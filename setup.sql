-- TikTok Political Sentiment Scraper - Database Schema
-- Supabase PostgreSQL Setup
-- Run this script in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- VIDEOS TABLE
-- ============================================
-- Stores TikTok video metadata and statistics

CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tiktok_id VARCHAR(255) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    author_username VARCHAR(255),
    description TEXT,
    post_url TEXT,                          -- Supabase Storage URL for video post/screenshot
    transcribed_url TEXT,                   -- Supabase Storage URL for transcription file
    summary TEXT,                           -- AI-generated video content summary
    views_count BIGINT DEFAULT 0,
    likes_count BIGINT DEFAULT 0,
    shares_count BIGINT DEFAULT 0,
    comments_count BIGINT DEFAULT 0,
    hashtags JSONB,
    search_keyword VARCHAR(255),            -- Keyword used to find this video
    scraped_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- COMMENTS TABLE
-- ============================================
-- Stores TikTok video comments

CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    author_username VARCHAR(255),
    likes_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- SENTIMENT ANALYSIS TABLE
-- ============================================
-- Stores AI-generated sentiment analysis results

CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    overall_sentiment VARCHAR(50),          -- positive/negative/neutral/mixed
    sentiment_score DECIMAL(3,1),           -- 1-10 scale
    topic TEXT,
    discussion_points TEXT,
    key_issues JSONB,                       -- Array of identified issues
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- PERFORMANCE INDEXES
-- ============================================

-- Videos table indexes
CREATE INDEX IF NOT EXISTS idx_videos_tiktok_id ON videos(tiktok_id);
CREATE INDEX IF NOT EXISTS idx_videos_scraped_at ON videos(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_keyword ON videos(search_keyword);
CREATE INDEX IF NOT EXISTS idx_videos_author ON videos(author_username);

-- Comments table indexes
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);

-- Sentiment analysis table indexes
CREATE INDEX IF NOT EXISTS idx_sentiment_video_id ON sentiment_analysis(video_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_overall ON sentiment_analysis(overall_sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiment_score ON sentiment_analysis(sentiment_score DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed_at ON sentiment_analysis(analyzed_at DESC);

-- ============================================
-- HELPER VIEWS
-- ============================================

-- View: Videos with sentiment analysis
CREATE OR REPLACE VIEW videos_with_sentiment AS
SELECT
    v.*,
    sa.overall_sentiment,
    sa.sentiment_score,
    sa.topic,
    sa.discussion_points,
    sa.key_issues,
    sa.analyzed_at
FROM videos v
LEFT JOIN sentiment_analysis sa ON v.id = sa.video_id;

-- View: Unanalyzed videos
CREATE OR REPLACE VIEW unanalyzed_videos AS
SELECT v.*
FROM videos v
LEFT JOIN sentiment_analysis sa ON v.id = sa.video_id
WHERE sa.id IS NULL
ORDER BY v.scraped_at DESC;

-- ============================================
-- SAMPLE QUERIES
-- ============================================

-- Get recent videos with sentiment (last 7 days)
-- SELECT * FROM videos_with_sentiment
-- WHERE scraped_at >= NOW() - INTERVAL '7 days'
-- ORDER BY scraped_at DESC;

-- Get sentiment overview
-- SELECT
--     overall_sentiment,
--     COUNT(*) as count,
--     AVG(sentiment_score) as avg_score
-- FROM sentiment_analysis
-- WHERE analyzed_at >= NOW() - INTERVAL '7 days'
-- GROUP BY overall_sentiment;

-- Get videos by keyword
-- SELECT * FROM videos
-- WHERE search_keyword = 'Abang Johari'
-- ORDER BY scraped_at DESC;

-- Get top issues discussed
-- SELECT
--     jsonb_array_elements_text(key_issues) as issue,
--     COUNT(*) as mention_count
-- FROM sentiment_analysis
-- WHERE analyzed_at >= NOW() - INTERVAL '30 days'
-- GROUP BY issue
-- ORDER BY mention_count DESC
-- LIMIT 10;

-- Get videos with summaries
-- SELECT
--     author_username,
--     description,
--     summary,
--     views_count,
--     overall_sentiment
-- FROM videos_with_sentiment
-- WHERE summary IS NOT NULL
-- ORDER BY scraped_at DESC;

-- ============================================
-- ROW LEVEL SECURITY (Optional - for future)
-- ============================================

-- Enable RLS on tables (uncomment when ready)
-- ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sentiment_analysis ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
-- CREATE POLICY "Allow public read access on videos"
-- ON videos FOR SELECT
-- USING (true);

-- CREATE POLICY "Allow public read access on comments"
-- ON comments FOR SELECT
-- USING (true);

-- CREATE POLICY "Allow public read access on sentiment_analysis"
-- ON sentiment_analysis FOR SELECT
-- USING (true);

-- ============================================
-- TABLE COMMENTS
-- ============================================

COMMENT ON TABLE videos IS 'Stores TikTok video metadata scraped from searches';
COMMENT ON TABLE comments IS 'Stores comments from TikTok videos';
COMMENT ON TABLE sentiment_analysis IS 'Stores AI-generated sentiment analysis results';
COMMENT ON COLUMN videos.post_url IS 'Supabase Storage URL for video post/screenshot image';
COMMENT ON COLUMN videos.transcribed_url IS 'Supabase Storage URL for transcription file (JSON/TXT)';
COMMENT ON COLUMN videos.summary IS 'AI-generated summary of video content';
COMMENT ON COLUMN videos.search_keyword IS 'Keyword used to discover this video';
COMMENT ON VIEW videos_with_sentiment IS 'Videos joined with their sentiment analysis';
COMMENT ON VIEW unanalyzed_videos IS 'Videos that have not been analyzed yet';
