import requests
import json
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)
BASE_URL = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")

COINS = [
    "bitcoin", "ethereum", "solana", "cardano", "polkadot",
    "chainlink", "avalanche-2", "uniswap", "litecoin", "dogecoin",
]
def save_raw_data(data: list, extracted_at: str) -> str:
    """
    Saves raw API response to a local JSON file.
    Returns the file path where data was saved.
    """
    # Build folder path with date partitioning
    dt = datetime.fromisoformat(extracted_at)
    folder = f"data/raw/coingecko/year={dt.year}/month={dt.month:02d}/day={dt.day:02d}"
    
    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    
    # Build filename with timestamp
    timestamp = dt.strftime("%Y%m%dT%H%M%SZ")
    filepath = f"{folder}/market_data_{timestamp}.json"
    
    # Build the envelope — raw data + metadata
    payload = {
        "extracted_at": extracted_at,
        "source": "coingecko",
        "endpoint": "/coins/markets",
        "coin_count": len(data),
        "data": data,
    }
    
    # Save to disk
    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)
    
    logger.info(f"Saved {len(data)} coins to {filepath}")
    return filepath

def extract_market_data():
    logger.info(f"Starting extraction for {len(COINS)} coins")
    
    params = {
        "vs_currency": "usd",
        "ids": ",".join(COINS),
        "order": "market_cap_desc",
        "sparkline": False,
    }
    
    max_retries = 3
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        logger.info(f"Attempt {attempt} of {max_retries}")

        try:
            response = requests.get(
                f"{BASE_URL}/coins/markets",
                params=params,
                timeout=30,
            )

            # Rate limited
            if response.status_code == 429:
                wait = 2 ** attempt
                logger.warning(f"Rate limited (429). Waiting {wait}s before retry.")
                time.sleep(wait)
                continue

            # Server error
            if response.status_code >= 500:
                wait = 2 ** attempt
                logger.warning(f"Server error ({response.status_code}). Waiting {wait}s.")
                time.sleep(wait)
                continue

            # Bad request - don't retry
            if response.status_code == 400:
                logger.error(f"Bad request (400) - check your params: {response.text}")
                raise ValueError(f"Bad request: {response.text}")

            # Auth error - don't retry
            if response.status_code in (401, 403):
                logger.error(f"Auth error ({response.status_code}) - check your API key")
                raise ValueError(f"Auth error: {response.status_code}")

            # Success
            if response.status_code == 200:
                data = response.json()
                extracted_at = datetime.now(timezone.utc).isoformat()
                logger.info(f"Extracted {len(data)} coins successfully")
                filepath = save_raw_data(data, extracted_at)
                return data, filepath

        except requests.Timeout:
            wait = 2 ** attempt
            logger.warning(f"Timeout on attempt {attempt}. Waiting {wait}s.")
            time.sleep(wait)
            continue

        except requests.ConnectionError as e:
            wait = 2 ** attempt
            logger.warning(f"Connection error on attempt {attempt}: {e}. Waiting {wait}s.")
            time.sleep(wait)
            continue

    logger.error(f"All {max_retries} retries exhausted. Extraction failed.")
    raise RuntimeError(f"Failed to extract data after {max_retries} retries")