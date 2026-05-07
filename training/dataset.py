from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from features.engineer import FEATURE_COLUMNS


@dataclass
class Dataset:
    X_train: np.ndarray
    X_val: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray
    y_test: np.ndarray
    scaler: StandardScaler
    feature_names: list[str]
    walk_forward_folds: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]


def add_lag_features(df: pd.DataFrame, cols: list[str], max_lag: int = 5) -> pd.DataFrame:
    out = df.copy()
    group_cols = ["stock_symbol"] if "stock_symbol" in out.columns else None
    for col in cols:
        if col not in out.columns:
            continue
        for lag in range(1, max_lag + 1):
            lag_col = f"{col}_lag_{lag}"
            if group_cols:
                out[lag_col] = out.groupby(group_cols)[col].shift(lag)
            else:
                out[lag_col] = out[col].shift(lag)
    return out


def _time_boundaries(df: pd.DataFrame, n_splits: int = 4) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    dates = pd.to_datetime(df["date"]).sort_values().unique()
    if len(dates) < 120:
        return []
    boundaries: list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]] = []
    for i in range(1, n_splits + 1):
        train_end_idx = int(len(dates) * (0.45 + 0.1 * i))
        test_end_idx = int(len(dates) * (0.55 + 0.1 * i))
        if train_end_idx >= len(dates) - 5:
            break
        train_end = dates[min(train_end_idx, len(dates) - 6)]
        test_end = dates[min(test_end_idx, len(dates) - 1)]
        val_end_idx = int(train_end_idx * 0.9)
        val_end = dates[max(10, min(val_end_idx, train_end_idx - 1))]
        boundaries.append((pd.Timestamp(val_end), pd.Timestamp(train_end), pd.Timestamp(test_end)))
    return boundaries


def _scale_by_stock(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    global_scaler = StandardScaler().fit(train_df[feature_cols])

    def _transform(frame: pd.DataFrame) -> np.ndarray:
        if frame.empty:
            return np.zeros((0, len(feature_cols)))
        if "stock_symbol" not in frame.columns:
            return global_scaler.transform(frame[feature_cols])
        transformed_parts: list[np.ndarray] = []
        for sym, grp in frame.groupby("stock_symbol", sort=False):
            ref = train_df[train_df["stock_symbol"] == sym]
            if len(ref) < 30:
                transformed_parts.append(global_scaler.transform(grp[feature_cols]))
                continue
            local_scaler = StandardScaler().fit(ref[feature_cols])
            transformed_parts.append(local_scaler.transform(grp[feature_cols]))
        return np.concatenate(transformed_parts, axis=0) if transformed_parts else np.zeros((0, len(feature_cols)))

    return _transform(train_df), _transform(val_df), _transform(test_df), global_scaler


def prepare_dataset(df: pd.DataFrame, n_splits: int = 4, normalize_per_stock: bool = True, max_lag: int = 5) -> Dataset:
    work_df = df.copy()
    work_df["date"] = pd.to_datetime(work_df["date"])
    work_df.sort_values(["date", "stock_symbol"], inplace=True)

    lag_base_cols = [
        "daily_return",
        "rolling_vol",
        "volume_change",
        "momentum",
        "rsi",
    ]
    work_df = add_lag_features(work_df, lag_base_cols, max_lag=max_lag)

    lag_cols = [f"{c}_lag_{i}" for c in lag_base_cols for i in range(1, max_lag + 1)]
    feature_cols = list(FEATURE_COLUMNS) + [c for c in lag_cols if c in work_df.columns]
    work_df.dropna(subset=feature_cols + ["target"], inplace=True)

    boundaries = _time_boundaries(work_df, n_splits=n_splits)
    if not boundaries:
        raise ValueError("Not enough data for strict walk-forward splitting")

    folds: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    final_train_df = final_val_df = final_test_df = pd.DataFrame()
    for val_end, train_end, test_end in boundaries:
        train_df = work_df[work_df["date"] <= train_end].copy()
        val_df = train_df[train_df["date"] > val_end].copy()
        train_df = train_df[train_df["date"] <= val_end].copy()
        test_df = work_df[(work_df["date"] > train_end) & (work_df["date"] <= test_end)].copy()
        if train_df.empty or val_df.empty or test_df.empty:
            continue
        if normalize_per_stock:
            X_train_f, X_val_f, X_test_f, _ = _scale_by_stock(train_df, val_df, test_df, feature_cols)
        else:
            fold_scaler = StandardScaler().fit(train_df[feature_cols])
            X_train_f = fold_scaler.transform(train_df[feature_cols])
            _X_val_f = fold_scaler.transform(val_df[feature_cols])
            X_test_f = fold_scaler.transform(test_df[feature_cols])
        folds.append((X_train_f, train_df["target"].values, X_test_f, test_df["target"].values))
        final_train_df, final_val_df, final_test_df = train_df, val_df, test_df

    if final_train_df.empty or final_test_df.empty or final_val_df.empty:
        raise ValueError("Walk-forward split construction failed")

    if normalize_per_stock:
        X_train, X_val, X_test, scaler = _scale_by_stock(final_train_df, final_val_df, final_test_df, feature_cols)
    else:
        scaler = StandardScaler().fit(final_train_df[feature_cols])
        X_train = scaler.transform(final_train_df[feature_cols])
        X_val = scaler.transform(final_val_df[feature_cols])
        X_test = scaler.transform(final_test_df[feature_cols])

    y_train = final_train_df["target"].values
    y_val = final_val_df["target"].values
    y_test = final_test_df["target"].values

    return Dataset(
        X_train=X_train,
        X_val=X_val,
        X_test=X_test,
        y_train=y_train,
        y_val=y_val,
        y_test=y_test,
        scaler=scaler,
        feature_names=feature_cols,
        walk_forward_folds=folds,
    )


def make_sequences(X: np.ndarray, y: np.ndarray, lookback: int = 30) -> Tuple[np.ndarray, np.ndarray]:
    X_seq, y_seq = [], []
    for i in range(len(X) - lookback):
        X_seq.append(X[i : i + lookback])
        y_seq.append(y[i + lookback])
    return np.array(X_seq), np.array(y_seq)
