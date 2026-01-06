import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import ChatInterface from './components/ChatInterface'
import AssistantPage from './pages/AssistantPage'
import { fetchDashboardData, fetchVideosWithSentiment } from './services/api'
import './App.css'

function App() {
  const [dashboardData, setDashboardData] = useState(null)
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [videosLoading, setVideosLoading] = useState(true)
  const [error, setError] = useState(null)
  const [videosError, setVideosError] = useState(null)
  const [selectedDays, setSelectedDays] = useState(30) // Default to 30 days

  // Load dashboard data when timeline changes
  useEffect(() => {
    loadDashboardData()
    loadVideos()
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => {
      loadDashboardData()
      loadVideos()
    }, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [selectedDays])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const data = await fetchDashboardData(selectedDays)
      setDashboardData(data)
      setError(null)
    } catch (err) {
      console.error('Error loading dashboard data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadVideos = async () => {
    try {
      setVideosLoading(true)
      const data = await fetchVideosWithSentiment(selectedDays, 100) // Fetch up to 100 videos
      setVideos(data.videos)
      setVideosError(null)
    } catch (err) {
      console.error('Error loading videos:', err)
      setVideosError(err.message)
    } finally {
      setVideosLoading(false)
    }
  }

  const handleTimelineChange = (days) => {
    setSelectedDays(days)
  }

  // Build filters object for chat context
  const chatFilters = {
    days: selectedDays
    // Can add: keywords: [...], sentiment: "positive", etc.
  }

  return (
    <Router>
      <div className="app">
        <Sidebar />

        <Routes>
          <Route path="/" element={
            <>
              <Dashboard
                data={dashboardData}
                videos={videos}
                loading={loading}
                videosLoading={videosLoading}
                error={error}
                videosError={videosError}
                selectedDays={selectedDays}
                onTimelineChange={handleTimelineChange}
                onRefreshVideos={loadVideos}
              />
              <ChatInterface filters={chatFilters} />
            </>
          } />

          <Route path="/assistant" element={
            <AssistantPage filters={chatFilters} />
          } />
        </Routes>
      </div>
    </Router>
  )
}

export default App
