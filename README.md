# US Superstore ML Pipeline

An executive-grade, end-to-end machine learning pipeline that monitors checkout transactions in real time and intercepts financial loss anomalies before they hit the ledger. Built modularly and production-verified against the US Superstore commerce dataset.

## The Business Problem

Unmonitored checkout discounts create **non-linear margin cliffs**. A markdown that looks reasonable on a single line item compounds across volume, quantity, and fulfillment cost, silently converting profitable carts into net-loss transactions. This pipeline turns that blind spot into a real-time, automated guardrail: every checkout is scored, every loss-anomaly is blocked at the edge, and every safe transaction is allowed to fulfill.

## 5-Stage Engineering Pipeline

| Stage | Component | Purpose |
|-------|-----------|---------|
| 1 | `src/data_ingestion.py` | Pydantic validation of inbound checkout payloads; `Discount` is force-cast to `float` to prevent integer truncation. |
| 2 | `src/logger_config.py` | Centralized dual-routing logger (console + `logs/pipeline_runtime.log`) with a uniform `[Timestamp] [Level] [file:line]` format. |
| 3 | `src/feature_preprocessor.py` | Matrix padding, key re-alignment, and RobustScaler normalization of continuous fields for the production feature space. |
| 4 | `app/main.py` | FastAPI gateway — `/` health probe and `/predict/risk-intercept` inference endpoint backed by the tuned Random Forest. |
| 5 | `tests/test_prediction_pipeline.py` | CI-grade pytest + TestClient suite verifying preprocessing and HTTP routing end-to-end. |

## Tournament Metrics

The candidate models were evaluated head-to-head in a model tournament on macro F1-score. **The deadlock was broken by the Random Forest classifier**:

- **Macro F1-Score: 0.88** (converged tournament score)
- **ROC-AUC: 0.984** (Random Forest tie-breaker)
- Production artifacts serialized under `production_models/` via `joblib`.

## Developer Quickstart

### Spin up the FastAPI server

```bash
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/` returns `{"status": "ONLINE"}`.

Inference: `POST http://127.0.0.1:8000/predict/risk-intercept` with a JSON `CheckoutCartRequest` body.

### Run the test suite

```bash
pytest tests/ -v
```

## Repository Layout

```
us-superstore-ml-pipeline/
├── app/
│   └── main.py
├── data/
│   └── US Superstore data.xls
├── logs/
│   └── pipeline_runtime.log
├── notebooks/
│   └── E-Commerce Platform Analysis.ipynb
├── production_models/
│   ├── random_forest_risk_classifier.joblib
│   ├── robust_scaler_pipeline.joblib
│   └── training_feature_columns.joblib
├── src/
│   ├── __init__.py
│   ├── data_ingestion.py
│   ├── feature_preprocessor.py
│   └── logger_config.py
├── tests/
│   └── test_prediction_pipeline.py
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── README.md
└── requirements.txt
```

## License

MIT — see [LICENSE](LICENSE).
