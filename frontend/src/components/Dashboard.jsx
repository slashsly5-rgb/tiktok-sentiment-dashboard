import SummaryCard from './SummaryCard'
import NewsMediaCard from './NewsMediaCard'
import AnalyticsCard from './AnalyticsCard'
import StatsRow from './StatsRow'
import TimelineSelector from './TimelineSelector'
import VideoList from './VideoList'
import SentimentOverview from './SentimentOverview'
import ConstituentAnalysis from './ConstituentAnalysis'
import './Dashboard.css'

const Dashboard = ({
  data,
  videos,
  loading,
  videosLoading,
  error,
  videosError,
  selectedDays,
  onTimelineChange,
  onRefreshVideos
}) => {
  if (loading) {
    return (
      <main className="main-content">
        <div className="loading-spinner">
          <i className="fas fa-spinner fa-spin"></i> Loading dashboard data...
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="main-content">
        <div className="error-message">
          <i className="fas fa-exclamation-triangle"></i> Error loading data: {error}
          <br />
          <small>Make sure the backend API is running on http://localhost:5000</small>
        </div>
      </main>
    )
  }

  if (!data) {
    return (
      <main className="main-content">
        <div className="error-message">
          <i className="fas fa-exclamation-circle"></i> No data available
        </div>
      </main>
    )
  }

  const dashboardData = data

  return (
    <main className="main-content">
      {/* Timeline Selector */}
      <TimelineSelector
        selectedDays={selectedDays}
        onTimelineChange={onTimelineChange}
      />

      {/* Main Dashboard Sections - Single Row */}
      <div className="dashboard-sections-row">
        {/* Overview of Public Sentiment Section */}
        <div className="dashboard-section">
          <h2 className="section-title">Overview of Public Sentiment</h2>
          <div className="section-cards">
            <SummaryCard
              sentiment={dashboardData.sentiment}
              summary={dashboardData.summary}
              keyIssues={dashboardData.keyIssues}
              videos={videos}
            />
            <SentimentOverview videos={videos} />
          </div>
        </div>

        {/* News and Social Media Section */}
        <div className="dashboard-section">
          <h2 className="section-title">News and Social Media</h2>
          <div className="section-cards">
            <AnalyticsCard analytics={dashboardData.analytics} />
            <NewsMediaCard videos={videos} />
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <StatsRow stats={dashboardData.stats} />

      {/* Video List Section */}
      <div className="video-section">
        <VideoList
          videos={videos}
          loading={videosLoading}
          error={videosError}
          onRefresh={onRefreshVideos}
        />
      </div>
    </main>
  )
}

export default Dashboard
