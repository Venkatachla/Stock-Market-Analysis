from api.app import predict_single, SYMBOL_MAPPING
import yfinance as yf

for sym in ["NIFTY FINANCIAL SERVICES", "BSE BANKEX"]:
    pred = predict_single(sym)
    print(f"{sym} Prediction: {pred is not None}")
    
    ticker = SYMBOL_MAPPING.get(sym, sym)
    if not "." in ticker and not ticker.startswith("^"):
        ticker = f"{ticker}.NS"
    
    print(f"Testing ticker: {ticker}")
    tk = yf.Ticker(ticker)
    try:
        hist = tk.history(period="1mo")
        print(f"{sym} History length: {len(hist)}")
        options = tk.options
        print(f"{sym} Options: {options}")
    except Exception as e:
        print(f"{sym} Error: {e}")
