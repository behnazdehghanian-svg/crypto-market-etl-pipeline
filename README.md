# Crypto Market ETL Pipeline

A production-grade ETL pipeline that collects live cryptocurrency market data and loads it into Google BigQuery for analysis.

## How it works

CoinGecko API → Python → Google Cloud Storage → BigQuery → dbt

1. Pulls current prices, market caps and volumes for 10 coins from CoinGecko API
2. Stores raw JSON in Google Cloud Storage with date partitioning
3. Loads data into BigQuery
4. dbt transforms raw data into clean analysis-ready tables
5. Runs automatically every day via cron

## Coins tracked

Bitcoin, Ethereum, Solana, Cardano, Polkadot, Chainlink, Avalanche, Uniswap, Litecoin, Dogecoin

## Tech stack

- Python 3.11
- Google Cloud Storage
- BigQuery
- dbt
- Cron

## Running locally

```bash
git clone https://github.com/behnazdehghanian-svg/crypto-market-etl-pipeline.git
cd crypto-market-etl-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Environment variables

See `.env.example` for required configuration.
