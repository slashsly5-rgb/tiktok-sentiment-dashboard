# Project S - React Dashboard

A modern, responsive React dashboard for TikTok political sentiment analysis built with Vite, React 18, and Chart.js.

## 🚀 Features

- ✅ **Modern React** - Built with React 18 and Vite for blazing-fast development
- ✅ **Component-Based** - Modular, reusable components
- ✅ **Real-time Data** - Auto-refresh every 5 minutes
- ✅ **Interactive Charts** - Chart.js donut charts for sentiment visualization
- ✅ **Interactive Map** - SVG map with click events for regional analysis
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile
- ✅ **API Integration** - Ready to connect to Flask backend
- ✅ **Mock Data** - Built-in fallback data for development

## 📦 Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Chart.js** - Data visualization
- **Axios** - HTTP client
- **CSS3** - Styling with custom properties
- **Font Awesome** - Icons

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

### 3. Run Development Server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm run preview
```

## 🔧 API Configuration

Edit `.env`:

```env
VITE_API_URL=http://localhost:5000/api
```

## 📝 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## 🎨 Color Scheme

All colors match the UI design screenshot:
- Cream background: `#F5F1E8`
- Positive sentiment: `#2ECC71` (Green)
- Negative sentiment: `#E74C3C` (Red)
- Neutral sentiment: `#95A5A6` (Gray)

---

**Built with React + Vite** ⚛️
