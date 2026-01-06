import { useEffect, useRef } from 'react'
import { Chart } from 'chart.js/auto'
import './Cards.css'

const AnalyticsCard = ({ analytics }) => {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (chartRef.current) {
      const ctx = chartRef.current.getContext('2d')

      // Destroy existing chart
      if (chartInstance.current) {
        chartInstance.current.destroy()
      }

      // Create new chart
      chartInstance.current = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Positive Comments', 'Negative Comments', 'Neutral Comments'],
          datasets: [{
            data: [
              analytics.sentimentBreakdown.positive,
              analytics.sentimentBreakdown.negative,
              analytics.sentimentBreakdown.neutral
            ],
            backgroundColor: ['#2ECC71', '#E74C3C', '#F39C12'],
            borderWidth: 0,
            hoverOffset: 10
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#2C2C2C',
              titleColor: '#FFFFFF',
              bodyColor: '#FFFFFF',
              borderColor: '#F39C12',
              borderWidth: 2,
              padding: 12
            }
          },
          cutout: '70%'
        }
      })
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy()
      }
    }
  }, [analytics])

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  return (
    <div className="analytics-card fade-in">
      <div className="analytics-header">
        <div className="analytics-image">
          <i className="fas fa-video" style={{ fontSize: '40px', color: '#F39C12' }}></i>
        </div>
        <div className="analytics-meta">
          <h4 className="analytics-title">Reach</h4>
          <p className="analytics-stats">
            {formatNumber(analytics.reach.views)} Views | {formatNumber(analytics.reach.likes)} Likes
          </p>
        </div>
      </div>

      <div className="donut-chart-container">
        <canvas ref={chartRef} width="120" height="120"></canvas>
        <div className="chart-legend">
          <div className="legend-item">
            <span className="legend-color positive"></span>
            <span>{analytics.sentimentBreakdown.positive}% Positive</span>
          </div>
          <div className="legend-item">
            <span className="legend-color negative"></span>
            <span>{analytics.sentimentBreakdown.negative}% Negative</span>
          </div>
          <div className="legend-item">
            <span className="legend-color neutral"></span>
            <span>{analytics.sentimentBreakdown.neutral}% Neutral</span>
          </div>
        </div>
      </div>

      <div className="analytics-summary">
        <h5>Social Media Summary</h5>
        <p>{analytics.summary}</p>
        <button className="read-more-btn">Read More</button>
      </div>
    </div>
  )
}

export default AnalyticsCard
