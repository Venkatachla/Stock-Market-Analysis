import io
import pandas as pd
import requests
from utils.logger import get_logger

logger = get_logger(__name__)
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_nse_tickers() -> list[str]:
    """
    Download the official NSE equity list and return Yahoo-formatted tickers.
    Falls back to an empty list if the download fails so the caller can handle.
    """
    try:
        resp = requests.get(NSE_EQUITY_LIST_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        symbols = df['SYMBOL'].dropna().unique().tolist()
        tickers = [f"{s.strip()}.NS" for s in symbols if isinstance(s, str) and s.strip()]
        logger.info("Fetched %d NSE tickers", len(tickers))
        return tickers
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch NSE tickers: %s", exc)
        return []
