import { useState } from 'react'
import './Cards.css'

const MapCard = ({ regions }) => {
  const [selectedRegion, setSelectedRegion] = useState(null)

  const handleRegionClick = (region) => {
    setSelectedRegion(region)
    alert(`${region.name}: ${region.description}`)
  }

  const mapPaths = {
    kuching: 'M 100,100 L 200,80 L 250,120 L 200,160 Z',
    miri: 'M 250,120 L 350,100 L 400,150 L 350,180 Z',
    sibu: 'M 200,160 L 250,200 L 300,220 L 280,180 Z',
    bintulu: 'M 350,180 L 450,160 L 480,220 L 400,240 Z',
    kapit: 'M 280,180 L 350,180 L 400,240 L 300,260 Z'
  }

  return (
    <div className="map-card fade-in">
      <div className="map-container">
        <svg id="sentiment-map" viewBox="0 0 600 400">
          {regions.map(region => (
            <path
              key={region.id}
              className={`map-region ${region.sentiment}`}
              d={mapPaths[region.id]}
              data-region={region.name}
              onClick={() => handleRegionClick(region)}
            >
              <title>{region.name} - {region.sentiment} Sentiment</title>
            </path>
          ))}
        </svg>
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

export default MapCard
