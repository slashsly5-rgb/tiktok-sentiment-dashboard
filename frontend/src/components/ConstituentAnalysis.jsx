import { useMemo } from 'react'
import './Cards.css'

// Helper functions
const getDominantSentiment = (sentiments) => {
  const counts = sentiments.reduce((acc, s) => {
    acc[s] = (acc[s] || 0) + 1
    return acc
  }, {})
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral'
}

const getSentimentColor = (sentiment) => {
  if (!sentiment) return '#95A5A6'
  if (sentiment.includes('positive')) return '#2ECC71'
  if (sentiment === 'very_negative') return '#C0392B'
  if (sentiment.includes('negative')) return '#E74C3C'
  return '#95A5A6'
}

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const ConstituentAnalysis = ({ videos }) => {
  const constituentData = useMemo(() => {
    if (!videos || videos.length === 0) {
      return {
        byAuthor: [],
        keyIssues: [],
        totalIssues: 0
      }
    }

    // Filter videos with sentiment data
    const analyzed = videos.filter(v => v.sentiment)

    // Group by author
    const authorMap = {}
    analyzed.forEach(v => {
      const author = v.authorUsername || 'Unknown'
      if (!authorMap[author]) {
        authorMap[author] = {
          videos: 0,
          sentiments: [],
          totalViews: 0,
          totalLikes: 0
        }
      }
      authorMap[author].videos++
      authorMap[author].sentiments.push(v.sentiment)
      authorMap[author].totalViews += v.viewsCount || 0
      authorMap[author].totalLikes += v.likesCount || 0
    })

    const byAuthor = Object.entries(authorMap)
      .map(([author, data]) => ({
        author,
        videos: data.videos,
        totalViews: data.totalViews,
        totalLikes: data.totalLikes,
        dominantSentiment: getDominantSentiment(data.sentiments)
      }))
      .sort((a, b) => b.videos - a.videos)
      .slice(0, 5)

    // Collect all key issues
    const allIssues = []
    analyzed.forEach(v => {
      if (v.keyIssues && Array.isArray(v.keyIssues)) {
        v.keyIssues.forEach(issue => {
          if (issue && issue.title) {
            allIssues.push({
              title: issue.title,
              description: issue.description,
              evidence: issue.evidence || [],
              author: v.authorUsername
            })
          }
        })
      }
    })

    return {
      byAuthor,
      keyIssues: allIssues.slice(0, 5),
      totalIssues: allIssues.length
    }
  }, [videos])

  if (constituentData.byAuthor.length === 0) {
    return (
      <div className="constituent-analysis-card fade-in">
        <h4 className="card-subtitle">Constituent Analysis</h4>
        <p className="empty-message">No analyzed data available yet.</p>
      </div>
    )
  }

  return (
    <div className="constituent-analysis-card fade-in">
      <h4 className="card-subtitle">Sentiment by Content Creators</h4>

      {/* Top authors by sentiment */}
      <div className="authors-section">
        <h5 className="section-title">Top Creators Analyzed</h5>
        <div className="authors-list">
          {constituentData.byAuthor.map((author, idx) => (
            <div key={idx} className="author-item">
              <div className="author-info">
                <div className="author-name">@{author.author}</div>
                <div className="author-stats">
                  {author.videos} video{author.videos > 1 ? 's' : ''} •{' '}
                  {formatNumber(author.totalViews)} views
                </div>
              </div>
              <div
                className="author-sentiment-badge"
                style={{ backgroundColor: getSentimentColor(author.dominantSentiment) }}
              >
                {author.dominantSentiment?.replace('_', ' ').toUpperCase()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key issues raised */}
      {constituentData.keyIssues.length > 0 && (
        <div className="issues-section">
          <h5 className="section-title">
            Key Issues Identified ({constituentData.totalIssues} total)
          </h5>
          <div className="issues-list">
            {constituentData.keyIssues.map((issue, idx) => (
              <div key={idx} className="issue-card">
                <div className="issue-header">
                  <div className="issue-title">{issue.title}</div>
                  <div className="issue-author">by @{issue.author}</div>
                </div>
                <div className="issue-description">{issue.description}</div>
                {issue.evidence && issue.evidence.length > 0 && (
                  <div className="issue-evidence">
                    <div className="evidence-label">Evidence:</div>
                    <div className="evidence-quote">"{issue.evidence[0]}"</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ConstituentAnalysis
