import { useMemo } from 'react'
import './Cards.css'

const SentimentOverview = ({ videos }) => {
  const sentimentData = useMemo(() => {
    if (!videos || videos.length === 0) {
      return {
        analyzed: [],
        counts: { positive: 0, neutral: 0, negative: 0, veryNegative: 0 },
        avgScore: 0,
        keyTopics: []
      }
    }

    // Filter videos with sentiment data
    const analyzed = videos.filter(v => v.sentiment)

    // Count sentiments
    const counts = analyzed.reduce((acc, v) => {
      const sentiment = v.sentiment || 'neutral'
      if (sentiment.includes('negative')) {
        if (sentiment === 'very_negative') {
          acc.veryNegative++
        } else {
          acc.negative++
        }
      } else if (sentiment.includes('positive')) {
        acc.positive++
      } else {
        acc.neutral++
      }
      return acc
    }, { positive: 0, neutral: 0, negative: 0, veryNegative: 0 })

    // Calculate average score
    const avgScore = analyzed.length > 0
      ? (analyzed.reduce((sum, v) => sum + (v.sentimentScore || 0), 0) / analyzed.length).toFixed(2)
      : 0

    // Extract key topics (limit to top 5)
    const topicMap = {}
    analyzed.forEach(v => {
      if (v.topic) {
        try {
          const topics = typeof v.topic === 'string' ? JSON.parse(v.topic) : v.topic
          if (Array.isArray(topics)) {
            topics.forEach(t => {
              const name = typeof t === 'string' ? t : t.name
              if (name) {
                topicMap[name] = (topicMap[name] || 0) + 1
              }
            })
          }
        } catch (e) {
          // Skip invalid topic data
        }
      }
    })
    const keyTopics = Object.entries(topicMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }))

    return { analyzed, counts, avgScore, keyTopics }
  }, [videos])

  const getSentimentLabel = (score) => {
    if (score >= 0.7) return 'Very Positive'
    if (score >= 0.5) return 'Positive'
    if (score >= 0.3) return 'Neutral'
    if (score >= 0.1) return 'Negative'
    return 'Very Negative'
  }

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return '#F39C12'
    if (sentiment.includes('positive')) return '#2ECC71'
    if (sentiment === 'very_negative') return '#C0392B'
    if (sentiment.includes('negative')) return '#E74C3C'
    return '#F39C12'
  }

  if (sentimentData.analyzed.length === 0) {
    return (
      <div className="sentiment-overview-card fade-in">
        <h4 className="card-subtitle">Sentiment Analysis</h4>
        <p className="empty-message">No analyzed videos available yet.</p>
      </div>
    )
  }

  return (
    <div className="sentiment-overview-card fade-in">
      <h4 className="card-subtitle">Detailed Sentiment Breakdown</h4>

      {/* Sentiment counts */}
      <div className="sentiment-counts">
        <div className="sentiment-stat positive">
          <span className="stat-value">{sentimentData.counts.positive}</span>
          <span className="stat-label">Positive</span>
        </div>
        <div className="sentiment-stat neutral">
          <span className="stat-value">{sentimentData.counts.neutral}</span>
          <span className="stat-label">Neutral</span>
        </div>
        <div className="sentiment-stat negative">
          <span className="stat-value">{sentimentData.counts.negative}</span>
          <span className="stat-label">Negative</span>
        </div>
        <div className="sentiment-stat very-negative">
          <span className="stat-value">{sentimentData.counts.veryNegative}</span>
          <span className="stat-label">Very Negative</span>
        </div>
      </div>

      {/* Average score */}
      <div className="avg-score-section">
        <div className="avg-score-label">Average Sentiment Score</div>
        <div className="avg-score-value">
          {sentimentData.avgScore} / 1.0
          <span className="score-label">({getSentimentLabel(parseFloat(sentimentData.avgScore))})</span>
        </div>
      </div>

      {/* Key topics */}
      {sentimentData.keyTopics.length > 0 && (
        <div className="key-topics-section">
          <h5 className="section-title">Most Discussed Topics</h5>
          <div className="topics-list">
            {sentimentData.keyTopics.map((topic, idx) => (
              <div key={idx} className="topic-item">
                <span className="topic-name">{topic.name}</span>
                <span className="topic-count">{topic.count} videos</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent analyzed videos */}
      <div className="recent-analyzed-section">
        <h5 className="section-title">Recent Analyzed Videos</h5>
        <div className="analyzed-videos-list">
          {sentimentData.analyzed.slice(0, 3).map((video, idx) => (
            <div key={idx} className="analyzed-video-item">
              <div
                className="sentiment-indicator"
                style={{ backgroundColor: getSentimentColor(video.sentiment) }}
              />
              <div className="video-info">
                <div className="video-author">@{video.authorUsername}</div>
                <div className="video-sentiment">
                  {video.sentiment?.replace('_', ' ').toUpperCase()}
                  <span className="sentiment-score">({video.sentimentScore?.toFixed(2)})</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SentimentOverview
