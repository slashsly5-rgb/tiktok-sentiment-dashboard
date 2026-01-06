# Implementation Plan: Local MVP TikTok Political Sentiment Scraper

## Overview

Transform the existing TikTok scraper into a **local, non-Docker MVP** with **two scraper options**:

### Scraper Options
1. **Local Playwright Scraper** (Free)
   - Uses existing scraper.py with Playwright
   - Runs on your local machine
   - Free but requires maintenance for anti-bot changes
   - Good for testing and low-volume scraping

2. **Apify TikTok Scraper** (Paid - Free tier available)
   - Uses Apify's pre-built TikTok scraper actor
   - More reliable and maintained by Apify team
   - $5 free credits monthly, then pay-as-you-go (~$0.50 per 100 videos)
   - Handles anti-bot measures automatically

### Common Components
- HTTP API for n8n orchestration (Flask)
- Supabase database persistence
- Automated scheduling (every 6 hours via n8n)
- Streamlit dashboard for visualization
- Focus on Sarawak politicians and current events

## File Structure

### New Files to Create

```
tiktok-scraper/
├── api.py                          # Flask API wrapper for n8n
├── database.py                     # Supabase client and operations
├── config.py                       # Centralized configuration
├── run_api.py                      # API startup script
├── run_scraper_job.py              # Standalone scraper job script (for local)
├── requirements-api.txt            # API-specific dependencies
├── setup.sql                       # Database schema for Supabase
├── n8n-workflow-local.json         # n8n workflow using local Playwright scraper
├── n8n-workflow-apify.json         # n8n workflow using Apify TikTok scraper
├── scripts/
│   ├── setup_database.py           # Database initialization
│   ├── test_api.py                 # API testing script
│   ├── install_local.bat           # Windows setup script
│   └── apify_adapter.py            # Convert Apify data to our schema
└── docs/
    ├── LOCAL_SETUP.md              # Step-by-step setup guide
    └── APIFY_SETUP.md              # Apify integration guide
```

### Files to Modify

- `scraper.py` - Add Supabase integration and keyword parameter
- `analyzer.py` - Work with Supabase data instead of in-memory
- `app.py` - Query Supabase instead of running scraper directly
- `requirements.txt` - Add Supabase client
- `.env` - Add OpenAI API key and API port config

---

## Phase 1: Database Foundation

### 1.1 Create Database Schema (setup.sql)

**Tables:**
- `videos` - TikTok video metadata (url, author, description, stats, post_url, transcribed_url, summary, hashtags)
- `comments` - Video comments with author and likes
- `sentiment_analysis` - AI analysis results (sentiment, score, topic, key issues)

**Key Features:**
- UUID primary keys
- Foreign key relationships with CASCADE delete
- Performance indexes on tiktok_id, scraped_at, video_id
- JSONB columns for hashtags and key_issues
- Unique constraint on tiktok_id to prevent duplicates
- URL fields for post/screenshot and transcription (stored in Supabase Storage)
- Summary field for video content summary

### 1.2 Create Database Module (database.py)

**Core Class:** `SupabaseClient`

**Methods:**
- `insert_video(video_data)` - Insert video and return UUID
- `insert_comments(video_id, comments)` - Batch insert comments
- `insert_sentiment(video_id, analysis)` - Store analysis results
- `get_video_by_tiktok_id(tiktok_id)` - Check for duplicates
- `get_unanalyzed_videos(limit)` - Query videos without sentiment
- `get_video_with_comments(video_id)` - Join query for analysis
- `get_recent_videos(days, keyword)` - Dashboard query
- `get_sentiment_overview(days)` - Aggregated statistics

**Error Handling:**
- Connection retry (3 attempts with exponential backoff)
- Detailed logging for debugging
- Graceful degradation if Supabase unavailable

### 1.3 Create Config Module (config.py)

**Configuration:**
- Supabase URL, keys
- OpenAI API key
- API host/port (default: 0.0.0.0:5000)
- Scraper settings (headless mode, max videos)
- Default keywords for Sarawak politics

**Keywords List:**
```python
DEFAULT_KEYWORDS = [
    # Politicians
    "Abang Johari", "Fadillah Yusof", "Abdul Karim Rahman Hamzah",
    "Tiong King Sing", "Yii Siew Ling",

    # Topics
    "GPS Sarawak", "Sarawak politics", "Sarawak development",
    "Pan Borneo Highway", "MA63 rights", "Sarawak autonomous",
    "PCDS Sarawak", "Sarawak budget 2025"
]
```

---

## Phase 2: Core Scraper Integration

### 2.1 Modify scraper.py

**New Functions:**

```python
def extract_tiktok_id(url: str) -> str:
    """Extract video ID from TikTok URL for uniqueness"""
    # Parse from URL: https://www.tiktok.com/@user/video/1234567890
    return url.split('/video/')[1].split('?')[0]

async def scrape_and_save(keyword: str, max_videos: int, db_client: SupabaseClient):
    """Scrape videos and save to Supabase"""
    # 1. Search videos by keyword
    # 2. For each video:
    #    - Extract tiktok_id
    #    - Check if already exists in DB (skip duplicates)
    #    - Scrape video details + comments
    #    - Save to database (video + comments)
    # 3. Return list of video IDs
```

**Changes:**
- Accept keyword parameter in search function
- Add database integration after scraping
- Store screenshots as base64 in database
- Implement deduplication logic
- Add search_keyword field to track which keyword found the video

### 2.2 Create run_scraper_job.py

**Purpose:** Standalone script to run scraping job (called by API)

**Functionality:**
- Accept keywords and max_videos as command-line args
- Initialize database client
- Run scraper for each keyword
- Return results as JSON
- Handle errors gracefully

---

## Phase 3: HTTP API Layer

### 3.1 Create api.py (Flask)

**Framework:** Flask (simpler than FastAPI for MVP)
**Port:** 5000

**Endpoints:**

```python
GET  /health
     # Health check - returns {"status": "ok", "timestamp": "..."}

POST /scrape
     # Trigger scraping job
     # Body: {
     #   "keywords": ["keyword1", "keyword2"],
     #   "max_videos_per_keyword": 5,
     #   "analyze": true
     # }
     # Returns: {"job_id": "uuid", "status": "started"}

GET  /scrape/status/<job_id>
     # Get job status and progress
     # Returns: {
     #   "job_id": "uuid",
     #   "status": "running|completed|failed",
     #   "progress": {...},
     #   "results": {...}
     # }

GET  /videos?limit=10&days=7&keyword=filter
     # Get recent videos from database

GET  /sentiment/overview?days=7
     # Get sentiment statistics

POST /analyze
     # Trigger analysis for specific video IDs or all unanalyzed
     # Body: {"video_ids": ["uuid1", "uuid2"]}

POST /api/videos/bulk
     # Bulk insert videos (for Apify workflow)
     # Body: [{video_data1}, {video_data2}, ...]
     # Returns: {"inserted": 5, "skipped": 2, "video_ids": [...]}
```

**Background Jobs:**
- Use Python threading for async execution (no Redis/Celery needed for MVP)
- Store job status in memory dict
- Each job runs scraper + analyzer in separate thread

**Error Handling:**
- Proper HTTP status codes (400, 404, 500)
- Logging to `logs/api.log`
- Try/catch all routes

### 3.2 Create run_api.py

**Purpose:** Start Flask API server

```python
from api import app
from config import Config

if __name__ == "__main__":
    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.API_DEBUG
    )
```

---

## Phase 4: Analyzer Integration

### 4.1 Modify analyzer.py

**New Functions:**

```python
def analyze_from_database(video_id: str, db_client: SupabaseClient):
    """Analyze a video already in database"""
    # 1. Fetch video + comments from database
    # 2. Run existing analysis logic
    # 3. Parse result to match database schema
    # 4. Save sentiment to database
    # 5. Return analysis result

def batch_analyze_unanalyzed(db_client: SupabaseClient, limit: int = 10):
    """Analyze videos without sentiment data"""
    # 1. Query unanalyzed videos
    # 2. For each video, run analyze_from_database()
    # 3. Handle errors (continue on failure)
    # 4. Return list of results
```

**Changes:**
- Accept database client as parameter
- Fetch data from Supabase instead of in-memory
- Save results to database after analysis
- Enhanced parsing for structured database schema

---

## Phase 5: Dashboard Modification

### 5.1 Modify app.py

**Remove:**
- Scraper execution code
- Direct scraper.py imports
- Settings sidebar (keyword input, video limit)

**Add:**
- Supabase database queries
- Filters: date range, keyword, sentiment
- Auto-refresh option (5 minute cache)
- Sentiment distribution chart (pie chart)
- Metrics row: Total Videos, Analyzed, Avg Sentiment, Total Views
- Recent videos table with expandable details

**New Structure:**

```python
import streamlit as st
from database import SupabaseClient
import pandas as pd
import plotly.express as px

# Initialize DB
db = SupabaseClient()

# Sidebar filters
days_filter = st.sidebar.slider("Days to show", 1, 30, 7)
keyword_filter = st.sidebar.text_input("Filter by keyword")
auto_refresh = st.sidebar.checkbox("Auto-refresh (5 min)")

# Load data with caching
@st.cache_data(ttl=300)
def load_videos(days, keyword):
    return db.get_recent_videos(days=days, keyword=keyword)

@st.cache_data(ttl=300)
def load_sentiment_overview(days):
    return db.get_sentiment_overview(days=days)

# Display metrics
overview = load_sentiment_overview(days_filter)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Videos", overview['total_videos'])
col2.metric("Analyzed", overview['total_analyzed'])
col3.metric("Avg Sentiment", f"{overview['avg_sentiment']:.1f}/10")
col4.metric("Trending Keyword", overview['top_keyword'])

# Sentiment chart
fig = px.pie(overview['sentiment_breakdown'])
st.plotly_chart(fig)

# Videos table
videos = load_videos(days_filter, keyword_filter)
st.dataframe(videos)
```

---

## Phase 6: n8n Workflows (Two Options)

### Option 1: Local Playwright Scraper Workflow

### 6.1 Create n8n-workflow-local.json

**Workflow Name:** "TikTok Political Scraper - Local (Scheduled)"

**Nodes:**

1. **Schedule Trigger** (Cron)
   - Expression: `0 */6 * * *` (every 6 hours)
   - Timezone: Asia/Kuching

2. **Set Keywords** (Code Node)
   ```javascript
   const keywords = [
     "Abang Johari",
     "GPS Sarawak",
     "Sarawak politics",
     "Sarawak development",
     "Pan Borneo Highway",
     "MA63 Sarawak"
   ];
   return keywords.map(k => ({keyword: k}));
   ```

3. **Loop Over Keywords** (Split Out Node)
   - Item mode: Split each item

4. **HTTP Request - Trigger Scrape** (HTTP Request)
   - Method: POST
   - URL: `http://localhost:5000/scrape`
   - Body Type: JSON
   - Body:
     ```json
     {
       "keywords": ["{{$node["Set Keywords"].json["keyword"]}}"],
       "max_videos_per_keyword": 5,
       "analyze": true
     }
     ```

5. **Wait for Completion** (Wait Node)
   - Wait type: Time
   - Duration: 5 minutes

6. **HTTP Request - Check Status** (HTTP Request)
   - Method: GET
   - URL: `http://localhost:5000/scrape/status/{{$node["HTTP Request - Trigger Scrape"].json["job_id"]}}`

7. **IF - Check Success** (IF Node)
   - Condition: `{{$node["HTTP Request - Check Status"].json["status"]}} === "completed"`
   - True branch: Success notification
   - False branch: Error notification

8. **Success Notification** (Email/Webhook - Optional)
   - Send summary of scraped videos
   - Include video count and sentiment stats

**Export:** Standard n8n JSON export with all nodes pre-configured

---

### Option 2: Apify TikTok Scraper Workflow

### 6.2 Create n8n-workflow-apify.json

**Workflow Name:** "TikTok Political Scraper - Apify (Scheduled)"

**Prerequisites:**
- Apify account (free tier: $5 credits/month)
- Apify API token
- n8n Apify node installed

**Nodes:**

1. **Schedule Trigger** (Cron)
   - Expression: `0 */6 * * *` (every 6 hours)
   - Timezone: Asia/Kuching

2. **Set Keywords** (Code Node)
   ```javascript
   const keywords = [
     "Abang Johari",
     "GPS Sarawak",
     "Sarawak politics",
     "Sarawak development",
     "Pan Borneo Highway",
     "MA63 Sarawak"
   ];
   return keywords.map(k => ({keyword: k}));
   ```

3. **Loop Over Keywords** (Split Out Node)
   - Item mode: Split each item

4. **Apify - Run TikTok Scraper** (Apify Node)
   - Actor: `clockworks/tiktok-scraper`
   - Input:
     ```json
     {
       "searchQueries": ["{{$node["Set Keywords"].json["keyword"]}}"],
       "resultsPerPage": 5,
       "shouldDownloadVideos": false,
       "shouldDownloadCovers": false,
       "proxyConfiguration": {
         "useApifyProxy": true
       }
     }
     ```
   - Wait for completion: Yes
   - Timeout: 10 minutes

5. **Code Node - Parse Apify Output** (Code Node)
   ```javascript
   // Apify returns different format than our local scraper
   // Need to transform to match our database schema
   const items = $input.all();
   const videos = [];

   for (const item of items) {
     const data = item.json;
     videos.push({
       tiktok_id: data.id,
       url: data.webVideoUrl,
       author_username: data.authorMeta.name,
       description: data.text,
       views_count: data.playCount,
       likes_count: data.diggCount,
       shares_count: data.shareCount,
       comments_count: data.commentCount,
       hashtags: data.hashtags.map(h => h.name),
       search_keyword: $node["Set Keywords"].json["keyword"]
     });
   }

   return videos.map(v => ({json: v}));
   ```

6. **HTTP Request - Save to Database** (HTTP Request)
   - Method: POST
   - URL: `http://localhost:5000/api/videos/bulk`
   - Body Type: JSON
   - Body: `{{$json}}`
   - Loop over items: Yes

7. **HTTP Request - Trigger Analysis** (HTTP Request)
   - Method: POST
   - URL: `http://localhost:5000/analyze`
   - Body Type: JSON
   - Body:
     ```json
     {
       "video_ids": null,
       "analyze_all_unanalyzed": true
     }
     ```

8. **Success Notification** (Email/Webhook - Optional)
   - Send summary of scraped videos
   - Include video count and Apify credits used

**Export:** Standard n8n JSON export with all nodes pre-configured

### 6.3 Create scripts/apify_adapter.py

**Purpose:** Helper script to transform Apify data format to our database schema

```python
def transform_apify_to_schema(apify_data):
    """
    Transform Apify TikTok scraper output to our database schema

    Apify format:
    {
        "id": "1234567890",
        "text": "Video description...",
        "authorMeta": {"name": "username"},
        "webVideoUrl": "https://...",
        "playCount": 12000,
        "diggCount": 450,
        "shareCount": 20,
        "commentCount": 89,
        "hashtags": [{"name": "politics"}]
    }

    Our schema:
    {
        "tiktok_id": "1234567890",
        "url": "https://...",
        "author_username": "username",
        "description": "...",
        "views_count": 12000,
        "likes_count": 450,
        "shares_count": 20,
        "comments_count": 89,
        "hashtags": ["politics"]
    }
    """
    return {
        "tiktok_id": apify_data.get("id"),
        "url": apify_data.get("webVideoUrl"),
        "author_username": apify_data.get("authorMeta", {}).get("name"),
        "description": apify_data.get("text"),
        "views_count": apify_data.get("playCount", 0),
        "likes_count": apify_data.get("diggCount", 0),
        "shares_count": apify_data.get("shareCount", 0),
        "comments_count": apify_data.get("commentCount", 0),
        "hashtags": [h.get("name") for h in apify_data.get("hashtags", [])],
        "screenshot_base64": None,  # Apify doesn't capture screenshots
        "search_keyword": None  # Set by calling function
    }
```

### 6.4 Comparison: Local vs Apify

| Feature | Local Playwright | Apify |
|---------|------------------|-------|
| **Cost** | Free | $5 free credits/month, then ~$0.50/100 videos |
| **Reliability** | Medium (anti-bot changes) | High (maintained by Apify) |
| **Setup** | Complex (Playwright, browser) | Simple (just API token) |
| **Speed** | 2-5 min per 5 videos | 1-2 min per 5 videos |
| **Comments** | ✅ Scrapes 20 comments | ❌ No comments (use separate actor) |
| **Screenshots** | ✅ Captures screenshots | ❌ No screenshots |
| **Proxy** | Manual setup | ✅ Built-in residential proxies |
| **Maintenance** | High (breaks with TikTok changes) | Low (Apify updates actor) |
| **Best For** | Testing, low-volume | Production, high-volume |

**Recommendation for MVP:**
- **Start with Apify** (free tier) to validate the concept quickly
- **Keep local scraper** as backup if Apify credits run out
- **Switch to Apify paid** once MVP is validated and needs scale

---

## Phase 7: Dependencies & Environment

### 7.1 Update requirements.txt

```
# Existing
playwright==1.40.0
openai==1.6.1
python-dotenv==1.0.0
streamlit==1.29.0
pandas==2.1.4
plotly==5.18.0

# Add
supabase==2.3.0
```

### 7.2 Create requirements-api.txt

```
flask==3.0.0
flask-cors==4.0.0
supabase==2.3.0
python-dotenv==1.0.0
playwright==1.40.0
openai==1.6.1
```

### 7.3 Update .env

```env
# Existing Supabase config (already present)
SUPABASE_URL=https://diifidwgnzqxogeygrsz.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Add these new variables
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_api_...           # For Apify scraper option
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
SCRAPER_HEADLESS=True
```

---

## Phase 8: Documentation & Setup Scripts

### 8.1 Create docs/LOCAL_SETUP.md

**Contents:**
1. System requirements (Python 3.11+, Node.js 18+, 8GB RAM)
2. Installation steps
3. Database setup instructions
4. Starting the services
5. Accessing the dashboard
6. Troubleshooting guide

### 8.2 Create docs/APIFY_SETUP.md

**Contents:**
1. Create Apify account (free tier signup)
2. Get Apify API token
3. Install n8n Apify node (if not included)
4. Configure Apify workflow in n8n
5. Import n8n-workflow-apify.json
6. Set up Apify credentials in n8n
7. Test Apify scraper
8. Monitor credit usage
9. Comparison with local scraper
10. When to upgrade from free tier

### 8.3 Create scripts/install_local.bat

**Purpose:** Automated Windows setup script

**Steps:**
```batch
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt

# Install Playwright browsers
playwright install chromium

# Install n8n globally
npm install -g n8n

# Setup database
python scripts/setup_database.py

# Create logs directory
mkdir logs
```

### 8.3 Create scripts/setup_database.py

**Purpose:** Initialize Supabase database

**Functionality:**
- Read setup.sql
- Connect to Supabase
- Execute SQL to create tables
- Verify table creation
- Print success/error messages

### 8.4 Create scripts/test_api.py

**Purpose:** Test all API endpoints

**Tests:**
- GET /health
- POST /scrape (with test keywords)
- GET /scrape/status/<job_id>
- GET /videos
- GET /sentiment/overview

---

## Implementation Order

### Day 1: Database Foundation
1. Create `setup.sql` with complete schema
2. Create `config.py` with environment variables
3. Create `database.py` with SupabaseClient class
4. Create `scripts/setup_database.py`
5. Run database initialization
6. Verify tables in Supabase dashboard

### Day 2: Scraper Integration
1. Modify `scraper.py`:
   - Add `extract_tiktok_id()` function
   - Add `scrape_and_save()` function
   - Integrate database client
2. Create `run_scraper_job.py`
3. Update `requirements.txt`
4. Test scraping manually with `python run_scraper_job.py`

### Day 3: API Layer
1. Create `api.py` with Flask routes
2. Create `run_api.py` startup script
3. Create `requirements-api.txt`
4. Implement background job threading
5. Add logging to `logs/api.log`
6. Test API with Postman or curl

### Day 4: Analyzer Integration
1. Modify `analyzer.py`:
   - Add `analyze_from_database()` function
   - Add `batch_analyze_unanalyzed()` function
2. Update API `/analyze` endpoint
3. Test analysis pipeline end-to-end
4. Verify sentiment data in Supabase

### Day 5: Dashboard
1. Modify `app.py`:
   - Remove scraper execution code
   - Add Supabase queries
   - Add filters and charts
   - Add auto-refresh
2. Test dashboard locally
3. Verify data display

### Day 6: n8n Workflows (Both Options)
1. Install n8n: `npm install -g n8n`
2. Start n8n: `n8n start`
3. **Option 1 - Local Workflow:**
   - Create workflow in n8n UI using local scraper
   - Configure all nodes (cron, keywords, HTTP requests)
   - Test workflow manually
   - Export to `n8n-workflow-local.json`
4. **Option 2 - Apify Workflow:**
   - Create Apify account and get API token
   - Create workflow in n8n UI using Apify node
   - Configure Apify actor settings
   - Test workflow manually
   - Export to `n8n-workflow-apify.json`
5. Create `scripts/apify_adapter.py` for data transformation

### Day 7: Documentation & Testing
1. Create `docs/LOCAL_SETUP.md`
2. Create `docs/APIFY_SETUP.md`
3. Create `scripts/install_local.bat`
4. Create `scripts/test_api.py`
5. Test both workflows end-to-end
6. Compare performance and costs
5. Document any issues

---

## Critical Files

**Priority 1 (Must create first):**
1. [setup.sql](setup.sql) - Database schema
2. [config.py](config.py) - Configuration management
3. [database.py](database.py) - Supabase client

**Priority 2 (Core functionality):**
4. [api.py](api.py) - Flask API
5. [run_api.py](run_api.py) - API startup
6. Modified [scraper.py](scraper.py) - Database integration
7. Modified [analyzer.py](analyzer.py) - Database integration

**Priority 3 (User interface):**
8. Modified [app.py](app.py) - Dashboard queries
9. [n8n-workflow-local.json](n8n-workflow-local.json) - Local Playwright workflow template
10. [n8n-workflow-apify.json](n8n-workflow-apify.json) - Apify workflow template
11. [scripts/apify_adapter.py](scripts/apify_adapter.py) - Apify data transformation

**Priority 4 (Setup & docs):**
12. [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) - Local setup guide
13. [docs/APIFY_SETUP.md](docs/APIFY_SETUP.md) - Apify setup guide
14. [scripts/setup_database.py](scripts/setup_database.py) - DB init
15. [scripts/install_local.bat](scripts/install_local.bat) - Setup script

---

## Quick Start (After Implementation)

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt
playwright install chromium
npm install -g n8n

# 2. Setup environment
# Edit .env and add OPENAI_API_KEY

# 3. Initialize database
python scripts/setup_database.py

# 4. Start services (3 separate terminals)

# Terminal 1 - API Server
python run_api.py

# Terminal 2 - Streamlit Dashboard
streamlit run app.py

# Terminal 3 - n8n
n8n start

# 5. Import n8n workflow
# Open http://localhost:5678
# Import n8n-workflow.json
# Activate workflow

# 6. Access dashboard
# Open http://localhost:8501
```

---

## Success Criteria

- ✅ n8n workflow triggers scraping every 6 hours
- ✅ API accepts scrape requests and runs jobs in background
- ✅ Scraper saves videos and comments to Supabase
- ✅ Analyzer processes videos and stores sentiment
- ✅ Dashboard displays real-time data from Supabase
- ✅ No Docker required - everything runs locally
- ✅ n8n workflow is exportable as JSON template
- ✅ Handles errors gracefully (TikTok blocks, API failures, etc.)

---

## Estimated Timeline

- **Database setup:** 1 day
- **Scraper integration:** 1 day
- **API development:** 1 day
- **Analyzer integration:** 1 day
- **Dashboard modification:** 1 day
- **n8n workflow:** 1 day
- **Documentation & testing:** 1 day

**Total:** 7 days for core implementation + 3 days buffer = **10 days**

---

## Notes

- **No Docker:** All components run directly on the host machine
- **Simple deployment:** Perfect for Windows development environment
- **Easy debugging:** Logs accessible in `logs/` folder
- **Future scalability:** Can migrate to Docker later without major changes
- **Cost-effective:** Uses Supabase free tier + OpenAI pay-as-you-go
