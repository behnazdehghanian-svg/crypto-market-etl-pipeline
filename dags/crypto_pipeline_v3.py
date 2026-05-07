import os
import json
from datetime import datetime, timedelta, timezone
from airflow import DAG
from airflow.operators.bash import BashOperator

# ── Paths ──────────────────────────────────────────────────────────────────────
PIPELINE_DIR = '/Users/behnazdehghanian/Documents/crypto-pipeline/crypto-market-etl-pipeline'
VENV_PYTHON  = f'{PIPELINE_DIR}/.venv/bin/python'
VENV_DBT     = f'{PIPELINE_DIR}/.venv/bin/dbt'
DBT_DIR      = f'{PIPELINE_DIR}/crypto_market_dbt'
DBT_PROFILES = '/Users/behnazdehghanian/.dbt'
TEMP_FILE    = '/tmp/crypto_market_data.json'

# ── Default args ───────────────────────────────────────────────────────────────
default_args = {
    'owner': 'behnaz',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email_on_retry': True,
    'email': ['behnazdehghanian@gmail.com'],
}

# ── DAG ────────────────────────────────────────────────────────────────────────
with DAG(
    dag_id='crypto_pipeline_v3',
    default_args=default_args,
    description='Crypto market ETL: CoinGecko → GCS → BigQuery → dbt',
    start_date=datetime(2026, 1, 1),
    schedule_interval='0 6 * * *',
    catchup=False,
    tags=['crypto', 'etl', 'bigquery', 'dbt'],
) as dag:

    # ── Task 1: Extract ────────────────────────────────────────────────────────
    extract = BashOperator(
        task_id='extract',
        bash_command=f"""
            {VENV_PYTHON} -c "
import sys, json
sys.path.insert(0, '{PIPELINE_DIR}')
from dotenv import load_dotenv
load_dotenv('{PIPELINE_DIR}/.env')
from src.extractors.coingecko import extract_market_data
from datetime import datetime, timezone
data, filepath = extract_market_data()
extracted_at = datetime.now(timezone.utc).isoformat()
payload = {{'data': data, 'extracted_at': extracted_at}}
with open('{TEMP_FILE}', 'w') as f:
    json.dump(payload, f)
print(f'Extracted {{len(data)}} coins. Saved to {TEMP_FILE}')
"
        """,
    )
    # ── Task 2: Upload to GCS ─────────────────────────────────────────────────
    upload_to_gcs = BashOperator(
        task_id='upload_to_gcs',
        bash_command=f"""
            {VENV_PYTHON} -c "
import sys, json, os
sys.path.insert(0, '{PIPELINE_DIR}')
from dotenv import load_dotenv
load_dotenv('{PIPELINE_DIR}/.env')
from src.load.gcs_client import GCSClient

# Read data from temp file
with open('{TEMP_FILE}', 'r') as f:
    payload = json.load(f)

data = payload['data']
extracted_at = payload['extracted_at']

# Upload to GCS
gcs = GCSClient(bucket_name=os.getenv('GCS_BUCKET_NAME'))
gcs_uri = gcs.upload_raw_data(data=data, extracted_at=extracted_at)

# Save GCS URI to temp file for next task
payload['gcs_uri'] = gcs_uri
with open('{TEMP_FILE}', 'w') as f:
    json.dump(payload, f)

print(f'Uploaded to {{gcs_uri}}')
"
        """,
    )
    # ── Task 3: Load to BigQuery ───────────────────────────────────────────────
    load_to_bigquery = BashOperator(
        task_id='load_to_bigquery',
        bash_command=f"""
            {VENV_PYTHON} -c "
import sys, json, os
sys.path.insert(0, '{PIPELINE_DIR}')
from dotenv import load_dotenv
load_dotenv('{PIPELINE_DIR}/.env')
from src.load.bigquery_client import BigQueryClient

# Read GCS URI from temp file
with open('{TEMP_FILE}', 'r') as f:
    payload = json.load(f)

gcs_uri = payload['gcs_uri']

# Load into BigQuery
bq = BigQueryClient(
    project_id=os.getenv('GCP_PROJECT_ID'),
    dataset_id=os.getenv('BIGQUERY_DATASET'),
)
bq.create_table_if_not_exists(table_id='crypto_market')
bq.load_from_gcs(gcs_uri=gcs_uri, table_id='crypto_market')

print(f'Loaded data from {{gcs_uri}} into BigQuery')
"
        """,
    )
    # ── Task 4: dbt run ────────────────────────────────────────────────────────
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f'cd {DBT_DIR} && {VENV_DBT} run --profiles-dir {DBT_PROFILES}',
    )

    # ── Task 5: dbt test ───────────────────────────────────────────────────────
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=f'cd {DBT_DIR} && {VENV_DBT} test --profiles-dir {DBT_PROFILES}',
    )

    # ── Task order ─────────────────────────────────────────────────────────────
    extract >> upload_to_gcs >> load_to_bigquery >> dbt_run >> dbt_test
