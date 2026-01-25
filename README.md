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

### Daily Collection (APScheduler)

Coming soon - scheduler will run daily at 6 AM by default.

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

## Next Steps

- [ ] React frontend dashboard
- [ ] Daily automation scheduler
- [ ] Email summaries
- [ ] Historical trend analysis
- [ ] Export capabilities (CSV, JSON)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
