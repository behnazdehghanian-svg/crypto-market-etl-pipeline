import os
import sys
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="DEBUG")

def test_environment_variables():
    logger.info("Checking environment variables...")
    required_vars = ["GCP_PROJECT_ID", "GCS_BUCKET_NAME", "BIGQUERY_DATASET", "GOOGLE_APPLICATION_CREDENTIALS"]
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            logger.warning(f"  ⚠️  {var} is NOT set")
        else:
            logger.debug(f"  ✓  {var} = {value}")
    if missing:
        logger.error(f"❌ Missing: {missing}")
        return False
    logger.success("✅ All environment variables are set.")
    return True

def test_gcs_connection():
    from google.cloud import storage
    try:
        logger.info("Testing GCS connection...")
        client = storage.Client(project=os.getenv("GCP_PROJECT_ID"))
        buckets = list(client.list_buckets())
        logger.success(f"✅ GCS connected. Found {len(buckets)} existing buckets.")
        return True
    except Exception as e:
        logger.error(f"❌ GCS connection failed: {e}")
        return False

def test_bigquery_connection():
    from google.cloud import bigquery
    try:
        logger.info("Testing BigQuery connection...")
        client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
        query = "SELECT 1 AS test_value, CURRENT_TIMESTAMP() AS tested_at"
        result = client.query(query).result()
        for row in result:
            logger.success(f"✅ BigQuery connected. Result: {dict(row)}")
        return True
    except Exception as e:
        logger.error(f"❌ BigQuery connection failed: {e}")
        return False

def run_all_tests():
    logger.info("=" * 50)
    logger.info("🚀 Starting GCP Connection Tests")
    logger.info("=" * 50)
    results = {
        "Environment Variables": test_environment_variables(),
        "GCS Connection": test_gcs_connection(),
        "BigQuery Connection": test_bigquery_connection(),
    }
    logger.info("=" * 50)
    logger.info("📋 Results:")
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {status} — {test_name}")
        if not passed:
            all_passed = False
    logger.info("=" * 50)
    if all_passed:
        logger.success("🎉 All tests passed! Ready.")
    else:
        logger.error("💥 Fix the errors above first.")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
