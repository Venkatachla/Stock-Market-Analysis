# Assignment Report Content (Exact 8-Topic Format)

| Sl No | Content | Page No |
|---|---|---|
| 1 | Abstract | 1 |
| 2 | Introduction | 2 |
| 3 | Literature Study | 3 |
| 4 | Coding | 4 |
| 5 | Results Snapshots and Discussion | 5 |
| 6 | Conclusion | 6 |
| 7 | References | 7 |
| 8 | Literature Survey Proofs | 8 |

---

## 1. Abstract (Page 1)

This assignment implements an end-to-end stock market intelligence platform that combines high-frequency deep learning prediction, ensemble machine learning, sentiment-aware reasoning, and blockchain-based tamper-evident proof recording. The system predicts direction over multiple timeframes including intraday intervals and provides practical outputs such as signal type, confidence, trend interpretation, entry zone, stop loss, and target.

The implemented architecture integrates XGBoost, LightGBM, Random Forest, and LSTM models with dynamic weighting and robust API serving through FastAPI. For intraday use, the system processes true selected-timeframe candles (for example, 5-minute candles for 5-minute mode) and predicts the next corresponding candle direction. This makes prediction behavior operationally consistent and suitable for high-frequency analysis.

A major enhancement is the blockchain proof layer added to the production pipeline. Every stored prediction is cryptographically hashed and chained with previous block hash references in a verifiable sequence. The system includes live chain status, chain record listing, and per-prediction verification APIs, enabling transparent auditability and trust.

Compared with the referenced research paper, this implementation delivers a broader and deeper system: multi-model fusion, multi-timeframe real-time inference, dashboard analytics, portfolio and alert modules, and practical blockchain integrity verification in a running software product.

---

## 2. Introduction (Page 2)

Stock forecasting is inherently difficult because market movement is influenced by momentum, volatility, liquidity shifts, technical structure changes, and event-driven sentiment. Many systems provide static one-time predictions but do not offer operational consistency across timeframes, risk-aware signal outputs, or trustworthy audit logs.

This project is designed as a full-stack decision-support platform rather than a single-model experiment. It unifies:

- Multi-timeframe prediction from 1-minute to weekly frames.
- Intraday next-candle directional prediction logic.
- Ensemble + LSTM modeling for stronger generalization.
- Confidence and reason generation from technical + probabilistic evidence.
- Blockchain-style chained proof records for prediction integrity.

The core motivation is to create a deployable framework that is both technically advanced and demonstrably trustworthy. For academic relevance, it aligns with high-frequency deep learning research; for practical relevance, it adds APIs, dashboards, alerting, and verification mechanisms used in real systems.

Key system capabilities implemented:

1. True timeframe-aware inference.
2. Structured trade signal outputs for simulation.
3. Real-time dashboard views and API-driven automation.
4. Tamper-evident blockchain proof chain for all stored predictions.

---

## 3. Literature Study (Page 3)

The selected paper, High-Frequency Stock Market Price Prediction Using Blockchain and Deep Learning, emphasizes LSTM-based return-rate prediction and optimizer-guided performance improvements. It places blockchain in the trust layer context and evaluates performance mainly with error metrics.

From the literature direction, the most relevant themes are:

1. High-frequency temporal modeling with deep learning.
2. Optimizer-aware training stability and accuracy gains.
3. Need for trust and integrity over financial prediction records.

This project fully aligns with those themes and extends them in implementation depth:

- Deep Learning Core: LSTM is implemented and integrated with classical ML models.
- Optimizer Alignment: Adam-based training is implemented in the model training pipeline.
- High-Frequency Readiness: 5-minute and other intraday predictions use corresponding candle streams and next-candle objective.
- Trust Layer Realization: blockchain-style cryptographic hash chaining and verification APIs are implemented in live backend.

What is improved beyond paper-level scope:

- Ensemble fusion (XGB + LGBM + RF + LSTM) instead of single pipeline dependence.
- Real API and dashboard deployment for applied usage.
- Practical chain verification endpoints and visible blockchain status section.
- Alerting, portfolio analytics, and operational runtime validation.

Hence, the project translates research concepts into a scalable product-grade software architecture with measurable transparency.

---

## 4. Coding (Page 4)

### 4.1 Backend Design

The backend is implemented using FastAPI and modular Python services.

Core backend modules include:

- Data retrieval and feature engineering from OHLCV streams.
- Multi-timeframe model inference APIs.
- Signal generation and risk-related output construction.
- Backtest/performance and alert modules.
- Blockchain proof chain persistence and verification.

Important implemented endpoints include:

- /prediction/{symbol}?timeframe=...
- /candles?symbol=...&interval=...
- /alerts/live
- /portfolio/analytics
- /chain/status
- /chain/records
- /chain/verify/{prediction_id}

### 4.2 Model Pipeline

Implemented model stack:

1. XGBoost classifier
2. LightGBM classifier
3. Random Forest classifier
4. LSTM sequence model

Fusion approach:

- Dynamic weighted aggregation and optional meta-model usage.
- Confidence logic and structured textual reasoning.
- Intraday probability-dominant direction alignment for next-candle output.

### 4.3 Blockchain Proof Layer Coding

A cryptographic proof chain is implemented in the backend database.

For each saved prediction:

1. Canonical payload JSON is created.
2. payload_hash = SHA256(payload).
3. Latest previous block hash is read.
4. block_hash = SHA256(prediction_id + payload_hash + prev_hash + created_at).
5. Row is written into chain_blocks table.

Verification endpoint recomputes hashes and validates:

- payload_hash_match
- prev_hash_match
- block_hash_match
- overall is_valid

### 4.4 Frontend Coding

React + TypeScript frontend includes:

- Stock dashboard and detail pages.
- Indicator/chart rendering.
- Live strong-signal alert cards.
- Portfolio analytics cards.
- Blockchain proof status section showing implemented and planned items plus chain statistics.

This integration ensures that blockchain proof is not only backend logic but also user-visible functionality.

---

## 5. Results Snapshots and Discussion (Page 5)

### 5.1 Snapshot List to Insert

Add the following screenshots in this page (with short captions):

1. Dashboard with blockchain proof section visible.
2. Professional trade signal panel with timeframe set to 5m.
3. /chain/status API response screenshot.
4. /chain/records API response screenshot showing chained hashes.
5. /chain/verify/{prediction_id} response screenshot showing is_valid = true.
6. Alerts and portfolio analytics panels.

### 5.2 Discussion

Observed outcomes from implemented system:

- Timeframe consistency: Intraday prediction now follows selected candle interval and next-candle objective.
- Signal quality: Ensemble + LSTM outputs provide stable probabilistic direction with confidence context.
- Explainability: Reason text combines trend structure, RSI, MACD, volume behavior, and probability split.
- Trust evidence: Prediction records are chain-anchored and verifiable through cryptographic checks.
- Runtime stability: APIs deliver sanitized responses and recover gracefully under missing/noisy data.

Blockchain layer discussion:

- The chain mechanism enables tamper-evident continuity through prev_hash linking.
- Verification endpoint demonstrates reproducible integrity checks.
- Dashboard visibility converts cryptographic backend logic into transparent user-level trust evidence.

Overall, the obtained results validate both intelligence quality and trust infrastructure maturity.

---

## 6. Conclusion (Page 6)

This assignment successfully delivers a blockchain-enhanced high-frequency stock prediction platform with real software implementation across backend intelligence, frontend analytics, and cryptographic proof auditing.

The final system demonstrates:

1. Strong AI capability through ensemble + LSTM architecture.
2. High-frequency practical behavior with true timeframe-consistent next-candle predictions.
3. End-to-end operational features including alerts, portfolio analytics, and rich signal explanation.
4. Cryptographic trust layer with chained prediction proof and verification APIs.

The project therefore goes beyond conceptual research translation and establishes a practical, verifiable, deployable framework for trustworthy financial AI.

---

## 7. References (Page 7)

1. Govindasamy, P., Radhakrishnan, G. V., Shankar, U., High-Frequency Stock Market Price Prediction Using Blockchain and Deep Learning, IEEE Conference Proceedings, 2025.
2. Research articles on blockchain-based trust and integrity for financial data systems.
3. Research sources on LSTM and Adam optimization for sequential prediction.
4. Documentation and technical references for FastAPI, PyTorch, XGBoost, LightGBM, Scikit-learn, and React/TypeScript.

---

## 8. Literature Survey Proofs (Page 8)

Paste the following proof artifacts on this page:

1. Title page screenshot/PDF snippet of selected paper.
2. Abstract section screenshot from selected paper.
3. Methodology screenshot highlighting LSTM + Adam mention.
4. Performance table/figure screenshot from selected paper.
5. Reference page screenshot from selected paper.
6. Short comparison table prepared by you (paper vs implemented project):

| Survey Parameter | Paper Focus | Implemented in Our Project |
|---|---|---|
| Deep Learning Core | LSTM | LSTM + Ensemble Fusion |
| Optimizer | Adam | Adam + dynamic production pipeline |
| High Frequency | Return-rate analysis | Next-candle timeframe-consistent intraday prediction |
| Blockchain Role | Conceptual trust context | Live hash-chain anchoring + verification APIs |
| Deployment | Experimental | Full backend APIs + frontend dashboard + proof section |

Recommended proof captions:

- Figure LS1: Selected paper title and publication details.
- Figure LS2: Paper abstract and methodology evidence.
- Figure LS3: Reported metrics in paper.
- Figure LS4: Our implementation evidence (chain status, chain verify, dashboard proof section).

This page confirms survey authenticity and demonstrates academic alignment with implemented engineering outcomes.
