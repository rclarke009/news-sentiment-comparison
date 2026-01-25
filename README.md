# News Sentiment Comparison Tool

A production-ready platform for comparing sentiment and "uplift" scores between conservative and liberal news sources. Fetches top headlines daily, scores them using LLM-based sentiment analysis, and provides a web dashboard for visualization.

## Features

- 📰 **Daily Headline Collection**: Automatically fetches top stories from conservative and liberal news sources
- 🤖 **LLM-Powered Sentiment Scoring**: Uses Groq or OpenAI to score headlines for "uplift" (-5 to +5 scale)
- 🎯 **Puff Piece Detection**: Automatically boosts scores for heartwarming/uplifting stories
- 📊 **Daily Comparisons**: Aggregates and compares sentiment across political sides
- 🌟 **Most Uplifting Stories**: Highlights the most positive story from each side daily
- 📈 **Historical Trends**: Track sentiment changes over time
- 🗄️ **MongoDB Storage**: Simple document-based storage for headlines and comparisons
- 🚀 **FastAPI Backend**: RESTful API for data access
- ⚛️ **React Frontend**: Modern dashboard with visualizations (coming soon)

## Architecture

```
┌─────────────┐
│  Scheduler  │ (APScheduler - daily runs)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Collector  │ (Orchestrates pipeline)
└──────┬──────┘
       │
       ├──► NewsAPI ──► Headlines
       │
       ├──► LLM API ──► Scores
       │
       └──► MongoDB ──► Storage
              │
              ▼
       ┌─────────────┐
       │  FastAPI    │ (REST API)
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │  React App  │ (Frontend Dashboard)
       └─────────────┘
```

## Prerequisites

- Python 3.9+
- MongoDB (local or Atlas)
- Node.js 18+ (for React frontend)
- API Keys:
  - NewsAPI.org (free tier: 100 requests/day)
  - Groq API (free tier available) OR OpenAI API

## Quick Start

### 1. Clone and Setup

```bash
cd news-sentiment-comparison

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
NEWS_API_KEY=your_newsapi_key_here
GROQ_API_KEY=your_groq_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here

MONGODB_URI=mongodb://localhost:27017/news_sentiment
```

### 3. Setup MongoDB

**Option A: Local MongoDB (Docker)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo
```

**Option B: MongoDB Atlas (Cloud)**
1. Sign up at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get connection string and update `MONGODB_URI` in `.env`

### 4. Run Your First Collection

```bash
python scripts/run_collector.py
```

This will:
1. Fetch headlines from conservative and liberal sources
2. Score each headline for sentiment
3. Calculate statistics
4. Save to MongoDB

### 5. Start the API Server

```bash
uvicorn news_sentiment.api.main:app --reload
```

API will be available at `http://localhost:8000`

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### 6. Test the API

```bash
# Get today's comparison
curl http://localhost:8000/api/v1/today

# Get most uplifting conservative story
curl http://localhost:8000/api/v1/most-uplifting?side=conservative

# Get last 7 days
curl http://localhost:8000/api/v1/history?days=7
```

## Project Structure

```
news-sentiment-comparison/
├── news_sentiment/          # Python backend package
│   ├── config.py            # Configuration management
│   ├── models.py             # Pydantic data models
│   ├── news_fetcher.py       # NewsAPI integration
│   ├── sentiment_scorer.py  # LLM-based scoring
│   ├── database.py           # MongoDB operations
│   ├── collector.py          # Main orchestration
│   ├── api/                  # FastAPI application
│   └── utils/                # Utilities (logging, scheduling)
├── frontend/                 # React frontend (coming soon)
├── scripts/                  # CLI scripts
│   └── run_collector.py      # Manual collection script
├── tests/                    # Test suite
└── requirements.txt          # Python dependencies
```

## API Endpoints

### Comparisons
- `GET /api/v1/today` - Get today's comparison
- `GET /api/v1/date/{date}` - Get comparison for specific date (YYYY-MM-DD)
- `GET /api/v1/history?days=7` - Get historical comparisons

### Stories
- `GET /api/v1/most-uplifting?side={conservative|liberal}&date={date}` - Get most uplifting story

### Statistics
- `GET /api/v1/stats?days=30` - Get aggregate statistics

### Health
- `GET /api/v1/health` - Health check

## Configuration

### News Sources

Edit `news_sentiment/config.py` to customize sources:

**NewsAPI Sources:**
```python
conservative: ["fox-news", "breitbart-news", ...]
liberal: ["cnn", "msnbc", "the-new-york-times", ...]
```

**RSS Feed Sources:**
For sources not available via NewsAPI (like Newsmax), use RSS feeds:
```python
conservative_rss: [
    RSSSourceConfig(
        url="https://www.newsmax.com/rss/Newsfront/16",
        name="Newsmax",
        id="newsmax"
    )
]
```

Newsmax is now configured via RSS feeds since it's not available through NewsAPI.

### Puff Piece Keywords

Keywords that boost scores for uplifting stories:

```python
keywords: ["heartwarming", "inspiring", "rescue", "hero", ...]
```

## Development

### Making code changes and restarting

- **Local:** API runs with `--reload` and the frontend with `npm run dev` (HMR), so most code edits apply without restarting. Restart the API if you change `requirements.txt` or `.env`; restart the frontend if you change `package.json` or `VITE_*` env vars. Re-run `python scripts/run_collector.py` after backend changes if you use the collector.
- **Render (production):** Push to the connected branch to trigger a rebuild and deploy of the API and frontend. Change env vars in the Render dashboard, then redeploy the affected service(s). The cron job uses the latest deploy on each run; use **Trigger Run** in the dashboard to run it immediately.

See **QUICKSTART.md** → [Making Code Changes & Restarting](QUICKSTART.md#making-code-changes--restarting) for full tables and commands.

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Code Formatting

```bash
black news_sentiment/
```

### Type Checking

```bash
mypy news_sentiment/
```

## Automation

### Local Cron Job Setup

To automatically collect news headlines daily on your local machine:

#### Step 1: Create Wrapper Script

A wrapper script (`scripts/cron_collect.sh`) is provided to ensure the correct environment is used. Make sure it's executable:

```bash
chmod +x scripts/cron_collect.sh
```

#### Step 2: Test the Script

Test the wrapper script manually before setting up cron:

```bash
./scripts/cron_collect.sh
```

Or test directly:

```bash
cd /path/to/news-sentiment-comparison
source .venv/bin/activate
python scripts/run_collector.py
```

#### Step 3: Add Cron Job

Edit your crontab:

```bash
crontab -e
```

Add a line for daily collection. Example (runs at 10:00 AM daily):

```cron
0 10 * * * /absolute/path/to/news-sentiment-comparison/scripts/cron_collect.sh >> /tmp/news-collector.log 2>&1
```

**Cron time format:** `minute hour day-of-month month day-of-week`
- `0 10 * * *` = 10:00 AM every day
- `0 6 * * *` = 6:00 AM every day
- `0 0 * * *` = Midnight every day
- `30 9 * * *` = 9:30 AM every day

**Important Notes:**
- Cron jobs only run when your computer is **on and awake**
- If your computer is off/asleep at the scheduled time, the job will **not run**
- For production reliability, deploy to a cloud host (see Deployment section)

#### Step 4: Verify Cron Job

```bash
# List your cron jobs
crontab -l

# View the log after it runs
cat /tmp/news-collector.log

# Edit the cron job
crontab -e
```

#### Troubleshooting Cron

If the cron job doesn't run:

1. **Check if MongoDB is running:**
   ```bash
   docker ps | grep mongo
   # If not running: docker start mongodb
   ```

2. **Test the wrapper script directly:**
   ```bash
   /absolute/path/to/scripts/cron_collect.sh
   ```

3. **Check file permissions:**
   ```bash
   ls -l scripts/cron_collect.sh
   # Should show executable permissions
   ```

4. **Verify environment variables:**
   - Ensure `.env` file exists in project root
   - Check that API keys are set correctly

### Cloud-Based Automation

For production deployments, set up the cron job on your cloud host:

- **Render**: Use "Cron Job" service type, set command to run `python scripts/run_collector.py`
- **Railway**: Use scheduled tasks or background workers
- **Fly.io**: Use scheduled tasks or systemd timers
- **External cron services**: Use cron-job.org or EasyCron to call an API endpoint that triggers collection

### Manual Collection

```bash
# Collect for today
python scripts/run_collector.py

# Collect for specific date
python scripts/run_collector.py --date 2026-01-24

# Dry run (don't save to DB)
python scripts/run_collector.py --dry-run
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
docker ps | grep mongo

# Test connection
mongosh mongodb://localhost:27017
```

### API Key Issues

- NewsAPI: Sign up at https://newsapi.org (free tier: 100 requests/day)
- Groq: Sign up at https://console.groq.com (free tier available)
- OpenAI: Sign up at https://platform.openai.com

### Rate Limiting

NewsAPI free tier allows 100 requests/day. The collector respects rate limits with delays between requests.

## Deployment

### Frontend Deployment (Netlify)

Netlify is perfect for hosting the React frontend as a static site.

#### Option 1: Manual Deploy

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy:**
   - Go to https://app.netlify.com
   - Drag and drop the `frontend/dist` folder

#### Option 2: Git-Based Deploy (Recommended)

1. **Connect repository:**
   - Go to Netlify → Add new site → Import from Git
   - Connect your GitHub/GitLab/Bitbucket repository

2. **Configure build settings:**
   
   In Netlify → **Site settings → Build & deploy → Build settings**, configure:
   
   | Setting | Value |
   |---------|-------|
   | **Base directory** | `frontend` |
   | **Build command** | `npm run build` |
   | **Publish directory** | `frontend/dist` |
   
   These settings tell Netlify:
   - Where to find `package.json` (in the `frontend/` subdirectory)
   - What command to run (`npm run build` from the base directory)
   - Where the built files are located (`frontend/dist/`)

3. **Set environment variable:**
   - Go to **Site settings → Environment variables**
   - Add: `VITE_API_URL` = `https://your-api-host.com/api/v1`
   - Use your deployed backend API URL (from Render/Railway/Fly.io)
   - **Important:** Redeploy after adding the variable for it to take effect

4. **SPA Routing (if using React Router):**
   Create `frontend/public/_redirects`:
   ```
   /*    /index.html   200
   ```

   Or add to `netlify.toml` at repo root:
   ```toml
   [build]
     base = "frontend"
     command = "npm run build"
     publish = "frontend/dist"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

### Backend Deployment

Deploy your FastAPI backend to a cloud host that supports Python:

#### Option 1: Render (Recommended for Simplicity)

1. **Create account:** https://render.com

2. **Create new Web Service:**
   - Connect your Git repository
   - **Environment:** Python 3
   - **Build command:** `pip install -r requirements.txt` (or leave blank if auto-detected)
   - **Start command:** `uvicorn news_sentiment.api.main:app --host 0.0.0.0 --port $PORT`
     - ⚠️ **Critical:** The start command is required. Render sets the `$PORT` environment variable automatically.
     - `--host 0.0.0.0` allows external connections
     - The app path is `news_sentiment.api.main:app`
   - **Root Directory:** 
     - **Not needed** if deploying from the `news-sentiment-comparison` directory
     - Only specify if deploying from a parent monorepo (set to `news-sentiment-comparison`)

3. **Set environment variables:**
   In Render dashboard → Environment, add:
   - `NEWS_API_KEY` - Your NewsAPI key
   - `GROQ_API_KEY` - Your Groq API key (or use `OPENAI_API_KEY` instead)
   - `MONGODB_URI` - MongoDB Atlas connection string (required for production)
   - `CORS_ORIGINS` - Comma-separated list, e.g., `https://your-site.netlify.app,http://localhost:3000`

4. **Configure CORS:**
   Update `news_sentiment/api/main.py` to allow your Netlify domain:
   ```python
   origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
   ```

5. **Set up cron job:**
   - Create a new "Cron Job" service
   - **Schedule:** `0 10 * * *` (10 AM daily)
   - **Command:** `cd /opt/render/project/src && python scripts/run_collector.py`

#### Option 2: Railway

1. **Create account:** https://railway.app

2. **Deploy:**
   - Connect Git repository
   - Railway auto-detects Python
   - Set environment variables (same as Render)

3. **Cron job:**
   - Use Railway's scheduled tasks or a separate worker service

#### Option 3: Fly.io

1. **Install flyctl:** https://fly.io/docs/getting-started/installing-flyctl/

2. **Create app:**
   ```bash
   fly launch
   ```

3. **Set secrets:**
   ```bash
   fly secrets set NEWS_API_KEY=your_key
   fly secrets set GROQ_API_KEY=your_key
   fly secrets set MONGODB_URI=your_uri
   ```

4. **Deploy:**
   ```bash
   fly deploy
   ```

### Database: MongoDB Atlas

For production, use MongoDB Atlas (cloud database):

1. **Sign up:** https://www.mongodb.com/cloud/atlas
2. **Create free cluster** (M0 tier is free)
3. **Get connection string:**
   - Click "Connect" → "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
4. **Update `MONGODB_URI`** in your backend environment variables

### Complete Deployment Checklist

- [ ] Deploy backend to Render/Railway/Fly.io
- [ ] Set all environment variables on backend host
- [ ] Configure CORS to allow Netlify domain
- [ ] Set up MongoDB Atlas cluster
- [ ] Update `MONGODB_URI` to use Atlas
- [ ] Build and deploy frontend to Netlify
- [ ] Set `VITE_API_URL` environment variable on Netlify
- [ ] Set up cron job on backend host (or external service)
- [ ] Test the complete flow: cron → database → API → frontend

## Next Steps

- [x] React frontend dashboard
- [x] Daily automation scheduler
- [ ] Email summaries
- [ ] Historical trend analysis
- [ ] Export capabilities (CSV, JSON)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
