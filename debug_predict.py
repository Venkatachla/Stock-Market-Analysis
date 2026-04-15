#!/usr/bin/env python3
"""Debug script to test predict_single function."""
import sys
import traceback

sys.path.insert(0, '.')

from api.server import (
    predict_single, resolve_symbol, yahoo_symbol, 
    load_models, fetch_history, compute_features_from_history,
    FEATURE_COLUMNS
)

print('[DEBUG] Testing predict_single()')
print('=' * 70)

try:
    result = predict_single('RELIANCE.NS')
    print('[SUCCESS] Prediction completed!')
    import json
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f'[ERROR] {e}')
    traceback.print_exc()
    
    # Try to debug step by step
    print('\n\n[DEBUG] Step-by-step debugging:')
    print('-' * 70)
    
    symbol = 'RELIANCE.NS'
    print(f'1. Resolving symbol: {symbol}')
    sym_resolved, name_resolved, suggestions = resolve_symbol(symbol)
    print(f'   -> {sym_resolved}, {name_resolved}')
    
    print(f'2. Converting to Yahoo symbol')
    ticker = yahoo_symbol(sym_resolved)
    print(f'   -> {ticker}')
    
    print(f'3. Loading models')
    models = load_models()
    print(f'   -> Models loaded: xgb={models["xgb"] is not None}, lgbm={models["lgbm"] is not None}, scaler={models["scaler"] is not None}')
    
    print(f'4. Fetching history')
    hist = fetch_history(ticker)
    print(f'   -> History type: {type(hist)}')
    print(f'   -> History shape: {hist.shape if hasattr(hist, "shape") else "N/A"}')
    print(f'   -> Columns type: {type(hist.columns)}')
    print(f'   -> Columns: {list(hist.columns)[:3]}...')
    
    print(f'5. Computing features')
    features_df = compute_features_from_history(hist)
    print(f'   -> Features: {features_df.shape if features_df is not None else "None"}')
    print('[SUCCESS] No more errors!')
