import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone
from src.extractors.coingecko import extract_market_data
from src.load.gcs_client import GCSClient
from src.load.bigquery_client import BigQueryClient
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def run_pipeline():
    """
    Runs the full pipeline:
    Step 1: Extract crypto data from CoinGecko
    Step 2: Upload raw data to GCS
    Step 3: Load data from GCS into BigQuery
    """
    logger.info("Pipeline started")

    # Step 1: Extract
    logger.info("Step 1: Extracting data from CoinGecko...")
    data, local_filepath = extract_market_data()
    logger.info(f"Extraction done. Local file: {local_filepath}")

    # Step 2: Upload to GCS
    logger.info("Step 2: Uploading to GCS...")
    extracted_at = datetime.now(timezone.utc).isoformat()
    gcs = GCSClient(bucket_name=os.getenv("GCS_BUCKET_NAME"))
    gcs_uri = gcs.upload_raw_data(data=data, extracted_at=extracted_at)

    # Step 3: Load into BigQuery
    logger.info("Step 3: Loading into BigQuery...")
    bq = BigQueryClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        dataset_id=os.getenv("BIGQUERY_DATASET"),
    )
    bq.create_table_if_not_exists(table_id="crypto_market")
    bq.load_from_gcs(gcs_uri=gcs_uri, table_id="crypto_market")

    logger.info("✅ Pipeline complete!")

    


if __name__ == "__main__":
    
    try:
        run_pipeline()
        sys.exit(0)
    except EnvironmentError as e:
        logger.error(f"❌ Missing configuration: {e}")
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Pipeline failed with unexpected error: {e}")
        sys.exit(1)