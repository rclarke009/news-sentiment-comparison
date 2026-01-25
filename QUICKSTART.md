# Quick Start Guide

Get up and running in 5 minutes!

## 1. Setup Python Backend

```bash
cd news-sentiment-comparison

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# - NEWS_API_KEY (get from https://newsapi.org)
# - GROQ_API_KEY (get from https://console.groq.com) OR OPENAI_API_KEY
# - MONGODB_URI (default: mongodb://localhost:27017/news_sentiment)
```

## 3. Start MongoDB

**Option A: Docker (Recommended)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo
```

**Option B: MongoDB Atlas (Cloud)**
- Sign up at https://www.mongodb.com/cloud/atlas
- Create free cluster
- Get connection string and update `MONGODB_URI` in `.env`

## 4. Setup Database

```bash
python scripts/setup_db.py
```

## 5. Run Your First Collection

```bash
python scripts/run_collector.py
```
#the run_collector above will
#answer: it will fetch headlines, score them, and save to MongoDB.


## 6. Start the API Server

```bash
uvicorn news_sentiment.api.main:app --reload
```

#the uvicorn command above will start the API server.
#the API server will be available at http://localhost:8000
#the API server will have the following endpoints:
#- GET /api/v1/today
#- GET /api/v1/date/{date}
#- GET /api/v1/history?days=7
#- GET /api/v1/most-uplifting?side=conservative&date={date}
#- GET /api/v1/stats?days=30
#- GET /api/v1/health

API available at: http://localhost:8000
- API Docs: http://localhost:8000/docs


## 7. Setup React Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend available at: http://localhost:3000

## Test It Out

1. **Run collection**: `python scripts/run_collector.py`
2. **Check API**: Visit http://localhost:8000/api/v1/today
3. **View dashboard**: Visit http://localhost:3000

## Troubleshooting

### MongoDB Connection Failed
- Check if MongoDB is running: `docker ps | grep mongo`
- Verify `MONGODB_URI` in `.env`

### API Key Errors
- NewsAPI: Sign up at https://newsapi.org (free tier: 100 req/day)
- Groq: Sign up at https://console.groq.com (free tier available)
- OpenAI: Sign up at https://platform.openai.com

### Frontend Can't Connect to API
- Make sure API is running on port 8000
- Check `vite.config.ts` proxy configuration
- Check CORS settings in `api/main.py`

## 8. Set Up Daily Automation (Cron Job)

To automatically collect news headlines daily, set up a cron job:

### Step 1: Create Wrapper Script

The wrapper script `scripts/cron_collect.sh` should already exist. If not, create it:

```bash
chmod +x scripts/cron_collect.sh
```

### Step 2: Test the Script

```bash
./scripts/cron_collect.sh
```

### Step 3: Add Cron Job

```bash
crontab -e
```

Add this line (runs daily at 10:00 AM - adjust time as needed):

```cron
0 10 * * * /Users/rebeccaclarke/Documents/Financial/Gigs/devops_software_engineering/conceptprojects/news-sentiment-comparison/scripts/cron_collect.sh >> /tmp/news-collector.log 2>&1
```

**Cron time format:** `minute hour * * *`
- `0 10 * * *` = 10:00 AM daily
- `0 6 * * *` = 6:00 AM daily
- `0 0 * * *` = Midnight daily

### Step 4: Verify

```bash
# List your cron jobs
crontab -l

# Check the log after it runs
cat /tmp/news-collector.log
```

**Note:** Cron jobs only run when your computer is on and awake. For production, deploy to a cloud host (see Deployment section below).

## 9. Deploy to Production

### Frontend on Netlify

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Netlify:**
   - Go to https://app.netlify.com
   - **Option A:** Drag and drop the `frontend/dist` folder (no build settings needed)
   - **Option B:** Connect your Git repository (recommended for auto-deploys)

3. **If using Git-based deploy, configure build settings:**
   
   In Netlify → **Site settings → Build & deploy → Build settings**, set:
   
   | Setting | Value |
   |---------|-------|
   | **Base directory** | `frontend` |
   | **Build command** | `npm run build` |
   | **Publish directory** | `frontend/dist` |

4. **Set environment variable:**
   - In Netlify: **Site settings → Environment variables**
   - Add: `VITE_API_URL` = `https://your-api-host.com/api/v1`
   - Use your deployed backend API URL (from Render/Railway/etc.)
   - **Redeploy** after adding the variable

### Backend on Cloud Host

Deploy your FastAPI backend to:
- **Render** (recommended): Free tier, easy setup
- **Railway**: Simple deployment
- **Fly.io**: More control

#### Render Deployment Settings

**⚠️ Prerequisite: MongoDB Atlas**
You need a MongoDB Atlas cluster before the app will work on Render. The app requires a database connection at startup. You can set up Atlas in parallel with your Render deployment.

**Quick MongoDB Atlas Setup (5-10 minutes):**
1. Sign up at https://www.mongodb.com/cloud/atlas
2. Create a free M0 cluster (takes ~5 minutes to provision)
3. Create a database user (Database Access → Add New User)
4. Whitelist IP addresses (Network Access → Add IP Address → Allow Access from Anywhere: `0.0.0.0/0`)
5. Get connection string (Database → Connect → Connect your application) #would this use python?
#yes, it would use python.
6. Copy the connection string (format: `mongodb+srv://username:password@cluster.mongodb.net/news_sentiment`)

When creating a new Web Service on Render:

**Required Settings:**
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt` (or leave blank if auto-detected)
- **Start Command:** `uvicorn news_sentiment.api.main:app --host 0.0.0.0 --port $PORT`
  - ⚠️ **Critical:** The start command is required. Render sets the `$PORT` environment variable automatically.
  - `--host 0.0.0.0` allows external connections
  - The app path is `news_sentiment.api.main:app`

**Root Directory:**
- **Not needed** if deploying from the `news-sentiment-comparison` directory
- Only specify if deploying from a parent monorepo (set to `news-sentiment-comparison`)

**Environment Variables:**
Set these in Render dashboard → Environment:
- `NEWS_API_KEY` - Your NewsAPI key
- `GROQ_API_KEY` - Your Groq API key (or use `OPENAI_API_KEY` instead)
- `MONGODB_URI` - MongoDB Atlas connection string (⚠️ **Required** - app won't start without it)
- `CORS_ORIGINS` - Comma-separated list, e.g., `https://your-site.netlify.app,http://localhost:3000`

**Note:** You can create the Render service first and add the `MONGODB_URI` environment variable once you have your Atlas connection string. The app will connect on the next deploy/restart.

**Set up cron on cloud host:**
- Render: Use "Cron Job" service type
- Railway: Use scheduled tasks
- Or use external cron service (cron-job.org) to call an API endpoint

See README.md for detailed deployment instructions.

## Next Steps

- Customize news sources in `config.py`
- Add more visualizations to the dashboard
- Deploy to production for 24/7 availability
