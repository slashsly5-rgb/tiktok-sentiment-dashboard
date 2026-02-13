import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Input } from './ui/input'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import './SingleVideoAnalysis.css'

/**
 * SingleVideoAnalysis Component
 * Allows users to analyze a single TikTok video by URL
 * Shows step-by-step progress and detailed results
 *
 * Usage:
 * <SingleVideoAnalysis />
 */
const SingleVideoAnalysis = () => {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState([])
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Format numbers for display (1200 -> "1.2K", etc.)
  const formatNumber = (num) => {
    if (!num) return '0'
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  // Get sentiment badge styling
  const getSentimentStyle = (sentiment) => {
    const normalized = sentiment?.toLowerCase()
    switch (normalized) {
      case 'positive':
      case 'very_positive':
        return { variant: 'default', color: '#2ECC71', bg: 'rgba(46, 204, 113, 0.1)' }
      case 'negative':
      case 'very_negative':
        return { variant: 'destructive', color: '#E74C3C', bg: 'rgba(231, 76, 60, 0.1)' }
      case 'neutral':
        return { variant: 'secondary', color: '#F39C12', bg: 'rgba(243, 156, 18, 0.1)' }
      default:
        return { variant: 'outline', color: '#6B6B6B', bg: 'rgba(107, 107, 107, 0.1)' }
    }
  }

  // Get step status icon
  const getStepIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
        return <i className="fas fa-check-circle step-icon success"></i>
      case 'error':
      case 'failed':
        return <i className="fas fa-times-circle step-icon error"></i>
      case 'running':
      case 'in_progress':
        return <i className="fas fa-spinner fa-spin step-icon running"></i>
      case 'skipped':
        return <i className="fas fa-forward step-icon skipped"></i>
      default:
        return <i className="fas fa-circle step-icon pending"></i>
    }
  }

  // Get step status class
  const getStepClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
        return 'success'
      case 'error':
      case 'failed':
        return 'error'
      case 'running':
      case 'in_progress':
        return 'running'
      case 'skipped':
        return 'skipped'
      default:
        return 'pending'
    }
  }

  // Handle video analysis
  const handleAnalyze = async () => {
    if (!url.trim()) {
      setError('Please enter a TikTok URL')
      return
    }

    setLoading(true)
    setError(null)
    setSteps([])
    setResult(null)

    try {
      // Import the API function dynamically
      const { analyzeSingleVideo } = await import('../services/api')

      const response = await analyzeSingleVideo(url)

      if (response.steps) {
        setSteps(response.steps)
      }

      if (response.status === 'completed' && response.video) {
        setResult(response)
      } else if (response.status === 'failed') {
        setError(response.error || 'Analysis failed. Please try again.')
      }
    } catch (err) {
      console.error('Error analyzing video:', err)
      setError(err.message || 'Failed to analyze video. Please check the URL and try again.')
    } finally {
      setLoading(false)
    }
  }

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleAnalyze()
    }
  }

  // Reset to initial state
  const handleReset = () => {
    setUrl('')
    setLoading(false)
    setSteps([])
    setResult(null)
    setError(null)
  }

  return (
    <div className="single-video-analysis">
      {/* URL Input Form */}
      <Card className="analysis-input-card">
        <CardHeader>
          <CardTitle className="analysis-title">
            <i className="fas fa-search"></i>
            Analyze Single Video
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="input-group">
            <Input
              type="text"
              placeholder="Paste a TikTok video URL (e.g., https://www.tiktok.com/@user/video/123456)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              className="url-input"
            />
            <Button
              onClick={handleAnalyze}
              disabled={loading || !url.trim()}
              className="analyze-button"
            >
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  Analyzing...
                </>
              ) : (
                <>
                  <i className="fas fa-play"></i>
                  Analyze
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="error-card">
          <CardContent>
            <div className="error-content">
              <i className="fas fa-exclamation-triangle"></i>
              <div className="error-text">
                <h4>Error</h4>
                <p>{error}</p>
              </div>
              <Button
                onClick={handleReset}
                variant="outline"
                className="try-again-button"
              >
                <i className="fas fa-redo"></i>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step Progress Log */}
      {steps.length > 0 && (
        <Card className="steps-card">
          <CardHeader>
            <CardTitle className="steps-title">
              <i className="fas fa-tasks"></i>
              Processing Steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="steps-timeline">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className={`step-item ${getStepClass(step.status)}`}
                >
                  <div className="step-indicator">
                    <div className="step-number">{step.step}</div>
                    {index < steps.length - 1 && <div className="step-line"></div>}
                  </div>
                  <div className="step-content">
                    <div className="step-header">
                      <div className="step-name">
                        {getStepIcon(step.status)}
                        <span>{step.name}</span>
                      </div>
                      {step.duration && (
                        <span className="step-duration">{step.duration}</span>
                      )}
                    </div>
                    {step.detail && (
                      <div className="step-detail">{step.detail}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Result Card */}
      {result && result.video && (
        <Card className="result-card">
          <CardHeader>
            <CardTitle className="result-title">
              <i className="fas fa-check-circle"></i>
              Analysis Complete
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="result-content">
              {/* Video Metadata */}
              <div className="video-metadata">
                <div className="metadata-header">
                  <div className="author-info">
                    <i className="fas fa-user"></i>
                    <span className="author-username">
                      @{result.video.authorUsername || 'Unknown'}
                    </span>
                  </div>
                  <a
                    href={result.video.url || `https://www.tiktok.com/@${result.video.authorUsername}/video/${result.video.tiktokId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="view-original"
                  >
                    <i className="fas fa-external-link-alt"></i>
                    View Original
                  </a>
                </div>

                {result.video.description && (
                  <p className="video-description">{result.video.description}</p>
                )}

                {/* Stats Grid */}
                <div className="stats-grid">
                  <div className="stat-item">
                    <i className="fas fa-eye"></i>
                    <div className="stat-content">
                      <span className="stat-value">
                        {formatNumber(result.video.viewsCount)}
                      </span>
                      <span className="stat-label">Views</span>
                    </div>
                  </div>
                  <div className="stat-item">
                    <i className="fas fa-heart"></i>
                    <div className="stat-content">
                      <span className="stat-value">
                        {formatNumber(result.video.likesCount)}
                      </span>
                      <span className="stat-label">Likes</span>
                    </div>
                  </div>
                  <div className="stat-item">
                    <i className="fas fa-comment"></i>
                    <div className="stat-content">
                      <span className="stat-value">
                        {formatNumber(result.video.commentsCount)}
                      </span>
                      <span className="stat-label">Comments</span>
                    </div>
                  </div>
                  <div className="stat-item">
                    <i className="fas fa-share"></i>
                    <div className="stat-content">
                      <span className="stat-value">
                        {formatNumber(result.video.sharesCount)}
                      </span>
                      <span className="stat-label">Shares</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sentiment Analysis */}
              {result.video.sentiment && (
                <div className="sentiment-section">
                  <h3 className="section-heading">
                    <i className="fas fa-chart-line"></i>
                    Sentiment Analysis
                  </h3>

                  <div className="sentiment-overview">
                    <div className="sentiment-badge-wrapper">
                      <Badge
                        className="sentiment-badge"
                        style={{
                          backgroundColor: getSentimentStyle(result.video.sentiment.sentiment).bg,
                          color: getSentimentStyle(result.video.sentiment.sentiment).color,
                          border: `1px solid ${getSentimentStyle(result.video.sentiment.sentiment).color}`,
                        }}
                      >
                        {result.video.sentiment.sentiment?.replace('_', ' ').toUpperCase()}
                      </Badge>
                      {result.video.sentiment.sentimentScore !== undefined && (
                        <div className="sentiment-score">
                          <span className="score-label">Score:</span>
                          <div className="score-bar">
                            <div
                              className="score-fill"
                              style={{
                                width: `${(result.video.sentiment.sentimentScore / 10) * 100}%`,
                                backgroundColor: getSentimentStyle(result.video.sentiment.sentiment).color,
                              }}
                            ></div>
                          </div>
                          <span className="score-value">
                            {result.video.sentiment.sentimentScore}/10
                          </span>
                        </div>
                      )}
                    </div>

                    {result.video.sentiment.summary && (
                      <p className="sentiment-summary">{result.video.sentiment.summary}</p>
                    )}
                  </div>

                  {/* Key Issues */}
                  {result.video.sentiment.keyIssues && result.video.sentiment.keyIssues.length > 0 && (
                    <div className="key-issues">
                      <h4 className="subsection-heading">
                        <i className="fas fa-exclamation-circle"></i>
                        Key Issues
                      </h4>
                      <div className="issues-tags">
                        {result.video.sentiment.keyIssues.map((issue, index) => (
                          <span key={index} className="issue-tag">
                            {issue}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Discussion Points */}
                  {result.video.sentiment.discussionPoints && (
                    <div className="discussion-points">
                      <h4 className="subsection-heading">
                        <i className="fas fa-comments"></i>
                        Discussion Points
                      </h4>
                      <p className="discussion-text">
                        {result.video.sentiment.discussionPoints}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="result-actions">
                <Button
                  onClick={handleReset}
                  variant="outline"
                  className="analyze-another-button"
                >
                  <i className="fas fa-plus"></i>
                  Analyze Another Video
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default SingleVideoAnalysis
