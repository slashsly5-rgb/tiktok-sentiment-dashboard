# Project S - UI Implementation Guide

## 📁 Frontend Assets Structure

```
frontend/
├── index.html              # Main HTML dashboard template
├── css/
│   └── styles.css         # Complete stylesheet with all components
├── js/
│   └── app.js             # JavaScript for charts and interactivity
├── images/                # (Create as needed) Image assets
└── README.md             # This file
```

## 🎨 UI Components Overview

### 1. **Standalone HTML Dashboard** (`index.html`)
A complete, standalone HTML version of the Project S dashboard with:
- Sidebar navigation
- Three-column dashboard layout
- Summary cards with sentiment badges
- Interactive map visualization
- Analytics cards with donut charts
- Stats row with metrics
- AI chat interface

**To Use:**
```bash
# Simply open in browser
start frontend/index.html

# Or serve with Python
cd frontend
python -m http.server 8000
# Visit http://localhost:8000
```

### 2. **Streamlit Dashboard** (`backend/app.py`)
The main Streamlit application with integrated custom styling:
- Uses the same color scheme as the HTML version
- Connects to Supabase database for real-time data
- Custom CSS injected for consistent UI/UX
- Card-based layout with hover effects
- Sentiment badges and color-coded metrics

**To Use:**
```bash
# Run Streamlit app
streamlit run backend/app.py
# Visit http://localhost:8501
```

## 🎨 Color Scheme Reference

| Purpose | Color | Hex Code | Usage |
|---------|-------|----------|-------|
| **Background** | Cream | `#F5F1E8` | Main page background |
| **Cards** | White | `#FFFFFF` | Content containers |
| **Sidebar** | Dark Charcoal | `#2C2C2C` | Navigation sidebar |
| **Text Primary** | Very Dark Gray | `#1A1A1A` | Headlines, important text |
| **Text Secondary** | Medium Gray | `#6B6B6B` | Body text, labels |
| **Positive** | Green | `#2ECC71` | Positive sentiment |
| **Negative** | Red | `#E74C3C` | Negative sentiment |
| **Neutral** | Gray | `#95A5A6` | Neutral sentiment |
| **Warning** | Orange | `#E67E22` | Warnings, alerts |
| **Accent Yellow** | Orange-Yellow | `#F39C12` | Highlights, active states |
| **Accent Blue** | Blue | `#3498DB` | Links, CTAs |

## 📊 Chart Implementation

### Donut Chart (Chart.js)
The sentiment breakdown donut chart is implemented using Chart.js:

**Features:**
- 70% cutout for donut effect
- Custom colors matching sentiment palette
- Interactive tooltips
- Smooth animations
- No legend (uses custom legend below chart)

**Example Data:**
```javascript
{
  labels: ['Positive Comments', 'Negative Comments', 'Neutral Comments'],
  data: [45, 33, 22],
  colors: ['#2ECC71', '#E74C3C', '#95A5A6']
}
```

### Map Visualization (SVG)
Interactive SVG map of Sarawak regions:

**Features:**
- Color-coded by sentiment (Green/Orange/Red)
- Hover effects with brightness and shadow
- Click events for detailed region view
- Tooltips with region names
- Responsive scaling

## 🧩 Component Library

### Sentiment Badge
```html
<div class="sentiment-badge positive">Moderately Positive</div>
<div class="sentiment-badge negative">Negative</div>
<div class="sentiment-badge neutral">Neutral</div>
```

### Summary Card
```html
<div class="summary-card">
  <div class="sentiment-badge positive">Moderately Positive</div>
  <h3 class="card-title">Briefing Summary</h3>
  <p class="card-description">Your description text here...</p>
</div>
```

### Stat Card
```html
<div class="stat-card">
  <div class="stat-icon positive">
    <i class="fas fa-thumbs-up"></i>
  </div>
  <div class="stat-content">
    <h3 class="stat-value">1,247</h3>
    <p class="stat-label">Total Videos Analyzed</p>
  </div>
</div>
```

### Chat Interface
```html
<section class="chat-interface">
  <div class="chat-container">
    <div class="chat-welcome">
      <h3>Welcome, User. How may I help you today?</h3>
    </div>
    <div class="chat-input-wrapper">
      <input type="text" class="chat-input" placeholder="Ask BUMI">
    </div>
  </div>
</section>
```

## 🔧 Integration Options

### Option 1: Standalone HTML (Demo/Prototype)
- Use `frontend/index.html` directly
- No backend required
- Perfect for presentations and mockups
- Update data manually in HTML

### Option 2: Streamlit Integration (Production)
- Use `backend/app.py` with custom CSS
- Real-time data from Supabase
- Auto-refresh capabilities
- Easy deployment

### Option 3: Custom Backend Integration
- Use `frontend/` files as frontend
- Create API endpoints (see `backend/api.py`)
- Connect JavaScript to your API
- Full control over data flow

## 📱 Responsive Breakpoints

```css
/* Desktop (default) - 1200px+ */
.dashboard-grid { grid-template-columns: repeat(3, 1fr); }

/* Tablet - 768px to 1199px */
@media (max-width: 1199px) {
  .dashboard-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Mobile - 767px and below */
@media (max-width: 767px) {
  .dashboard-grid { grid-template-columns: 1fr; }
  .sidebar { width: 60px; }
}
```

## 🚀 Quick Start Guide

### 1. View Standalone HTML Dashboard
```bash
# Open in browser
cd frontend
start index.html
```

### 2. Run Streamlit Dashboard
```bash
# Ensure dependencies are installed
pip install -r backend/requirements.txt

# Run Streamlit app
streamlit run backend/app.py
```

### 3. Integrate with API
```bash
# Start Flask API
cd backend
python run_api.py

# Start Streamlit Dashboard (in another terminal)
streamlit run backend/app.py

# The dashboard will fetch data from API automatically
```

## 🎯 Customization Guide

### Change Colors
Edit CSS variables in `frontend/css/styles.css`:
```css
:root {
  --bg-cream: #F5F1E8;          /* Your color */
  --sentiment-positive: #2ECC71; /* Your color */
  /* etc... */
}
```

### Add New Components
1. Add HTML markup to `index.html`
2. Add styles to `styles.css`
3. Add interactivity to `app.js` (if needed)

### Modify Chart Data
Update the data in `frontend/js/app.js`:
```javascript
// Line 20: Update chart data
data: {
  labels: ['Your', 'Labels'],
  datasets: [{
    data: [45, 33, 22], // Your data
  }]
}
```

## 📚 Dependencies

### Frontend (HTML Version)
- **Chart.js** v4.4.0 - For donut charts
- **Font Awesome** v6.4.0 - For icons
- No other dependencies (vanilla JavaScript)

### Backend (Streamlit Version)
```txt
streamlit==1.29.0
plotly==5.18.0
pandas==2.1.4
supabase==2.9.1
python-dotenv==1.0.0
```

## 🐛 Troubleshooting

### Charts not showing
- Ensure Chart.js CDN is loaded
- Check browser console for errors
- Verify canvas element exists

### Styles not applying
- Check CSS file path in HTML
- Clear browser cache
- Verify CSS selectors match HTML

### Streamlit custom CSS not working
- Ensure `unsafe_allow_html=True` is set
- Check for CSS syntax errors
- Restart Streamlit app

## 📝 Best Practices

1. **Performance**
   - Use CSS transforms for animations (not position)
   - Minimize repaints with `will-change`
   - Lazy load images

2. **Accessibility**
   - Add ARIA labels to interactive elements
   - Ensure keyboard navigation works
   - Maintain sufficient color contrast

3. **Maintenance**
   - Keep CSS variables for easy theming
   - Comment complex JavaScript functions
   - Document custom components

## 🔗 Related Documentation

- [UI Implementation Plan](../docs/UI_IMPLEMENTATION_PLAN.md) - Detailed component specs
- [Local Setup Guide](../docs/LOCAL_SETUP.md) - Full project setup
- [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Architecture overview

## 📧 Support

For issues or questions:
1. Check the [UI Implementation Plan](../docs/UI_IMPLEMENTATION_PLAN.md)
2. Review browser console for errors
3. Verify all dependencies are installed

---

**Version:** 1.0
**Last Updated:** 2025-12-27
**Maintainer:** Project S Team
