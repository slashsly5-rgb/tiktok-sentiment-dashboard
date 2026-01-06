import './Cards.css'

const StatsRow = ({ stats }) => {
  const statsData = [
    {
      icon: 'fa-thumbs-up',
      iconClass: 'positive',
      value: stats.totalVideos.toLocaleString(),
      label: 'Total Videos Analyzed'
    },
    {
      icon: 'fa-chart-pie',
      iconClass: 'neutral',
      value: `${stats.positiveSentiment}%`,
      label: 'Positive Sentiment'
    },
    {
      icon: 'fa-fire',
      iconClass: 'accent',
      value: stats.trendingTopics,
      label: 'Trending Topics'
    },
    {
      icon: 'fa-exclamation-triangle',
      iconClass: 'negative',
      value: stats.criticalIssues,
      label: 'Critical Issues'
    }
  ]

  return (
    <div className="stats-row">
      {statsData.map((stat, index) => (
        <div key={index} className="stat-card fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
          <div className={`stat-icon ${stat.iconClass}`}>
            <i className={`fas ${stat.icon}`}></i>
          </div>
          <div className="stat-content">
            <h3 className="stat-value">{stat.value}</h3>
            <p className="stat-label">{stat.label}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StatsRow
