import os
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from src.logger import get_logger

logger = get_logger(__name__)


class BigQueryClient:
    """
    Handles loading raw crypto data from GCS into BigQuery.
    """

    def __init__(self, project_id: str, dataset_id: str):
        """
        Initialize BigQuery client.

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self._client = bigquery.Client(project=project_id)
        logger.info(f"Connected to BigQuery project: {project_id}")

    def _get_schema(self) -> list:
        """
        Define the BigQuery table schema.
        Each field matches the coin data from CoinGecko.
        """
        return [
            bigquery.SchemaField("id",                              "STRING"),
            bigquery.SchemaField("symbol",                          "STRING"),
            bigquery.SchemaField("name",                            "STRING"),
            bigquery.SchemaField("image",                            "STRING"),
            bigquery.SchemaField("current_price",                   "FLOAT"),
            bigquery.SchemaField("market_cap",                      "FLOAT"),
            bigquery.SchemaField("market_cap_rank",                 "INTEGER"),
            bigquery.SchemaField("fully_diluted_valuation",         "FLOAT"),
            bigquery.SchemaField("total_volume",                    "FLOAT"),
            bigquery.SchemaField("high_24h",                        "FLOAT"),
            bigquery.SchemaField("low_24h",                         "FLOAT"),
            bigquery.SchemaField("price_change_24h",                "FLOAT"),
            bigquery.SchemaField("price_change_percentage_24h",     "FLOAT"),
            bigquery.SchemaField("market_cap_change_24h",           "FLOAT"),
            bigquery.SchemaField("market_cap_change_percentage_24h","FLOAT"),
            bigquery.SchemaField("circulating_supply",              "FLOAT"),
            bigquery.SchemaField("total_supply",                    "FLOAT"),
            bigquery.SchemaField("max_supply",                      "FLOAT"),
            bigquery.SchemaField("ath",                             "FLOAT"),
            bigquery.SchemaField("ath_change_percentage",           "FLOAT"),
            bigquery.SchemaField("ath_date",                        "STRING"),
            bigquery.SchemaField("atl",                             "FLOAT"),
            bigquery.SchemaField("atl_change_percentage",           "FLOAT"),
            bigquery.SchemaField("atl_date",                        "STRING"),
            bigquery.SchemaField("last_updated",                    "STRING"),
            bigquery.SchemaField("extracted_at",                    "STRING"),
        ]

    def create_table_if_not_exists(self, table_id: str) -> None:
        """
        Create BigQuery table if it doesn't already exist.

        Args:
            table_id: Table name e.g. 'crypto_market'
        """
        full_table_id = f"{self.project_id}.{self.dataset_id}.{table_id}"

        try:
            self._client.get_table(full_table_id)
            logger.info(f"Table already exists: {full_table_id}")

        except Exception:
            # Table doesn't exist — create it
            table = bigquery.Table(full_table_id, schema=self._get_schema())
            self._client.create_table(table)
            logger.info(f"Created table: {full_table_id}")

    def load_from_gcs(self, gcs_uri: str, table_id: str) -> None:
        """
        Load raw JSON data from GCS into BigQuery.

        Args:
            gcs_uri:  Full GCS URI e.g. gs://bucket/path/file.json
            table_id: Target table name e.g. 'crypto_market'
        """
        full_table_id = f"{self.project_id}.{self.dataset_id}.{table_id}"

        # Tell BigQuery how to read our JSON file
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            schema=self._get_schema(),
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )

        try:
            logger.info(f"Starting BigQuery load job from: {gcs_uri}")
            load_job = self._client.load_table_from_uri(
                gcs_uri,
                full_table_id,
                job_config=job_config,
            )

            # Wait for the job to complete
            load_job.result()

            table = self._client.get_table(full_table_id)
            logger.info(f"✅ Loaded data into {full_table_id} — total rows: {table.num_rows}")

        except GoogleCloudError as e:
            logger.error(f"❌ BigQuery load failed: {e}")
            raise