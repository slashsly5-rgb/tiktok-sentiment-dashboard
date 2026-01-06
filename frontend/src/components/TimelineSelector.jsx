import './TimelineSelector.css'

const TimelineSelector = ({ selectedDays, onTimelineChange }) => {
  const timelineOptions = [
    { label: 'Today', value: 1 },
    { label: '7 Days', value: 7 },
    { label: '30 Days', value: 30 },
    { label: 'All Time', value: 365 }
  ]

  return (
    <div className="timeline-selector">
      <span className="timeline-label">Time Period:</span>
      <div className="timeline-options">
        {timelineOptions.map(option => (
          <button
            key={option.value}
            className={`timeline-btn ${selectedDays === option.value ? 'active' : ''}`}
            onClick={() => onTimelineChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default TimelineSelector
