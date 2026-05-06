from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier

from data.multi_timeframe import align_daily_trend_to_intraday, fetch_multi_timeframe_data
from features.multi_strategy import (
    FEATURE_SET_INTRADAY,
    FEATURE_SET_OPTIONS,
    FEATURE_SET_SWING,
    build_feature_frame,
)


@dataclass
class StrategyArtifacts:
    model: object
    features: list[str]
    auc: float


@dataclass
class MultiStrategyBundle:
    swing: StrategyArtifacts
    intraday: StrategyArtifacts
    options_directional: StrategyArtifacts
    volatility: StrategyArtifacts


def _select_features(frame: pd.DataFrame, candidate_features: list[str], top_k: int = 16) -> list[str]:
    cols = [c for c in candidate_features if c in frame.columns]
    if len(cols) <= top_k:
        return cols
    xgb = XGBClassifier(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
    )
    xgb.fit(frame[cols], frame["target_up"], sample_weight=frame["sample_weight"])
    importance = xgb.feature_importances_
    ranking = sorted(zip(cols, importance), key=lambda t: t[1], reverse=True)
    return [name for name, _ in ranking[:top_k]]


def _train_with_timeseries_cv(frame: pd.DataFrame, features: list[str], complexity: str = "medium") -> StrategyArtifacts:
    if frame.empty:
        raise ValueError("No training data available")

    params = dict(n_estimators=200, max_depth=4, min_samples_leaf=15, random_state=42, n_jobs=-1)
    if complexity == "low":
        params.update(dict(n_estimators=120, max_depth=3, min_samples_leaf=20))

    tscv = TimeSeriesSplit(n_splits=5)
    auc_scores: list[float] = []

    X = frame[features]
    y = frame["target_up"].values
    w = frame["sample_weight"].values

    for tr_idx, te_idx in tscv.split(X):
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y[tr_idx], y[te_idx]
        w_tr = w[tr_idx]

        clf = RandomForestClassifier(**params)
        clf.fit(X_tr, y_tr, sample_weight=w_tr)
        prob = clf.predict_proba(X_te)[:, 1]
        if len(np.unique(y_te)) > 1:
            auc_scores.append(float(roc_auc_score(y_te, prob)))

    final_model = RandomForestClassifier(**params)
    final_model.fit(X, y, sample_weight=w)
    auc = float(np.mean(auc_scores)) if auc_scores else 0.5
    return StrategyArtifacts(model=final_model, features=features, auc=auc)


def train_multi_strategy_for_symbol(symbol: str) -> MultiStrategyBundle:
    tf = fetch_multi_timeframe_data(symbol)
    index_tf = fetch_multi_timeframe_data("^NSEI")

    swing_df = build_feature_frame(tf.daily, index_tf.daily)

    intraday_60 = align_daily_trend_to_intraday(tf.daily, tf.h1)
    intraday_15 = align_daily_trend_to_intraday(tf.daily, tf.m15)
    intraday_5 = align_daily_trend_to_intraday(tf.daily, tf.m5)
    intraday_df = pd.concat([
        build_feature_frame(intraday_60, index_tf.h1 if not index_tf.h1.empty else index_tf.daily),
        build_feature_frame(intraday_15, index_tf.m15 if not index_tf.m15.empty else index_tf.daily),
        build_feature_frame(intraday_5, index_tf.m5 if not index_tf.m5.empty else index_tf.daily),
    ]).sort_index()

    options_df = swing_df.copy()
    options_df["target_up"] = (options_df["ret_1"].shift(-1) > 0).astype(int)

    vol_df = swing_df.copy()
    vol_df["target_up"] = (vol_df["iv_percentile"].shift(-1) > vol_df["iv_percentile"]).astype(int)

    swing_features = _select_features(swing_df, FEATURE_SET_SWING, top_k=18)
    intraday_features = _select_features(intraday_df, FEATURE_SET_INTRADAY, top_k=12)
    options_features = _select_features(options_df, FEATURE_SET_OPTIONS, top_k=10)
    vol_features = _select_features(vol_df, FEATURE_SET_OPTIONS, top_k=10)

    swing_art = _train_with_timeseries_cv(swing_df, swing_features, complexity="medium")
    intraday_art = _train_with_timeseries_cv(intraday_df, intraday_features, complexity="low")
    options_art = _train_with_timeseries_cv(options_df, options_features, complexity="low")
    vol_art = _train_with_timeseries_cv(vol_df, vol_features, complexity="low")

    return MultiStrategyBundle(
        swing=swing_art,
        intraday=intraday_art,
        options_directional=options_art,
        volatility=vol_art,
    )


def save_multi_strategy(bundle: MultiStrategyBundle, symbol: str, path: str = "models") -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    out_path = str(Path(path) / f"multi_strategy_{symbol.upper()}.pkl")
    joblib.dump(bundle, out_path)
    return out_path


def load_multi_strategy(symbol: str, path: str = "models") -> MultiStrategyBundle:
    return joblib.load(str(Path(path) / f"multi_strategy_{symbol.upper()}.pkl"))


def predict_strategy(bundle: MultiStrategyBundle, features_row: pd.Series, trade_type: str) -> tuple[float, float]:
    trade_type = trade_type.lower()
    if trade_type == "swing":
        art = bundle.swing
    elif trade_type == "intraday":
        art = bundle.intraday
    elif trade_type == "options":
        art = bundle.options_directional
    elif trade_type == "volatility":
        art = bundle.volatility
    else:
        raise ValueError("Unknown trade_type")

    x = pd.DataFrame([features_row.reindex(art.features).fillna(0.0)])
    p = float(art.model.predict_proba(x)[:, 1][0])
    confidence = float(min(100.0, max(0.0, abs(p - 0.5) * 200.0)))
    return p, confidence
