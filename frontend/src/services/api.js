import axios from 'axios'

// Use empty baseURL to enable Vite proxy for all requests
// When VITE_API_URL is set (production), use it. Otherwise use relative URLs (development)
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Fetch dashboard summary data using new comprehensive analytics endpoint
 */
export const fetchDashboardData = async (days = 30) => {
  try {
    // Use the new comprehensive dashboard analytics endpoint
    // Dashboard queries are complex aggregations, so we use a longer timeout
    const response = await apiClient.get('/api/analytics/dashboard', {
      params: { days },
      timeout: 30000  // 30 seconds for dashboard aggregations
    })

    const data = response.data || {}
    const videoStats = data.videoStats || {}
    const sentimentStats = data.sentimentStats || {}
    const topAuthors = data.topAuthors || []
    const topHashtags = data.topHashtags || []
    const topKeywords = data.topKeywords || []

    // Calculate sentiment breakdown percentages
    const totalAnalyzed = sentimentStats.analyzedCount || 0
    const breakdown = sentimentStats.sentimentBreakdown || {}
    const positive = breakdown.positive || 0
    const negative = breakdown.negative || 0
    const neutral = breakdown.neutral || 0
    const veryNegative = breakdown.veryNegative || 0

    const positivePercent = totalAnalyzed > 0 ? Math.round((positive / totalAnalyzed) * 100) : 0
    const negativePercent = totalAnalyzed > 0 ? Math.round(((negative + veryNegative) / totalAnalyzed) * 100) : 0
    const neutralPercent = totalAnalyzed > 0 ? Math.round((neutral / totalAnalyzed) * 100) : 0

    // Get average sentiment score (already normalized to 0-1)
    const avgSentiment = sentimentStats.avgScore || 0

    // Transform API data into dashboard format
    return {
      sentiment: {
        overall: getSentimentLabel(avgSentiment),
        score: avgSentiment,
        type: getSentimentType(avgSentiment)
      },
      summary: totalAnalyzed > 0
        ? `Analysis based on ${totalAnalyzed} analyzed videos from ${videoStats.total || 0} total videos over the past ${data.periodDays || 30} days.`
        : 'No analyzed data available yet. Please scrape and analyze videos first.',
      keyIssues: formatKeyIssues(topHashtags, topKeywords),
      mapRegions: [], // Not available yet
      analytics: {
        reach: {
          views: videoStats.totalViews || 0,
          likes: videoStats.totalLikes || 0
        },
        sentimentBreakdown: {
          positive: positivePercent,
          negative: negativePercent,
          neutral: neutralPercent
        },
        summary: totalAnalyzed > 0
          ? `Analyzed ${totalAnalyzed} videos with ${videoStats.totalComments || 0} total comments. Avg engagement rate: ${videoStats.avgEngagementRate || 0}%`
          : 'No sentiment analysis data available yet.'
      },
      stats: {
        totalVideos: videoStats.total || 0,
        positiveSentiment: positivePercent,
        trendingTopics: topHashtags.length || 0,
        criticalIssues: sentimentStats.mostDiscussedIssues?.length || 0
      },
      topAuthors,
      topHashtags,
      topKeywords
    }
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
    throw new Error('Failed to fetch dashboard data from backend')
  }
}

/**
 * Helper: Get sentiment label from score (0-1)
 */
function getSentimentLabel(score) {
  if (score >= 0.7) return 'Very Positive'
  if (score >= 0.5) return 'Moderately Positive'
  if (score >= 0.3) return 'Neutral'
  if (score >= 0.1) return 'Moderately Negative'
  return 'Negative'
}

/**
 * Helper: Get sentiment type from score
 */
function getSentimentType(score) {
  if (score >= 0.5) return 'positive'
  if (score >= 0.3) return 'neutral'
  return 'negative'
}

/**
 * Helper: Format key issues from hashtags and keywords
 */
function formatKeyIssues(hashtags, keywords) {
  const issues = []

  // Add top hashtags
  hashtags.slice(0, 3).forEach(item => {
    issues.push({
      name: item.hashtag?.replace('#', '') || item.tag?.replace('#', '') || 'Unknown',
      trend: 'neutral',
      count: item.count || 0
    })
  })

  // Add top keywords
  keywords.slice(0, 2).forEach(item => {
    if (!issues.find(i => i.name === item.keyword)) {
      issues.push({
        name: item.keyword || 'Unknown',
        trend: 'neutral',
        count: item.videoCount || 0
      })
    }
  })

  return issues.slice(0, 5)
}

/**
 * Fetch recent videos (legacy endpoint - still available)
 */
export const fetchRecentVideos = async (days = 7, limit = 50) => {
  try {
    const response = await apiClient.get('/videos', {
      params: { days, limit }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching videos:', error)
    throw error
  }
}

/**
 * Fetch single video with details
 */
export const fetchVideoById = async (videoId, includeComments = true, includeSentiment = true) => {
  try {
    const response = await apiClient.get(`/api/videos/${videoId}`, {
      params: { include_comments: includeComments, include_sentiment: includeSentiment }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching video:', error)
    throw error
  }
}

/**
 * Fetch complete video view (video + comments + sentiment)
 */
export const fetchCompleteVideo = async (videoId) => {
  try {
    const response = await apiClient.get(`/api/videos/${videoId}/complete`)
    return response.data
  } catch (error) {
    console.error('Error fetching complete video:', error)
    throw error
  }
}

/**
 * Search videos with filters
 */
export const searchVideos = async (filters = {}) => {
  try {
    const response = await apiClient.get('/api/videos/search', { params: filters })
    return response.data
  } catch (error) {
    console.error('Error searching videos:', error)
    throw error
  }
}

/**
 * Fetch trending videos
 */
export const fetchTrendingVideos = async (days = 7, limit = 10) => {
  try {
    const response = await apiClient.get('/api/videos/trending', {
      params: { days, limit }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching trending videos:', error)
    throw error
  }
}

/**
 * Fetch videos by author
 */
export const fetchVideosByAuthor = async (username, limit = 50, offset = 0) => {
  try {
    const response = await apiClient.get(`/api/videos/by-author/${username}`, {
      params: { limit, offset }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching videos by author:', error)
    throw error
  }
}

/**
 * Fetch videos by hashtag
 */
export const fetchVideosByHashtag = async (hashtag, limit = 50, offset = 0) => {
  try {
    const response = await apiClient.get(`/api/videos/by-hashtag/${hashtag}`, {
      params: { limit, offset }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching videos by hashtag:', error)
    throw error
  }
}

/**
 * Fetch sentiment overview (legacy endpoint - still available)
 */
export const fetchSentimentOverview = async (days = 7) => {
  try {
    const response = await apiClient.get('/sentiment/overview', {
      params: { days }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching sentiment overview:', error)
    throw error
  }
}

/**
 * Fetch sentiment analysis by video ID
 */
export const fetchSentimentByVideo = async (videoId, includeVideo = false) => {
  try {
    const response = await apiClient.get(`/api/sentiment/${videoId}`, {
      params: { include_video: includeVideo }
    })
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      console.warn(`Sentiment analysis not found for video ${videoId}`)
      return null
    }
    console.error('Error fetching sentiment:', error)
    throw error
  }
}

/**
 * Fetch sentiment analyses by type
 */
export const fetchSentimentByType = async (sentimentType, limit = 50, offset = 0) => {
  try {
    const response = await apiClient.get(`/api/sentiment/by-type/${sentimentType}`, {
      params: { limit, offset }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching sentiment by type:', error)
    throw error
  }
}

/**
 * Fetch sentiment analyses by score range
 */
export const fetchSentimentByScore = async (minScore, maxScore, limit = 50, offset = 0) => {
  try {
    const response = await apiClient.get('/api/sentiment/by-score', {
      params: { min_score: minScore, max_score: maxScore, limit, offset }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching sentiment by score:', error)
    throw error
  }
}

/**
 * Fetch comments for a video
 */
export const fetchVideoComments = async (videoId, limit = 100, offset = 0) => {
  try {
    const response = await apiClient.get(`/api/videos/${videoId}/comments`, {
      params: { limit, offset }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching video comments:', error)
    throw error
  }
}

/**
 * Fetch all comments with filters
 */
export const fetchComments = async (filters = {}, limit = 100, offset = 0) => {
  try {
    const response = await apiClient.get('/api/comments', {
      params: { ...filters, limit, offset }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching comments:', error)
    throw error
  }
}

/**
 * Fetch comment statistics
 */
export const fetchCommentStats = async (days = 7, videoId = null) => {
  try {
    const params = { days }
    if (videoId) params.video_id = videoId
    const response = await apiClient.get('/api/comments/stats', { params })
    return response.data
  } catch (error) {
    console.error('Error fetching comment stats:', error)
    throw error
  }
}

/**
 * Fetch top commenters
 */
export const fetchTopCommenters = async (days = 7, limit = 10) => {
  try {
    const response = await apiClient.get('/api/comments/top-commenters', {
      params: { days, limit }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching top commenters:', error)
    throw error
  }
}

/**
 * Fetch top authors
 */
export const fetchTopAuthors = async (days = 7, limit = 10, sortBy = 'videos') => {
  try {
    const response = await apiClient.get('/api/analytics/top-authors', {
      params: { days, limit, sort_by: sortBy }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching top authors:', error)
    throw error
  }
}

/**
 * Fetch top hashtags
 */
export const fetchTopHashtags = async (days = 7, limit = 10) => {
  try {
    const response = await apiClient.get('/api/analytics/top-hashtags', {
      params: { days, limit }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching top hashtags:', error)
    throw error
  }
}

/**
 * Fetch keyword performance
 */
export const fetchKeywordPerformance = async (days = 7) => {
  try {
    const response = await apiClient.get('/api/analytics/keyword-performance', {
      params: { days }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching keyword performance:', error)
    throw error
  }
}

/**
 * Fetch sentiment trends over time
 */
export const fetchSentimentTrends = async (days = 30, groupBy = 'day') => {
  try {
    const response = await apiClient.get('/api/analytics/sentiment-trends', {
      params: { days, group_by: groupBy }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching sentiment trends:', error)
    throw error
  }
}

/**
 * Fetch engagement statistics
 */
export const fetchEngagementStats = async (days = 7) => {
  try {
    const response = await apiClient.get('/api/analytics/engagement-stats', {
      params: { days }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching engagement stats:', error)
    throw error
  }
}

/**
 * Fetch top political issues
 */
export const fetchTopIssues = async (days = 7, limit = 10) => {
  try {
    const response = await apiClient.get('/api/analytics/top-issues', {
      params: { days, limit }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching top issues:', error)
    throw error
  }
}

/**
 * Send chat message to Mistral AI assistant with context filters
 */
export const sendChatMessage = async (sessionId, message, filters = null) => {
  try {
    const payload = {
      session_id: sessionId,
      message: message
    }

    // Add filters if provided
    if (filters) {
      payload.filters = filters
    }

    const response = await apiClient.post('/api/chat', payload, {
      timeout: 30000  // 30 seconds for AI processing
    })

    return response.data
  } catch (error) {
    console.error('Error sending chat message:', error)
    throw error
  }
}

/**
 * Get conversation history for a session
 */
export const getChatHistory = async (sessionId) => {
  try {
    const response = await apiClient.get(`/api/chat/history/${sessionId}`)
    return response.data
  } catch (error) {
    console.error('Error fetching chat history:', error)
    throw error
  }
}

/**
 * Clear chat session
 */
export const clearChatSession = async (sessionId) => {
  try {
    const response = await apiClient.delete(`/api/chat/clear/${sessionId}`)
    return response.data
  } catch (error) {
    console.error('Error clearing chat session:', error)
    throw error
  }
}

/**
 * Fetch videos with enriched sentiment data
 * Fetches recent videos and enriches them with sentiment analysis
 */
export const fetchVideosWithSentiment = async (days = 30, limit = 50) => {
  try {
    // Fetch videos with sentiment included in one efficient query
    const response = await apiClient.get('/videos', {
      params: {
        days,
        limit,
        include_sentiment: true
      },
      timeout: 20000  // 20 seconds for video queries with sentiment joins
    })

    return {
      count: response.data.count,
      videos: response.data.videos || []
    }
  } catch (error) {
    console.error('Error fetching videos with sentiment:', error)
    throw error
  }
}

export default apiClient
