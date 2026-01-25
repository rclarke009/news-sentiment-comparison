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

## Next Steps

- Set up daily automation (see README.md)
- Customize news sources in `config.py`
- Add more visualizations to the dashboard
