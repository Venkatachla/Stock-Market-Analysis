from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
from tqdm import tqdm

from utils.logger import get_logger

logger = get_logger(__name__)


def download_history(tickers: list[str], years: int = 15, output_dir: str = "data/raw") -> None:
    """Download historical data for tickers and save as CSV in output_dir."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    end = datetime.utcnow()
    start = end - timedelta(days=365 * years)
    if not tickers:
        logger.warning("No tickers provided for download.")
        return

    for ticker in tqdm(tickers, desc="Downloading NSE data"):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if df.empty:
                logger.warning("No data for %s", ticker)
                continue
            # Ensure Close exists even if Adj Close missing
            if "Close" not in df.columns and "Adj Close" in df.columns:
                df["Close"] = df["Adj Close"]
            df.reset_index(inplace=True)
            df.rename(columns={"Date": "date"}, inplace=True)
            df.to_csv(Path(output_dir) / f"{ticker.replace('.NS','')}.csv", index=False)
        except Exception as exc:  # noqa: BLE001
            logger.error("Download failed for %s: %s", ticker, exc)

    logger.info("Download complete. Files saved to %s", output_dir)
