# Local Setup Guide - TikTok Political Sentiment Scraper

Complete setup guide for running the TikTok scraper locally on Windows.

## System Requirements

- Windows 10/11
- Python 3.11 or higher
- Node.js 18+ (for n8n)
- 8GB RAM minimum
- Active internet connection
- Supabase account (free tier)

## Step 1: Clone/Download Project

Download or clone the project to your local machine.

## Step 2: Install Python Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install API dependencies
pip install -r requirements-api.txt

# Install Playwright browsers
playwright install chromium
```

## Step 3: Configure Environment Variables

1. Open `.env` file in project root
2. Add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

3. Verify Supabase credentials are correct (should already be set)

## Step 4: Setup Database

1. Open Supabase Dashboard: https://app.supabase.com
2. Navigate to SQL Editor
3. Copy contents of `setup.sql`
4. Paste and execute in SQL Editor

Or run the setup script:

```bash
python scripts/setup_database.py
```

## Step 5: Install n8n (Optional - for automation)

```bash
npm install -g n8n
```

## Step 6: Create Logs Directory

```bash
mkdir logs
```

## Step 7: Start Services

You need 3 terminal windows:

### Terminal 1 - API Server

```bash
python run_api.py
```

API will be available at: http://localhost:5000

### Terminal 2 - Streamlit Dashboard

```bash
streamlit run app.py
```

Dashboard will open at: http://localhost:8501

### Terminal 3 - n8n (Optional)

```bash
n8n start
```

n8n will open at: http://localhost:5678

## Step 8: Import n8n Workflow (Optional)

1. Open n8n at http://localhost:5678
2. Click "Add workflow" → "Import from File"
3. Select `n8n-workflow-local.json`
4. Activate the workflow
5. The scraper will run every 6 hours automatically

## Testing the Setup

### Test API

```bash
python scripts/test_api.py
```

### Manual Scrape Test

```bash
python run_scraper_job.py --keywords "Sarawak politics" --max-videos 2
```

### Test Dashboard

1. Open http://localhost:8501
2. You should see the Project S dashboard
3. If no data, run a scrape job first

## Troubleshooting

### "Database connection failed"

- Check `.env` file has correct Supabase credentials
- Verify Supabase project is active
- Run `python scripts/setup_database.py` to verify tables

### "Playwright not found"

```bash
playwright install chromium
```

### "Port 5000 already in use"

Change API_PORT in `.env`:

```env
API_PORT=5001
```

### "No videos found"

- TikTok may be blocking the scraper
- Try different keywords
- Check `search_debug.png` for screenshots

## Daily Usage

1. **Automated (Recommended)**: n8n workflow runs every 6 hours
2. **Manual**: Run `python run_scraper_job.py` with keywords
3. **API**: Send POST request to `http://localhost:5000/scrape`

## Dashboard Access

Simply open http://localhost:8501 - it's read-only and shows latest data from database.

## Cost Breakdown

- Supabase: Free tier (500MB database)
- OpenAI: ~$0.002 per video analysis
- Playwright: Free
- n8n: Free (self-hosted)

**Total**: Essentially free for <10,000 videos/month

## Next Steps

- Read [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) for architecture details
- See [Project S Creative Document](../Project%20S%20—%20Creative%20Document%20(1).pdf) for design rationale
- Consider [Apify workflow](APIFY_SETUP.md) for production use
