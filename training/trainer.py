import joblib
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from training.dataset import Dataset, make_sequences
from training.lstm_model import LSTMClassifier
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelBundle:
    def __init__(self):
        self.xgb = None
        self.lgbm = None
        self.rf = None
        self.lstm = None
        self.meta_model = None
        self.dynamic_weights = {"xgb": 0.4, "lgbm": 0.3, "rf": 0.2, "lstm": 0.1}
        self.scaler = None
        self.feature_names = []

    def save(self, path: str = "models") -> None:
        import os
        os.makedirs(path, exist_ok=True)
        joblib.dump({
            "xgb": self.xgb,
            "lgbm": self.lgbm,
            "rf": self.rf,
            "meta_model": self.meta_model,
            "dynamic_weights": self.dynamic_weights,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
        }, f"{path}/tree_models.pkl")
        if self.lstm is not None:
            torch.save(self.lstm.state_dict(), f"{path}/lstm.pt")
        logger.info("Models saved to %s", path)


def train_tree_models(data: Dataset) -> tuple:
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
    )
    lgbm = LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=64,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary",
    )
    rf = RandomForestClassifier(n_estimators=200, max_depth=8, n_jobs=-1)

    xgb.fit(data.X_train, data.y_train)
    lgbm.fit(data.X_train, data.y_train)
    rf.fit(data.X_train, data.y_train)

    logger.info("Tree models trained")
    return xgb, lgbm, rf


def train_lstm(data: Dataset, lookback: int = 30, epochs: int = 10, batch_size: int = 64, lr: float = 1e-3) -> LSTMClassifier:
    X_seq, y_seq = make_sequences(data.X_train, data.y_train, lookback=lookback)
    X_seq_test, y_seq_test = make_sequences(data.X_test, data.y_test, lookback=lookback)
    model = LSTMClassifier(input_size=X_seq.shape[2])
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_ds = TensorDataset(torch.tensor(X_seq, dtype=torch.float32), torch.tensor(y_seq, dtype=torch.float32))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            preds = model(xb).squeeze()
            loss = criterion(preds, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        logger.info("LSTM epoch %d loss %.4f", epoch + 1, epoch_loss / len(train_loader))

    # Quick eval
    if len(X_seq_test) > 0:
        model.eval()
        with torch.no_grad():
            preds = model(torch.tensor(X_seq_test, dtype=torch.float32)).squeeze().numpy()
            auc = roc_auc_score(y_seq_test, preds)
            logger.info("LSTM validation AUC %.3f", auc)
    return model


def evaluate_models(models: ModelBundle, data: Dataset) -> dict:
    xgb_probs = models.xgb.predict_proba(data.X_test)[:, 1]
    lgbm_probs = models.lgbm.predict_proba(data.X_test)[:, 1]
    rf_probs = models.rf.predict_proba(data.X_test)[:, 1]
    lstm_probs = np.zeros_like(xgb_probs)
    if models.lstm is not None:
        lookback = 30
        X_seq, y_seq = make_sequences(data.X_test, data.y_test, lookback=lookback)
        if len(X_seq) > 0:
            with torch.no_grad():
                preds = models.lstm(torch.tensor(X_seq, dtype=torch.float32)).squeeze().numpy()
                lstm_probs = np.concatenate([np.zeros(lookback), preds])  # pad to align length
    stacked_features = np.column_stack([xgb_probs, lgbm_probs, rf_probs, lstm_probs])
    if models.meta_model is not None:
        ensemble_probs = models.meta_model.predict_proba(stacked_features)[:, 1]
    else:
        w = models.dynamic_weights
        ensemble_probs = w["xgb"] * xgb_probs + w["lgbm"] * lgbm_probs + w["rf"] * rf_probs + w["lstm"] * lstm_probs
    y_pred = (ensemble_probs > 0.5).astype(int)
    report = classification_report(data.y_test, y_pred, output_dict=True)
    auc = roc_auc_score(data.y_test, ensemble_probs)
    logger.info("Ensemble AUC %.3f", auc)
    return {"report": report, "auc": auc}


def train_all_models(data: Dataset) -> ModelBundle:
    bundle = ModelBundle()
    xgb, lgbm, rf = train_tree_models(data)
    bundle.xgb, bundle.lgbm, bundle.rf = xgb, lgbm, rf
    try:
        lstm = train_lstm(data)
        bundle.lstm = lstm
    except Exception as exc:  # noqa: BLE001
        logger.error("LSTM training failed: %s", exc)
        bundle.lstm = None

    # Dynamic weighting from validation AUC scores.
    val_xgb = bundle.xgb.predict_proba(data.X_val)[:, 1]
    val_lgbm = bundle.lgbm.predict_proba(data.X_val)[:, 1]
    val_rf = bundle.rf.predict_proba(data.X_val)[:, 1]
    val_lstm = np.zeros_like(val_xgb)
    aucs = {
        "xgb": max(roc_auc_score(data.y_val, val_xgb), 1e-6),
        "lgbm": max(roc_auc_score(data.y_val, val_lgbm), 1e-6),
        "rf": max(roc_auc_score(data.y_val, val_rf), 1e-6),
        "lstm": 1e-6,
    }

    if bundle.lstm is not None and len(data.X_val) > 31:
        try:
            lookback = 30
            X_seq_val, y_seq_val = make_sequences(data.X_val, data.y_val, lookback=lookback)
            with torch.no_grad():
                preds = bundle.lstm(torch.tensor(X_seq_val, dtype=torch.float32)).squeeze().numpy()
                val_lstm = np.concatenate([np.zeros(lookback), preds])
                aucs["lstm"] = max(roc_auc_score(data.y_val, val_lstm), 1e-6)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LSTM validation failed for dynamic weights: %s", exc)

    auc_sum = sum(aucs.values())
    bundle.dynamic_weights = {k: float(v / auc_sum) for k, v in aucs.items()}

    # Stacking meta-model on validation predictions.
    meta_X = np.column_stack([val_xgb, val_lgbm, val_rf, val_lstm])
    meta_y = data.y_val
    if len(meta_X) > 100 and len(np.unique(meta_y)) > 1:
        meta_model = LogisticRegression(max_iter=1000)
        meta_model.fit(meta_X, meta_y)
        bundle.meta_model = meta_model
    else:
        bundle.meta_model = None

    bundle.scaler = data.scaler
    bundle.feature_names = list(data.feature_names)
    logger.info("All models trained")
    return bundle
