# News Sentiment Comparison Tool

A production-ready automation platform that orchestrates data collection, API integration, and scheduled workflows. The system automatically fetches headlines from multiple news sources via REST APIs and RSS feeds, processes them through an automated pipeline, and serves results through a RESTful API with a web dashboard. Uses AI-powered sentiment analysis as part of the processing pipeline.

## Features

- 🔄 **Automated Data Collection**: Scheduled workflows orchestrate daily headline collection from multiple sources via REST APIs and RSS feeds
- 🚀 **FastAPI Backend**: Production-ready RESTful API with health checks, authentication, and comprehensive error handling
- ⚙️ **Infrastructure as Code**: Complete deployment automation via Render Blueprint (render.yaml) for multi-service architecture
- 🔐 **Secure API Endpoints**: Protected collection endpoints with secret-based authentication for external cron triggers
- 📡 **Multi-Source Integration**: Integrates with NewsAPI REST service and RSS feeds for comprehensive data collection
- 🗄️ **MongoDB Storage**: Document-based storage with connection pooling and error recovery
- ⚛️ **React Frontend**: Modern dashboard with real-time visualizations - [Live Demo](https://sentimentlens.netlify.app)
- 🤖 **AI-Powered Processing**: Uses LLM APIs (Groq/OpenAI) for sentiment scoring as part of the automated pipeline
- 📊 **Daily Comparisons**: Aggregates and compares sentiment across political sides
- 📈 **Historical Trends**: Track sentiment changes over time

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

## CI/CD Pipeline (GitLab CI)

[![Pipeline](https://gitlab.com/rclarke009-group/news-sentiment-comparison/badges/main/pipeline.svg)](https://gitlab.com/rclarke009-group/news-sentiment-comparison/-/pipelines)

This project uses a production-grade CI/CD pipeline with automated linting, testing, smoke validation against deployed services, and optional security scanning via OWASP ZAP. Smoke tests and ZAP scans are designed to catch configuration, deployment, and security regressions that unit tests cannot detect.

**Pipeline stages:**
- **Lint**: black, ruff, mypy
- **Test**: pytest unit and integration tests
- **Smoke**: validates live API endpoints (dev, staging, production) post-deploy
- **Security**: OWASP ZAP dynamic scan (configurable fail levels); Secret Detection for committed secrets

**How CI interacts with production:** CI does not deploy; it validates. On push to `main`/`master`, the pipeline runs lint, test, smoke against the production API URL, and security (ZAP + Secret Detection). Production is the live API (e.g. Render) that `PROD_API_BASE_URL`/`API_BASE_URL` points to. Render deploys from the connected Git repo; CI gives confidence before and after that deploy.

**Branch behavior:**

| Branch | Stages that run |
|--------|------------------|
| Feature / MR | lint, test |
| develop | lint, test, smoke:dev, zap:dev (optional) |
| staging | lint, test, smoke:staging, zap:staging |
| main / master | lint, test, smoke:prod, zap:prod (manual approval for prod ZAP) |

See [Development](#development) for CI/CD setup (variables, local testing).

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

- **Live Frontend**: https://sentimentlens.netlify.app
- **Local API Docs**: `http://localhost:8000/docs`
- **Production API Docs**: https://sentiment-lens.onrender.com/docs
- **Health Check**: `http://localhost:8000/api/v1/health`

### 6. Test the API

```bash
# Get today's comparison
curl http://localhost:8000/api/v1/today

# Get most uplifting conservative story
curl http://localhost:8000/api/v1/most-uplifting?side=conservative

# Get last 7 days
curl http://localhost:8000/api/v1/history?days=7
```

## Portfolio Demo / Manual Collection

For portfolio demonstrations or when cron jobs aren't running, you can manually trigger data collection:

### Option 1: Command Line Script
```bash
# Collect for today
python scripts/run_collector.py

# Collect for specific date
python scripts/run_collector.py --date 2026-01-24

# Dry run (test without saving to database)
python scripts/run_collector.py --dry-run
```

### Option 2: API Endpoint (if deployed)
If your API is deployed, you can trigger collection via the secure API endpoint:

```bash
# Requires CRON_SECRET_KEY header (set in your environment variables)
curl -X POST https://your-api-url.onrender.com/api/v1/collect \
  -H "X-Cron-Secret: your_secret_key_here"
```

This allows you to demonstrate the full automation pipeline on-demand without waiting for scheduled runs. The collection process will:
1. Fetch headlines from all configured sources (NewsAPI + RSS feeds)
2. Process and score each headline
3. Calculate statistics and comparisons
4. Save results to MongoDB
5. Return a summary with collection results

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

> **Interactive API Documentation**: View and test all endpoints at [https://sentiment-lens.onrender.com/docs](https://sentiment-lens.onrender.com/docs)

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

### CI/CD Pipeline (GitLab CI)

See above for a summary of stages and how CI interacts with production.

The project includes a GitLab CI pipeline (`.gitlab-ci.yml`) that automates code quality checks, testing, smoke tests, and security scanning per environment (dev, staging, production).

**Setup:**

1. **Push code to GitLab** - Connect your repository to GitLab
2. **Set CI/CD Variables** (Settings → CI/CD → Variables):
   - `DEV_API_BASE_URL`: Dev API URL (e.g., `https://news-sentiment-api-dev.onrender.com`); used on `develop`
   - `STAGING_API_BASE_URL`: Staging API URL; used on `staging`
   - `PROD_API_BASE_URL` or `API_BASE_URL`: Production API URL (e.g., `https://news-sentiment-api.onrender.com`); used on `main`/`master`
   - `ZAP_SKIP` (optional): Set to `"true"` to skip ZAP jobs (e.g. on MRs)
   - `ZAP_API_KEY` (optional): ZAP API key if using authenticated ZAP instance

3. **Pipeline runs** per branch (see branch behavior table above). Production ZAP can require manual approval (risk management).

**Local Testing:**
You can test the CI scripts locally:
```bash
# Test smoke script with env var (like CI does)
API_BASE_URL=https://your-api.onrender.com python scripts/smoke_test_production.py

# Test ZAP with fail-on (like CI does)
python scripts/zap_scan.py --target https://your-api.onrender.com --fail-on high,medium
```

### Security Testing (OWASP ZAP)

Run security scans with OWASP ZAP to identify common vulnerabilities:

```bash
# Start ZAP (Docker)
docker run -d -p 8080:8080 --name zap zaproxy/zap-stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true -config 'api.addrs.addr.name=.*' -config 'api.addrs.addr.regex=true'

# Run scan against local API
python scripts/zap_scan.py --target http://localhost:8000

# Run scan against production
python scripts/zap_scan.py --target https://sentiment-lens.onrender.com

# Fail on High/Medium findings (useful for CI/CD)
python scripts/zap_scan.py --target http://localhost:8000 --fail-on high,medium
```

See [SECURITY.md](SECURITY.md#security-testing-with-owasp-zap) for detailed instructions.

### Smoke testing production

After deploying to Render, run a quick smoke test against your production API:

```bash
python scripts/smoke_test_production.py
# If your API uses a different URL (e.g. sentiment-lens.onrender.com):
python scripts/smoke_test_production.py --base-url https://your-api.onrender.com
```

Use it **after deploys**, **after env var changes**, or when debugging prod vs local. See **QUICKSTART.md** → [Smoke testing production](QUICKSTART.md#smoke-testing-production) for when and how. For frontend and API checks in a browser, see **Playwright E2E** below.

### Playwright E2E (frontend + API)

The frontend uses Playwright for browser E2E and API checks. Run from `frontend/`:

```bash
cd frontend
npm install
npx playwright install   # first time only: installs browsers
```

| Script | What it runs | Target |
|--------|--------------|--------|
| `npm run test:e2e` | Frontend smoke + API tests | Local (dev server on :5173, API on :8000) |
| `npm run test:e2e:prod` | Frontend smoke + API tests | Production base URL |
| `npm run test:api` | API tests only | Local API |
| `npm run test:api:prod` | API tests only | Production API |

**Local:** Start the API (`uvicorn …`) and frontend (`npm run dev`) in separate terminals, then run `npm run test:e2e` or `npm run test:api` from `frontend/`.

**Production:** Use `test:e2e:prod` / `test:api:prod` to hit deployed services (e.g. after a Render deploy). For frontend E2E against your live site (e.g. Netlify), set `PLAYWRIGHT_BASE_URL` to the frontend URL:

```bash
PLAYWRIGHT_BASE_URL=https://sentimentlens.netlify.app npm run test:e2e
```

### Run full lint (match CI)

Before pushing, run the same checks as the GitLab lint job:

```bash
./scripts/lint.sh
```

Or run the commands directly:

```bash
black --check news_sentiment/ scripts/
ruff check news_sentiment/ scripts/
```

### Code Formatting

Format code (same paths as CI):

```bash
black news_sentiment/ scripts/
```

Check only (no write): `black --check news_sentiment/ scripts/`

### Linting (Ruff)

Run the same lint check as CI before pushing:

```bash
ruff check news_sentiment/ scripts/
```

Auto-fix what Ruff can fix: `ruff check news_sentiment/ scripts/ --fix`

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

- **Render**: Use "Cron Job" service type, set command to run `python scripts/run_collector.py` (requires Starter plan or higher - free tier doesn't support cron jobs)
- **Railway**: Use scheduled tasks or background workers
- **Fly.io**: Use scheduled tasks or systemd timers
- **External cron services**: Use cron-job.org or EasyCron to call an API endpoint that triggers collection (works on free tier - see setup below)

### Setting Up cron-job.org (Free Alternative)

If you're using Render's free tier (which doesn't support cron jobs), you can use an external service like cron-job.org to trigger collection:

#### Step 1: Generate a Secret Key

Generate a secure random secret key for authentication:

```bash
# On macOS/Linux
openssl rand -hex 32

# Or use Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 2: Set Environment Variable

Add the secret key to your Render environment variables:

1. Go to your Render dashboard → Your API service → Environment
2. Add a new environment variable:
   - **Key**: `CRON_SECRET_KEY`
   - **Value**: The secret key you generated (e.g., `a1b2c3d4e5f6...`)
3. Save and redeploy your service

#### Step 3: Create Account on cron-job.org

1. Sign up at https://cron-job.org (free account available)
2. Verify your email address

#### Step 4: Create a New Cron Job

1. Click **"Create cronjob"** in your dashboard
2. Configure the job:
   - **Title**: `News Sentiment Collection` (or any name you prefer)
   - **Address (URL)**: `https://your-api-url.onrender.com/api/v1/collect`
     - Replace `your-api-url` with your actual Render API URL
   - **Request method**: `POST`
   - **Request headers**: Click "Add header" and add:
     - **Name**: `X-Cron-Secret`
     - **Value**: Your `CRON_SECRET_KEY` value (the same one you set in Render)
   - **Schedule**: 
     - For daily at 10 AM UTC: `0 10 * * *`
     - For daily at 2 AM UTC (9 PM EST): `0 2 * * *`
     - Or use the visual scheduler to pick a time
   - **Activate cronjob**: Check this box
3. Click **"Create cronjob"**

#### Step 5: Test the Endpoint

Before activating, test that your endpoint works:

```bash
# Replace with your actual values
curl -X POST https://your-api-url.onrender.com/api/v1/collect \
  -H "X-Cron-Secret: your_secret_key_here"
```

You should get a JSON response with collection results.

#### Step 6: Monitor Logs

- **cron-job.org**: Check the "Executions" tab to see when the job runs and if it succeeded
- **Render**: Check your API service logs to see collection activity

#### Troubleshooting cron-job.org

- **401 Unauthorized**: Check that `CRON_SECRET_KEY` in Render matches the header value in cron-job.org
- **500 Error**: Check Render logs for collection errors (API keys, MongoDB connection, etc.)
- **Job not running**: Verify the schedule is correct and the job is activated in cron-job.org

### Manual Collection

For manual collection (useful for portfolio demos or troubleshooting), see the [Portfolio Demo / Manual Collection](#portfolio-demo--manual-collection) section above.

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

### Checking Render Logs (Production Issues)

If you're experiencing issues in production (e.g., all scores are 0, "No uplifting story found", collection failures), **always check Render logs first**:

1. **Access Render Logs:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Select your service (e.g., `news-sentiment-api` or `news-sentiment-collector`)
   - Click on the **Logs** tab
   - Scroll to see recent log entries

2. **What to Look For:**
   - **API Key Errors**: Look for `401`, `AuthenticationError`, or `Incorrect API key provided`
     - If you see this, your `OPENAI_API_KEY` or `GROQ_API_KEY` is invalid/truncated
     - Fix: Go to Render → Environment → Update the key (ensure it's the full key, no spaces/line breaks)
   - **Scoring Errors**: Look for `Error scoring headline` or `LLM API error`
     - These indicate why scoring failed (API key, network, rate limits)
   - **Collection Results**: Look for `Collection completed for` log entries
     - Shows `avg_uplift` values (should be non-zero if scoring worked)
   - **Save Verification**: Look for `Saving headlines with scores - sample: final_score=...`
     - Confirms scores are calculated before saving to MongoDB

3. **Common Issues Found in Logs:**
   - **Invalid API Key**: `openai.AuthenticationError: Error code: 401 - Incorrect API key provided`
     - **Solution**: Update `OPENAI_API_KEY` in Render environment variables with the full key
   - **All Scores Zero**: If `avg_uplift: 0.0` in collection results, check for scoring errors in logs
   - **500 Errors**: Check logs for stack traces showing conversion errors or missing data

4. **After Fixing Issues:**
   - Redeploy the affected service(s) in Render
   - Trigger a new collection (via `/collect` endpoint or wait for cron)
   - Check logs again to verify the fix worked

**Remember**: Render logs are your primary debugging tool for production issues. Always check them before assuming the problem is elsewhere.

### Rate Limiting

NewsAPI free tier allows 100 requests/day. The collector respects rate limits with delays between requests.

## Deployment a

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
   - Click "Connect" → "Connect your application."
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
- [ ] Add logic to only call expensive LLM when local model confidence is low (cost optimization story for interviews)
- [ ] Add comparison between local model and LLM over time.

## Challenges Overcome / Lessons Learned

- **Timezone Consistency**: Resolved date format inconsistencies between UTC and local time across different components of the system
- **Deployment Configuration**: Debugged and fixed environment variable truncation issues during initial cloud deployment setup
- **Timeout Issues**: Debugged and fixed timeout issues during initial cloud deployment setup (Render on free tier was spinning down, so the cron job couldn't access the API.)




## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
