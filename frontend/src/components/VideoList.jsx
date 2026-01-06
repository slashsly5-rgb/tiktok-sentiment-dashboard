import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import VideoCard from './VideoCard'
import './VideoList.css'

/**
 * VideoList Component
 * Displays a grid of videos with search, filter, and pagination
 */
const VideoList = ({ videos, loading, error, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState('all')
  const [sortBy, setSortBy] = useState('recent')
  const [currentPage, setCurrentPage] = useState(1)
  const videosPerPage = 12

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, sentimentFilter, sortBy])

  // Filter and sort videos
  const getFilteredAndSortedVideos = () => {
    if (!videos || !Array.isArray(videos)) return []

    let filtered = [...videos]

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(
        (video) =>
          video.description?.toLowerCase().includes(term) ||
          video.authorUsername?.toLowerCase().includes(term) ||
          video.hashtags?.some((tag) => tag.toLowerCase().includes(term)) ||
          video.searchKeyword?.toLowerCase().includes(term)
      )
    }

    // Sentiment filter
    if (sentimentFilter !== 'all') {
      filtered = filtered.filter((video) => {
        if (!video.sentiment) return sentimentFilter === 'unanalyzed'
        return video.sentiment.toLowerCase() === sentimentFilter.toLowerCase()
      })
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return new Date(b.scrapedAt) - new Date(a.scrapedAt)
        case 'views':
          return (b.viewsCount || 0) - (a.viewsCount || 0)
        case 'likes':
          return (b.likesCount || 0) - (a.likesCount || 0)
        case 'engagement':
          const engA = ((a.likesCount || 0) + (a.commentsCount || 0) + (a.sharesCount || 0)) / (a.viewsCount || 1)
          const engB = ((b.likesCount || 0) + (b.commentsCount || 0) + (b.sharesCount || 0)) / (b.viewsCount || 1)
          return engB - engA
        default:
          return 0
      }
    })

    return filtered
  }

  const filteredVideos = getFilteredAndSortedVideos()

  // Pagination
  const totalPages = Math.ceil(filteredVideos.length / videosPerPage)
  const startIndex = (currentPage - 1) * videosPerPage
  const endIndex = startIndex + videosPerPage
  const currentVideos = filteredVideos.slice(startIndex, endIndex)

  const handlePageChange = (page) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const getPaginationButtons = () => {
    const buttons = []
    const maxButtons = 5
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2))
    let endPage = Math.min(totalPages, startPage + maxButtons - 1)

    if (endPage - startPage + 1 < maxButtons) {
      startPage = Math.max(1, endPage - maxButtons + 1)
    }

    for (let i = startPage; i <= endPage; i++) {
      buttons.push(i)
    }

    return buttons
  }

  if (error) {
    return (
      <div className="video-list-container">
        <div className="video-list-error">
          <i className="fas fa-exclamation-triangle"></i>
          <h3>Error Loading Videos</h3>
          <p>{error}</p>
          {onRefresh && (
            <button onClick={onRefresh} className="btn-refresh">
              <i className="fas fa-redo"></i>
              Try Again
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="video-list-container">
      <div className="video-list-header">
        <div className="header-title">
          <h2>
            <i className="fas fa-video"></i>
            Recent Videos
          </h2>
          <span className="video-count">
            {filteredVideos.length} video{filteredVideos.length !== 1 ? 's' : ''}
            {searchTerm || sentimentFilter !== 'all' ? ' found' : ' total'}
          </span>
        </div>

        <div className="header-actions">
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="btn-refresh"
              disabled={loading}
            >
              <i className={`fas fa-sync-alt ${loading ? 'fa-spin' : ''}`}></i>
              Refresh
            </button>
          )}
        </div>
      </div>

      <div className="video-list-controls">
        <div className="search-box">
          <i className="fas fa-search"></i>
          <input
            type="text"
            placeholder="Search videos, authors, hashtags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button
              className="clear-search"
              onClick={() => setSearchTerm('')}
            >
              <i className="fas fa-times"></i>
            </button>
          )}
        </div>

        <div className="filter-controls">
          <div className="filter-group">
            <label>
              <i className="fas fa-smile"></i>
              Sentiment:
            </label>
            <select
              value={sentimentFilter}
              onChange={(e) => setSentimentFilter(e.target.value)}
            >
              <option value="all">All Sentiments</option>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
              <option value="very_negative">Very Negative</option>
              <option value="unanalyzed">Not Analyzed</option>
            </select>
          </div>

          <div className="filter-group">
            <label>
              <i className="fas fa-sort"></i>
              Sort by:
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="recent">Most Recent</option>
              <option value="views">Most Views</option>
              <option value="likes">Most Likes</option>
              <option value="engagement">Highest Engagement</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="video-list-loading">
          <div className="spinner"></div>
          <p>Loading videos...</p>
        </div>
      ) : filteredVideos.length === 0 ? (
        <div className="video-list-empty">
          <i className="fas fa-inbox"></i>
          <h3>No Videos Found</h3>
          <p>
            {searchTerm || sentimentFilter !== 'all'
              ? 'Try adjusting your filters or search terms'
              : 'No videos have been scraped yet. Start scraping to see videos here.'}
          </p>
        </div>
      ) : (
        <>
          <div className="video-grid">
            {currentVideos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="pagination-btn"
              >
                <i className="fas fa-chevron-left"></i>
                Previous
              </button>

              <div className="pagination-numbers">
                {currentPage > 3 && (
                  <>
                    <button
                      onClick={() => handlePageChange(1)}
                      className="pagination-number"
                    >
                      1
                    </button>
                    {currentPage > 4 && <span className="pagination-ellipsis">...</span>}
                  </>
                )}

                {getPaginationButtons().map((page) => (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`pagination-number ${page === currentPage ? 'active' : ''}`}
                  >
                    {page}
                  </button>
                ))}

                {currentPage < totalPages - 2 && (
                  <>
                    {currentPage < totalPages - 3 && <span className="pagination-ellipsis">...</span>}
                    <button
                      onClick={() => handlePageChange(totalPages)}
                      className="pagination-number"
                    >
                      {totalPages}
                    </button>
                  </>
                )}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="pagination-btn"
              >
                Next
                <i className="fas fa-chevron-right"></i>
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

VideoList.propTypes = {
  videos: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      tiktokId: PropTypes.string,
      url: PropTypes.string,
      authorUsername: PropTypes.string,
      description: PropTypes.string,
      viewsCount: PropTypes.number,
      likesCount: PropTypes.number,
      commentsCount: PropTypes.number,
      sharesCount: PropTypes.number,
      hashtags: PropTypes.arrayOf(PropTypes.string),
      searchKeyword: PropTypes.string,
      scrapedAt: PropTypes.string,
      sentiment: PropTypes.string,
      sentimentScore: PropTypes.number,
      summary: PropTypes.string,
      keyIssues: PropTypes.arrayOf(PropTypes.string),
    })
  ),
  loading: PropTypes.bool,
  error: PropTypes.string,
  onRefresh: PropTypes.func,
}

VideoList.defaultProps = {
  videos: [],
  loading: false,
  error: null,
  onRefresh: null,
}

export default VideoList
