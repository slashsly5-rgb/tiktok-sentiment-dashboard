# UI Implementation Plan - TikTok Political Sentiment Dashboard

## Overview
This document provides a complete color scheme, component breakdown, and HTML/CSS implementation guide based on the Project S dashboard design.

---

## 🎨 Color Palette

### CSS Variables Setup
```css
:root {
  /* Primary Colors */
  --bg-cream: #F5F1E8;
  --bg-white: #FFFFFF;
  --sidebar-dark: #2C2C2C;
  --text-primary: #1A1A1A;
  --text-secondary: #6B6B6B;

  /* Sentiment Colors */
  --sentiment-positive: #2ECC71;
  --sentiment-negative: #E74C3C;
  --sentiment-neutral: #95A5A6;

  /* Accent Colors */
  --accent-warning: #E67E22;
  --accent-yellow: #F39C12;
  --accent-blue: #3498DB;

  /* UI Elements */
  --border-color: #E8E4DC;
  --hover-bg: #EBEBEB;
  --shadow: rgba(0, 0, 0, 0.1);
  --shadow-lg: rgba(0, 0, 0, 0.15);

  /* Gradients */
  --gradient-map: linear-gradient(135deg, #2ECC71 0%, #F39C12 50%, #E74C3C 100%);
}
```

### Color Usage Guide

| Color | Usage | Hex Code |
|-------|-------|----------|
| Cream | Main background, neutral areas | `#F5F1E8` |
| White | Cards, content containers | `#FFFFFF` |
| Dark Charcoal | Sidebar, headers | `#2C2C2C` |
| Green | Positive sentiment, success states | `#2ECC71` |
| Red | Negative sentiment, warnings | `#E74C3C` |
| Gray | Neutral sentiment, disabled states | `#95A5A6` |
| Orange | Cost indicators, moderate warnings | `#E67E22` |
| Yellow | Map highlights, active states | `#F39C12` |
| Blue | Links, interactive elements | `#3498DB` |

---

## 🏗️ Layout Structure

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project S - Political Sentiment Dashboard</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Sidebar Navigation -->
  <aside class="sidebar">
    <!-- Navigation items -->
  </aside>

  <!-- Main Content Area -->
  <main class="main-content">
    <!-- Dashboard Header -->
    <header class="dashboard-header">
      <!-- Three-column layout -->
    </header>

    <!-- Dashboard Grid -->
    <div class="dashboard-grid">
      <!-- Cards and visualizations -->
    </div>

    <!-- Chat Interface -->
    <section class="chat-interface">
      <!-- AI assistant chat -->
    </section>
  </main>
</body>
</html>
```

### CSS Grid Layout
```css
body {
  display: flex;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: var(--bg-cream);
  color: var(--text-primary);
}

.sidebar {
  width: 80px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  background-color: var(--sidebar-dark);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  z-index: 1000;
}

.main-content {
  margin-left: 80px;
  width: calc(100% - 80px);
  min-height: 100vh;
  padding: 40px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 24px;
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 🧩 Component Library

### 1. Sidebar Navigation

**HTML:**
```html
<aside class="sidebar">
  <div class="sidebar-logo">
    <img src="logo.svg" alt="BUMI Logo">
  </div>

  <nav class="sidebar-nav">
    <a href="#" class="nav-item active">
      <svg class="nav-icon"><!-- Home icon --></svg>
      <span class="nav-label">Home</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon"><!-- Assistant icon --></svg>
      <span class="nav-label">Assistant</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon"><!-- Analytics icon --></svg>
      <span class="nav-label">Analytics</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon"><!-- News icon --></svg>
      <span class="nav-label">News</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon"><!-- Settings icon --></svg>
      <span class="nav-label">Settings</span>
    </a>
  </nav>

  <div class="sidebar-user">
    <img src="user-avatar.jpg" alt="User" class="user-avatar">
    <span class="user-version">Ver 1.1</span>
  </div>
</aside>
```

**CSS:**
```css
.sidebar {
  background: linear-gradient(180deg, #2C2C2C 0%, #1A1A1A 100%);
}

.sidebar-logo {
  margin-bottom: 40px;
}

.sidebar-logo img {
  width: 40px;
  height: auto;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  text-decoration: none;
  color: #A0A0A0;
  transition: all 0.3s ease;
  position: relative;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: #FFFFFF;
}

.nav-item.active {
  color: var(--accent-yellow);
  background-color: rgba(243, 156, 18, 0.1);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--accent-yellow);
}

.nav-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
}

.nav-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-user {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid var(--accent-yellow);
}

.user-version {
  font-size: 9px;
  color: #6B6B6B;
}
```

---

### 2. Dashboard Header

**HTML:**
```html
<header class="dashboard-header">
  <div class="header-section">
    <h2 class="section-title">Overview of Public Sentiment</h2>
  </div>
  <div class="header-section">
    <h2 class="section-title">Public Sentiment by Constituents</h2>
  </div>
  <div class="header-section">
    <h2 class="section-title">News and Social Media</h2>
  </div>
</header>
```

**CSS:**
```css
.dashboard-header {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--border-color);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

---

### 3. Summary Card

**HTML:**
```html
<div class="summary-card">
  <!-- Sentiment Indicator -->
  <div class="sentiment-badge positive">
    Moderately Positive
  </div>

  <h3 class="card-title">Briefing Summary</h3>

  <p class="card-description">
    Public sentiment is moderately positive, driven by infrastructure
    improvements, with concerns emerging around cost of living in
    urban areas.
  </p>

  <div class="key-issues">
    <h4 class="issues-title">Key Issues</h4>
    <ul class="issues-list">
      <li class="issue-item trending-up">
        <span class="issue-icon">↑</span>
        <span>Cost of Living</span>
      </li>
      <li class="issue-item trending-down">
        <span class="issue-icon">↓</span>
        <span>Road Conditions</span>
      </li>
      <li class="issue-item trending-up">
        <span class="issue-icon">↑</span>
        <span>Employment</span>
      </li>
      <li class="issue-item neutral">
        <span class="issue-icon">→</span>
        <span>Healthcare</span>
      </li>
      <li class="issue-item trending-down">
        <span class="issue-icon">↓</span>
        <span>Public Safety</span>
      </li>
    </ul>
  </div>
</div>
```

**CSS:**
```css
.summary-card {
  background-color: var(--bg-white);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--shadow);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px var(--shadow-lg);
}

.sentiment-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
}

.sentiment-badge::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.sentiment-badge.positive {
  background-color: rgba(46, 204, 113, 0.1);
  color: var(--sentiment-positive);
}

.sentiment-badge.positive::before {
  background-color: var(--sentiment-positive);
}

.sentiment-badge.negative {
  background-color: rgba(231, 76, 60, 0.1);
  color: var(--sentiment-negative);
}

.sentiment-badge.negative::before {
  background-color: var(--sentiment-negative);
}

.sentiment-badge.neutral {
  background-color: rgba(149, 165, 166, 0.1);
  color: var(--sentiment-neutral);
}

.sentiment-badge.neutral::before {
  background-color: var(--sentiment-neutral);
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.card-description {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

.key-issues {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.issues-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.issues-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.issue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  font-size: 14px;
}

.issue-icon {
  font-weight: 700;
  font-size: 16px;
}

.issue-item.trending-up .issue-icon {
  color: var(--sentiment-negative);
}

.issue-item.trending-down .issue-icon {
  color: var(--sentiment-positive);
}

.issue-item.neutral .issue-icon {
  color: var(--sentiment-neutral);
}
```

---

### 4. Map Visualization Card

**HTML:**
```html
<div class="map-card">
  <div class="map-container">
    <svg id="sentiment-map" viewBox="0 0 600 400">
      <!-- SVG map with regions -->
      <path class="map-region positive" d="..." data-region="Kuching"></path>
      <path class="map-region neutral" d="..." data-region="Miri"></path>
      <path class="map-region negative" d="..." data-region="Kapit"></path>
    </svg>
  </div>

  <div class="map-legend">
    <span class="legend-item">
      <span class="legend-dot positive"></span>
      Positive
    </span>
    <span class="legend-item">
      <span class="legend-dot neutral"></span>
      Neutral
    </span>
    <span class="legend-item">
      <span class="legend-dot negative"></span>
      Negative
    </span>
  </div>

  <div class="map-timestamp">
    Last updated at 22/10/25 at 14:30
  </div>

  <div class="map-hotspots">
    <h4 class="hotspots-title">Hotspots</h4>
    <ul class="hotspots-list">
      <li><strong>Kuching:</strong> Improving sentiment on infrastructure</li>
      <li><strong>Miri:</strong> Rising concern over cost of living</li>
      <li><strong>Kapit:</strong> Neutral, low engagement</li>
    </ul>
  </div>
</div>
```

**CSS:**
```css
.map-card {
  background-color: var(--bg-white);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--shadow);
}

.map-container {
  width: 100%;
  height: 300px;
  margin-bottom: 16px;
}

#sentiment-map {
  width: 100%;
  height: 100%;
}

.map-region {
  fill: var(--sentiment-neutral);
  stroke: var(--bg-white);
  stroke-width: 2;
  transition: all 0.3s ease;
  cursor: pointer;
}

.map-region:hover {
  opacity: 0.8;
  stroke-width: 3;
}

.map-region.positive {
  fill: var(--sentiment-positive);
}

.map-region.negative {
  fill: var(--sentiment-negative);
}

.map-region.neutral {
  fill: var(--accent-warning);
}

.map-legend {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.positive {
  background-color: var(--sentiment-positive);
}

.legend-dot.neutral {
  background-color: var(--accent-warning);
}

.legend-dot.negative {
  background-color: var(--sentiment-negative);
}

.map-timestamp {
  font-size: 11px;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 16px;
}

.hotspots-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.hotspots-list {
  list-style: disc;
  padding-left: 20px;
  margin: 0;
}

.hotspots-list li {
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-secondary);
}
```

---

### 5. Analytics Card with Donut Chart

**HTML:**
```html
<div class="analytics-card">
  <div class="analytics-header">
    <img src="news-thumbnail.jpg" alt="News" class="analytics-image">
    <div class="analytics-meta">
      <h4 class="analytics-title">Reach</h4>
      <p class="analytics-stats">144K Views | 89.7K Likes</p>
    </div>
  </div>

  <div class="donut-chart-container">
    <canvas id="sentimentChart" width="200" height="200"></canvas>
    <div class="chart-legend">
      <div class="legend-item">
        <span class="legend-color positive"></span>
        <span>45% POSITIVE COMMENTS</span>
      </div>
      <div class="legend-item">
        <span class="legend-color negative"></span>
        <span>33% NEGATIVE COMMENTS</span>
      </div>
      <div class="legend-item">
        <span class="legend-color neutral"></span>
        <span>30% NEUTRAL COMMENTS</span>
      </div>
    </div>
  </div>

  <div class="analytics-summary">
    <h5>Social Media Summary</h5>
    <p>
      Content related to urban development has generated strong engagement
      and favourable perceptions of leadership and experience...
    </p>
    <button class="read-more-btn">Read More</button>
  </div>
</div>
```

**CSS:**
```css
.analytics-card {
  background-color: var(--bg-white);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--shadow);
}

.analytics-header {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.analytics-image {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
}

.analytics-meta {
  flex: 1;
}

.analytics-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.analytics-stats {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.donut-chart-container {
  margin-bottom: 20px;
}

.chart-legend {
  margin-top: 16px;
}

.chart-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.legend-color.positive {
  background-color: var(--sentiment-positive);
}

.legend-color.negative {
  background-color: var(--sentiment-negative);
}

.legend-color.neutral {
  background-color: var(--sentiment-neutral);
}

.analytics-summary h5 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.analytics-summary p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
}

.read-more-btn {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.read-more-btn:hover {
  color: #2980b9;
}
```

---

### 6. Chat Interface

**HTML:**
```html
<section class="chat-interface">
  <div class="chat-container">
    <div class="chat-welcome">
      <h3>Welcome, YB Dennis Ngau. How may I help you today?</h3>
    </div>

    <div class="chat-input-wrapper">
      <button class="chat-add-btn">
        <svg><!-- Plus icon --></svg>
      </button>
      <input
        type="text"
        class="chat-input"
        placeholder="Ask BUMI"
      >
      <button class="chat-voice-btn">
        <svg><!-- Microphone icon --></svg>
      </button>
    </div>

    <div class="chat-suggestions">
      <button class="suggestion-chip">
        Why is cost of living trending up?
      </button>
      <button class="suggestion-chip">
        Summarise sentiment in Miri
      </button>
    </div>
  </div>
</section>
```

**CSS:**
```css
.chat-interface {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 800px;
  z-index: 100;
}

.chat-container {
  background-color: var(--bg-white);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px var(--shadow-lg);
}

.chat-welcome {
  text-align: center;
  margin-bottom: 20px;
}

.chat-welcome h3 {
  font-size: 18px;
  font-weight: 400;
  color: var(--text-primary);
  margin: 0;
}

.chat-input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: var(--bg-cream);
  border-radius: 12px;
  margin-bottom: 16px;
}

.chat-add-btn,
.chat-voice-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.3s ease;
}

.chat-add-btn:hover,
.chat-voice-btn:hover {
  background-color: var(--hover-bg);
}

.chat-add-btn svg,
.chat-voice-btn svg {
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: var(--text-primary);
  outline: none;
}

.chat-input::placeholder {
  color: var(--text-secondary);
}

.chat-suggestions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.suggestion-chip {
  padding: 8px 16px;
  background-color: var(--bg-cream);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-chip:hover {
  background-color: var(--hover-bg);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}
```

---

## 📊 Chart Implementation

### Donut Chart (using Chart.js)

**JavaScript:**
```javascript
// Include Chart.js library
// <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

const ctx = document.getElementById('sentimentChart').getContext('2d');
const sentimentChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['Positive', 'Negative', 'Neutral'],
    datasets: [{
      data: [45, 33, 30],
      backgroundColor: [
        '#2ECC71', // Positive
        '#E74C3C', // Negative
        '#95A5A6'  // Neutral
      ],
      borderWidth: 0,
      hoverOffset: 10
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: '#2C2C2C',
        titleColor: '#FFFFFF',
        bodyColor: '#FFFFFF',
        borderColor: '#F39C12',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: function(context) {
            return context.label + ': ' + context.parsed + '%';
          }
        }
      }
    },
    cutout: '70%'
  }
});
```

---

## 🎯 Interactive States

### Hover Effects
```css
/* Card hover effect */
.summary-card,
.map-card,
.analytics-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.summary-card:hover,
.map-card:hover,
.analytics-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px var(--shadow-lg);
}

/* Button hover effect */
button {
  transition: all 0.3s ease;
}

button:hover {
  transform: scale(1.05);
}

button:active {
  transform: scale(0.95);
}
```

### Loading States
```css
.loading-skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-cream) 0%,
    var(--hover-bg) 50%,
    var(--bg-cream) 100%
  );
  background-size: 200% 100%;
  animation: loading 1.5s ease-in-out infinite;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```

---

## 📱 Responsive Design

### Breakpoints
```css
/* Desktop (default) - 1200px+ */
.dashboard-grid {
  grid-template-columns: repeat(3, 1fr);
}

/* Tablet - 768px to 1199px */
@media (max-width: 1199px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dashboard-header {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

/* Mobile - 767px and below */
@media (max-width: 767px) {
  .sidebar {
    width: 60px;
  }

  .main-content {
    margin-left: 60px;
    width: calc(100% - 60px);
    padding: 20px;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .nav-label {
    display: none;
  }

  .chat-interface {
    width: 95%;
    bottom: 20px;
  }
}
```

---

## 🔧 Integration with Streamlit

### Streamlit Custom CSS
```python
import streamlit as st

# Custom CSS injection
def load_custom_css():
    st.markdown("""
    <style>
        /* Import color variables */
        :root {
            --bg-cream: #F5F1E8;
            --sentiment-positive: #2ECC71;
            --sentiment-negative: #E74C3C;
            --sentiment-neutral: #95A5A6;
        }

        /* Override Streamlit defaults */
        .stApp {
            background-color: var(--bg-cream);
        }

        /* Custom card styling */
        .element-container {
            background-color: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* Custom metric styling */
        [data-testid="stMetricValue"] {
            font-size: 32px;
            font-weight: 700;
        }
    </style>
    """, unsafe_allow_html=True)

# Apply custom CSS
load_custom_css()
```

### Component Wrappers
```python
def render_sentiment_badge(sentiment: str):
    """Render colored sentiment badge"""
    colors = {
        "Positive": "#2ECC71",
        "Negative": "#E74C3C",
        "Neutral": "#95A5A6"
    }

    st.markdown(f"""
    <div style="
        background-color: {colors.get(sentiment, '#95A5A6')}20;
        color: {colors.get(sentiment, '#95A5A6')};
        padding: 8px 16px;
        border-radius: 4px;
        border-left: 4px solid {colors.get(sentiment, '#95A5A6')};
        font-weight: 600;
        display: inline-block;
    ">
        {sentiment}
    </div>
    """, unsafe_allow_html=True)

def render_summary_card(title: str, content: str, sentiment: str):
    """Render summary card with sentiment"""
    st.markdown(f"""
    <div class="summary-card">
        {render_sentiment_badge(sentiment)}
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)
```

---

## 🚀 Performance Optimization

### CSS Best Practices
```css
/* Use CSS variables for theming */
:root {
  /* Define once, use everywhere */
}

/* Minimize repaints with transform */
.card:hover {
  transform: translateY(-4px); /* Better than top: -4px */
}

/* Use will-change for animations */
.animated-element {
  will-change: transform, opacity;
}

/* Optimize box-shadow with compositing */
.shadow-element {
  transform: translateZ(0); /* Force GPU acceleration */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### JavaScript Optimization
```javascript
// Debounce search input
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const handleSearch = debounce((query) => {
  // Search logic here
}, 300);
```

---

## ✅ Implementation Checklist

### Phase 1: Foundation
- [ ] Set up HTML structure
- [ ] Define CSS variables
- [ ] Create base layout (sidebar + main content)
- [ ] Implement responsive grid system

### Phase 2: Components
- [ ] Build sidebar navigation
- [ ] Create dashboard header
- [ ] Implement summary cards
- [ ] Build map visualization
- [ ] Create analytics cards
- [ ] Implement chat interface

### Phase 3: Interactivity
- [ ] Add hover states
- [ ] Implement chart.js for donut charts
- [ ] Add loading states
- [ ] Create form validation

### Phase 4: Integration
- [ ] Connect to Streamlit backend
- [ ] Fetch data from Supabase
- [ ] Implement real-time updates
- [ ] Add error handling

### Phase 5: Polish
- [ ] Test responsive design
- [ ] Optimize performance
- [ ] Add animations
- [ ] Cross-browser testing
- [ ] Accessibility audit (ARIA labels, keyboard navigation)

---

## 📚 Required Libraries

### CSS Framework (Optional)
- **Tailwind CSS** - For utility-first styling (alternative approach)
- **Bootstrap** - For grid system (if needed)

### JavaScript Libraries
```html
<!-- Chart.js for visualizations -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<!-- Optional: Iconography -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<!-- Optional: Map library (if not using custom SVG) -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### Python (Streamlit)
```txt
streamlit==1.29.0
plotly==5.18.0
pandas==2.1.4
```

---

## 🎨 Design System Summary

### Typography
- **Headings**: System font stack (San Francisco, Segoe UI, Roboto)
- **Body**: 14px base size, 1.6 line-height
- **Weights**: 400 (regular), 600 (semibold), 700 (bold)

### Spacing Scale
- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **2xl**: 40px

### Border Radius
- **sm**: 4px (badges)
- **md**: 8px (buttons)
- **lg**: 12px (cards)
- **xl**: 16px (modals)
- **full**: 50% (avatars)

### Shadows
- **sm**: `0 1px 3px rgba(0, 0, 0, 0.1)`
- **md**: `0 2px 8px rgba(0, 0, 0, 0.1)`
- **lg**: `0 8px 24px rgba(0, 0, 0, 0.15)`
- **xl**: `0 16px 48px rgba(0, 0, 0, 0.2)`

---

## 🔗 Next Steps

1. **Create HTML Template**: Use the structure above as base
2. **Style Components**: Implement CSS for each component
3. **Add Interactivity**: Wire up JavaScript for charts and interactions
4. **Integrate with Backend**: Connect to Flask API and Supabase
5. **Test & Refine**: Cross-browser testing and responsive checks

---

## 📝 Notes

- All colors extracted from the screenshot are approximate
- Component structure mirrors the Project S design
- Responsive breakpoints follow industry standards
- Accessibility features should be added (ARIA labels, focus states)
- Consider dark mode implementation for future enhancement

---

**Document Version**: 1.0
**Last Updated**: 2025-12-26
**Author**: Claude Code Implementation Assistant
