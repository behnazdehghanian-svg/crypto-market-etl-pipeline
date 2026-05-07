# Crypto Market ETL Pipeline

A production-grade ETL pipeline that collects live cryptocurrency market data and loads it into Google BigQuery for analysis, orchestrated by Apache Airflow.

## How it works

CoinGecko API → Python → Google Cloud Storage → BigQuery → dbt

1. Pulls current prices, market caps and volumes for 10 coins from CoinGecko API
2. Stores raw JSON in Google Cloud Storage with date partitioning
3. Loads data into BigQuery
4. dbt transforms raw data into clean analysis-ready tables
5. Runs automatically every day at 6am via Airflow

## Orchestration

The pipeline is orchestrated by Apache Airflow with 5 separate tasks:

extract → upload_to_gcs → load_to_bigquery → dbt_run → dbt_test

Each task is independent — if one fails only that task retries. Full visibility in Airflow UI.

## Coins tracked

Bitcoin, Ethereum, Solana, Cardano, Polkadot, Chainlink, Avalanche, Uniswap, Litecoin, Dogecoin

## Tech stack

- Python 3.11
- Google Cloud Storage
- BigQuery
- dbt
- Apache Airflow

## Project structure

crypto-market-etl-pipeline/
├── dags/
│   └── crypto_pipeline_v3.py
├── main.py
├── src/
│   ├── extractors/
│   │   └── coingecko.py
│   ├── load/
│   │   ├── gcs_client.py
│   │   └── bigquery_client.py
│   └── logger.py
├── crypto_market_dbt/
│   └── models/
│       └── staging/
│           ├── sources.yml
│           └── stg_crypto_market.sql
├── .env.example
├── requirements.txt
└── README.md

## Running locally

git clone https://github.com/behnazdehghanian-svg/crypto-market-etl-pipeline.git
cd crypto-market-etl-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py

## Running Airflow

Install Airflow in a separate virtual environment:
python -m venv airflow-env
source airflow-env/bin/activate
pip install apache-airflow==2.9.1

Initialize and start Airflow:
airflow db migrate
airflow webserver --port 8080
airflow scheduler

Then open http://localhost:8080 and trigger crypto_pipeline_v3.

## Environment variables

See .env.example for required configuration.
