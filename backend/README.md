# Backend

This directory contains all the Python backend code for the TikTok Political Sentiment Scraper.

## Structure

```
backend/
├── api.py                 # Flask API server for n8n integration
├── app.py                 # Streamlit dashboard application
├── scraper.py             # TikTok scraping logic using Playwright
├── analyzer.py            # OpenAI-powered sentiment analysis
├── database.py            # Supabase database client
├── config.py              # Configuration and environment variables
├── run_api.py             # API server startup script
├── run_scraper_job.py     # Scraper job runner
├── setup.sql              # Database schema
├── requirements.txt       # Python dependencies
├── requirements-api.txt   # API-specific dependencies
└── scripts/
    ├── setup_database.py  # Database initialization script
    ├── test_api.py        # API testing script
    └── apify_adapter.py   # Apify integration adapter
```

## Running the Backend

### API Server
```bash
cd backend
python run_api.py
```

### Streamlit Dashboard
```bash
streamlit run backend/app.py
```

### Run Scraper Job
```bash
cd backend
python run_scraper_job.py --keyword "Sarawak politics"
```

## Configuration

All configuration is managed through environment variables in the `.env` file located in the project root directory.
