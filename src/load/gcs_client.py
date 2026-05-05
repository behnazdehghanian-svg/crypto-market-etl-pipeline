import json
from datetime import datetime
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from src.logger import get_logger

logger = get_logger(__name__)


class GCSClient:
    """
    Handles uploading raw crypto data to Google Cloud Storage.
    Mirrors the same partitioned folder structure used for local saves.
    """

    def __init__(self, bucket_name: str):
        """
        Initialize GCS client and verify bucket access.

        Args:
            bucket_name: GCS bucket name (without gs://)
        """
        self.bucket_name = bucket_name
        self._client = storage.Client()
        self._bucket = self._get_bucket()

    def _get_bucket(self) -> storage.Bucket:
        """Fetch and validate bucket exists and is accessible."""
        try:
            bucket = self._client.get_bucket(self.bucket_name)
            logger.info(f"Connected to GCS bucket: {self.bucket_name}")
            return bucket
        except GoogleCloudError as e:
            logger.error(f"Cannot access bucket '{self.bucket_name}': {e}")
            raise

    def _build_blob_path(self, extracted_at: str) -> str:
        """
        Build a partitioned GCS path from the extraction timestamp.

        Mirrors your local structure:
          data/raw/coingecko/year=2025/month=04/day=28/market_data_20250428T143000Z.json

        Args:
            extracted_at: ISO format UTC timestamp string

        Returns:
            Full blob path string
        """
        dt = datetime.fromisoformat(extracted_at)
        folder = (
            f"coingecko/raw/"
            f"year={dt.year}/"
            f"month={dt.month:02d}/"
            f"day={dt.day:02d}"
        )
        timestamp = dt.strftime("%Y%m%dT%H%M%SZ")
        return f"{folder}/market_data_{timestamp}.json"

    def upload_raw_data(self, data: list, extracted_at: str) -> str:
        """
        Upload raw crypto market data to GCS as a NDJSON file.
        One coin per line — format BigQuery expects.
        Only keeps fields that match our BigQuery schema.
        """
        if not data:
            raise ValueError("Cannot upload empty data to GCS.")

        blob_path = self._build_blob_path(extracted_at)

        # Only keep fields that exist in our BigQuery schema
        fields_to_keep = [
            "id", "symbol", "name", "image", "current_price",
            "market_cap", "market_cap_rank", "fully_diluted_valuation",
            "total_volume", "high_24h", "low_24h", "price_change_24h",
            "price_change_percentage_24h", "market_cap_change_24h",
            "market_cap_change_percentage_24h", "circulating_supply",
            "total_supply", "max_supply", "ath", "ath_change_percentage",
            "ath_date", "atl", "atl_change_percentage", "atl_date",
            "last_updated",
        ]

        try:
            lines = []
            for coin in data:
                # Keep only schema fields + add extracted_at
                clean_coin = {field: coin.get(field) for field in fields_to_keep}
                clean_coin["extracted_at"] = extracted_at
                lines.append(json.dumps(clean_coin))

            ndjson_string = "\n".join(lines)

            blob = self._bucket.blob(blob_path)
            blob.upload_from_string(
                data=ndjson_string,
                content_type="application/json",
            )

            gcs_uri = f"gs://{self.bucket_name}/{blob_path}"
            logger.info(f"Uploaded {len(data)} coins to GCS: {gcs_uri}")
            return gcs_uri

        except GoogleCloudError as e:
            logger.error(f"GCS upload failed for path '{blob_path}': {e}")
            raise