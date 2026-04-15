import numpy as np
import pandas as pd

from features.engineer import FEATURE_COLUMNS


THRESHOLD = 0.6


def ensemble_predict(df: pd.DataFrame, bundle, lookback: int = 30) -> pd.DataFrame:
    """Generate probabilities and signals for a processed feature DataFrame."""
    X = bundle.scaler.transform(df[FEATURE_COLUMNS])
    xgb_p = bundle.xgb.predict_proba(X)[:, 1]
    lgb_p = bundle.lgbm.predict_proba(X)[:, 1]
    rf_p = bundle.rf.predict_proba(X)[:, 1]
    lstm_p = np.zeros_like(xgb_p)
    if bundle.lstm is not None and len(df) > lookback:
        import torch
        from training.dataset import make_sequences
        X_seq, _ = make_sequences(X, np.zeros(len(X)), lookback=lookback)
        with torch.no_grad():
            preds = bundle.lstm(torch.tensor(X_seq, dtype=torch.float32)).squeeze().numpy()
            lstm_p = np.concatenate([np.zeros(lookback), preds])
    stacked = np.column_stack([xgb_p, lgb_p, rf_p, lstm_p])
    meta_model = getattr(bundle, "meta_model", None)
    if meta_model is not None:
        ensemble = meta_model.predict_proba(stacked)[:, 1]
    else:
        weights = getattr(bundle, "dynamic_weights", {"xgb": 0.4, "lgbm": 0.3, "rf": 0.2, "lstm": 0.1})
        ensemble = (
            weights.get("xgb", 0.4) * xgb_p
            + weights.get("lgbm", 0.3) * lgb_p
            + weights.get("rf", 0.2) * rf_p
            + weights.get("lstm", 0.1) * lstm_p
        )
    df_out = df.copy()
    df_out["prob_up"] = ensemble
    df_out["prob_down"] = 1 - ensemble
    df_out["confidence_score"] = (np.abs(df_out["prob_up"] - 0.5) * 200).clip(0, 100)
    df_out["signal"] = df_out["prob_up"].apply(lambda p: 1 if p > THRESHOLD else (-1 if p < (1 - THRESHOLD) else 0))
    return df_out


def position_size(capital: float, price: float, risk_per_trade: float = 0.01, stop_loss_pct: float = 0.02) -> int:
    risk_amount = capital * risk_per_trade
    per_share_risk = price * stop_loss_pct
    if per_share_risk == 0:
        return 0
    size = int(risk_amount / per_share_risk)
    return max(size, 0)
