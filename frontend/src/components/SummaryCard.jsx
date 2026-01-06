import { useState, useEffect, useMemo } from 'react'
import './Cards.css'

const SummaryCard = ({ sentiment, summary, keyIssues: defaultIssues, videos = [] }) => {
  const [topIssues, setTopIssues] = useState([])
  const [loading, setLoading] = useState(true)

  // Calculate average sentiment from videos
  const avgSentiment = useMemo(() => {
    if (!videos || videos.length === 0) return 5 // Default to neutral (middle of 1-10 scale)

    const videosWithSentiment = videos.filter(v => v.sentimentScore != null && v.sentimentScore > 0)
    if (videosWithSentiment.length === 0) return 5

    const sum = videosWithSentiment.reduce((acc, v) => acc + v.sentimentScore, 0)
    const avg = sum / videosWithSentiment.length

    // Convert from 0-1 scale to 1-10 scale if needed
    if (avg <= 1) {
      return avg * 10
    }
    return avg
  }, [videos])

  // Calculate top issues from videos
  useEffect(() => {
    const calculateTopIssues = () => {
      if (!videos || videos.length === 0) {
        setTopIssues(defaultIssues || [])
        setLoading(false)
        return
      }

      // Aggregate issues
      const issueMap = new Map()

      videos.forEach(video => {
        if (video.keyIssues && Array.isArray(video.keyIssues)) {
          video.keyIssues.forEach(issue => {
            const title = typeof issue === 'string' ? issue : issue.title
            if (!title) return

            if (issueMap.has(title)) {
              const existing = issueMap.get(title)
              existing.count++
              existing.scores.push(video.sentimentScore || 5)
            } else {
              issueMap.set(title, {
                issue: title,
                count: 1,
                scores: [video.sentimentScore || 5]
              })
            }
          })
        }
      })

      // Calculate trends and format
      const issues = Array.from(issueMap.values())
        .map(item => {
          const avgScore = item.scores.reduce((a, b) => a + b, 0) / item.scores.length
          // Convert 0-1 scale to 1-10 if needed
          const normalizedScore = avgScore <= 1 ? avgScore * 10 : avgScore

          let trend = 'neutral'
          if (normalizedScore > 6) trend = 'up'
          else if (normalizedScore < 4) trend = 'down'

          return {
            issue: item.issue,
            mentionCount: item.count,
            avgSentiment: normalizedScore,
            trend
          }
        })
        .sort((a, b) => b.mentionCount - a.mentionCount)
        .slice(0, 5)

      setTopIssues(issues)
      setLoading(false)
    }

    calculateTopIssues()
  }, [videos, defaultIssues])

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return '↑'
      case 'down': return '↓'
      default: return '→'
    }
  }

  const getSentimentLabel = (score) => {
    if (score >= 8) return 'Very Positive'
    if (score >= 6) return 'Moderately Positive'
    if (score >= 4) return 'Neutral'
    if (score >= 2) return 'Moderately Negative'
    return 'Very Negative'
  }

  // Position marker on the intensity bar (0-100%)
  const getMarkerPosition = (score) => {
    // Convert 1-10 score to 0-100% position
    return ((score - 1) / 9) * 100
  }

  return (
    <div className="summary-card fade-in">
      <div className={`sentiment-badge ${sentiment.type}`}>
        {sentiment.overall}
      </div>

      <h3 className="card-title">Briefing Summary</h3>

      <p className="card-description">{summary}</p>

      {/* Sentiment Intensity Bar */}
      {!loading && (
        <div className="sentiment-intensity">
          <h4 className="intensity-title">Overall Sentiment</h4>
          <div className="intensity-label">{getSentimentLabel(avgSentiment)}</div>
          <div className="intensity-bar">
            <div className="intensity-gradient"></div>
            <div
              className="intensity-marker"
              style={{ left: `${getMarkerPosition(avgSentiment)}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Key Issues */}
      <div className="key-issues">
        <h4 className="issues-title">Key Issues</h4>
        {topIssues.length > 0 ? (
          <ul className="issues-list">
            {topIssues.map((issue, index) => (
              <li key={index} className={`issue-item trending-${issue.trend}`}>
                <span className="issue-text">{issue.issue}</span>
                <span className="issue-icon">{getTrendIcon(issue.trend)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-message">No key issues identified yet.</p>
        )}
      </div>
    </div>
  )
}

export default SummaryCard
