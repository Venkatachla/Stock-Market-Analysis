import os
import requests
import yfinance as yf
from textblob import TextBlob
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")

def get_live_stock(symbol: str) -> dict:
    """Fetch live stock price and volume using yfinance."""
    try:
        # Append .NS for Indian stocks if needed or use ticker directly
        ticker = symbol if "." in symbol or symbol.startswith("^") else f"{symbol}.NS"
        stock = yf.Ticker(ticker)
        # Get live data (last 1 day, 1 minute interval)
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            latest = hist.iloc[-1]
            return {
                "price": float(latest["Close"]),
                "volume": int(latest["Volume"])
            }
        
        # Fallback to fast info
        return {
            "price": float(stock.fast_info.last_price),
            "volume": int(stock.fast_info.last_volume)
        }
    except Exception as e:
        print(f"Error fetching live stock for {symbol}: {e}")
        return {"price": 0.0, "volume": 0}

def get_news(symbol: str) -> list:
    """Fetch news articles related to the symbol from NewsAPI."""
    if not NEWS_API_KEY or NEWS_API_KEY == "your_news_api_key_here":
        print("NEWS_API_KEY not configured properly.")
        return []

    try:
        url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}&language=en&sortBy=publishedAt&pageSize=5"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []

def average_sentiment(articles: list) -> float:
    """Calculate average sentiment score of article titles using TextBlob (Normalized to 0-1)."""
    if not articles:
        return 0.5  # Neutral sentiment fallback

    total_sentiment = 0.0
    count = 0

    for article in articles:
        title = article.get("title")
        if title:
            # TextBlob sentiment ranges from -1.0 to 1.0
            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            
            # Normalize from [-1.0, 1.0] to [0.0, 1.0]
            normalized = (polarity + 1.0) / 2.0
            total_sentiment += normalized
            count += 1

    if count == 0:
        return 0.5
        
    return total_sentiment / count
