#!/bin/bash
# Wrapper script for daily news collection cron job

# Change to project directory
cd /Users/rebeccaclarke/Documents/Financial/Gigs/devops_software_engineering/conceptprojects/news-sentiment-comparison

# Activate virtual environment
source .venv/bin/activate

# Run the collector
python scripts/run_collector.py

# Exit with the script's exit code
exit $?