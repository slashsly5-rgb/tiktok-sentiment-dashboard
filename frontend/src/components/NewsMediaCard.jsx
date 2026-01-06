import './Cards.css'

const NewsMediaCard = ({ videos }) => {
  // Helper function to extract topic name from JSON string or return as-is
  const extractTopicName = (topic) => {
    if (!topic) return null

    // If it's already a plain string, return it
    if (typeof topic === 'string' && !topic.startsWith('[') && !topic.startsWith('{')) {
      return topic
    }

    // Try to parse as JSON
    try {
      const parsed = JSON.parse(topic)

      // If it's an array, get the first item's name
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed[0].name || parsed[0]
      }

      // If it's an object with a name property
      if (parsed.name) {
        return parsed.name
      }

      // Otherwise return the original
      return topic
    } catch (e) {
      // If parsing fails, return the original string
      return topic
    }
  }

  // Filter videos that have sentiment analysis with topic and discussion
  const newsItems = videos
    .filter(video => video.topic && video.summary)
    .map(video => ({
      topic: extractTopicName(video.topic),
      discussion: video.summary,
      sentiment: video.sentiment || 'neutral',
      sentimentScore: video.sentiment_score || 0
    }))
    .filter(item => item.topic) // Remove items where topic extraction failed
    .slice(0, 10) // Limit to top 10 items

  const getSentimentColor = (sentiment) => {
    const sentimentLower = sentiment?.toLowerCase() || 'neutral'
    if (sentimentLower.includes('positive')) return 'positive'
    if (sentimentLower.includes('negative')) return 'negative'
    return 'neutral'
  }

  const getSentimentIcon = (sentiment) => {
    const sentimentLower = sentiment?.toLowerCase() || 'neutral'
    if (sentimentLower.includes('positive')) return 'fa-smile'
    if (sentimentLower.includes('negative')) return 'fa-frown'
    return 'fa-meh'
  }

  return (
    <div className="news-media-card fade-in">
      <div className="news-items-container">
        {newsItems.length > 0 ? (
          newsItems.map((item, index) => (
            <div
              key={index}
              className={`news-item sentiment-${getSentimentColor(item.sentiment)}`}
            >
              <div className="news-item-header">
                <i className={`fas ${getSentimentIcon(item.sentiment)} sentiment-icon`}></i>
                <h4 className="news-topic">{item.topic}</h4>
              </div>
              <p className="news-discussion">{item.discussion}</p>

              <div className="news-item-footer">
                <span className={`sentiment-badge ${getSentimentColor(item.sentiment)}`}>
                  {item.sentiment}
                  {item.sentimentScore > 0 && ` (${item.sentimentScore}/10)`}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="no-news-data">
            <i className="fas fa-newspaper" style={{ fontSize: '48px', color: '#95A5A6', marginBottom: '16px' }}></i>
            <p>No news and social media topics available yet.</p>
            <small>Topics will appear here once videos are analyzed.</small>
          </div>
        )}
      </div>

      <div className="map-legend">
        <span className="legend-item">
          <span className="legend-dot positive"></span>
          Positive
        </span>
        <span className="legend-item">
          <span className="legend-dot neutral"></span>
          Neutral
        </span>
        <span className="legend-item">
          <span className="legend-dot negative"></span>
          Negative
        </span>
      </div>

      <div className="map-timestamp">
        Last updated at {new Date().toLocaleString()}
      </div>
    </div>
  )
}

export default NewsMediaCard
