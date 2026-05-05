# Crypto Market ETL Pipeline

I built this pipeline as part of my journey to become a senior data engineer. It pulls live crypto prices from the CoinGecko API every morning, stores the raw data in Google Cloud Storage, loads it into BigQuery, and transforms it with dbt — all automatically.

## Why I built this

I wanted to go beyond tutorials and build something real on GCP. This pipeline runs in production, handles errors gracefully, and follows the same patterns used by data engineering teams at real companies.

## What it does

Every day at 6am it wakes up, grabs the latest market data for 10 coins, and loads it into BigQuery. By the time I start my day the data is already there waiting for me.

The 10 coins I track: Bitcoin, Ethereum, Solana, Cardano, Polkadot, Chainlink, Avalanche, Uniswap, Litecoin, Dogecoin.

## How it works

CoinGecko API → Python → Google Cloud Storage → BigQuery → dbt

1. Python hits the CoinGecko API and pulls current prices, market caps, volumes and more
2. Raw JSON gets uploaded to GCS in a partitioned folder structure (year/month/day)
3. BigQuery loads the file from GCS into a raw table
4. dbt cleans and renames the columns into a proper staging table
5. dbt tests run automatically to catch any data quality issues

## Tech stack

- Python 3.11 for extract and load
- Google Cloud Storage as the raw data lake
- BigQuery as the data warehouse
- dbt for transformations and data quality tests
- Cron for scheduling

## Running it locally

git clone https://github.com/YOUR_USERNAME/crypto-market-etl-pipeline.git
cd crypto-market-etl-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py

## What I learned building this

- How to design a partitioned data lake on GCS
- How BigQuery load jobs work and how to handle schema mismatches
- Why NDJSON matters and how it differs from regular JSON
- How dbt connects to BigQuery and what makes a good staging model
- How to handle API rate limits, retries, and failures gracefully
- How to use IAM roles properly instead of giving everything admin access

## What is next

This is Pipeline 1 of several I am building. Next up is adding more coins, scheduling dbt runs, setting up alerting, and eventually moving the orchestration from cron to a proper tool like Cloud Composer or Prefect.
