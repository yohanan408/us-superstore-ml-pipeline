# US Superstore ML Pipeline

👉 **[View Live Interactive Streamlit App](PASTE_YOUR_STREAMLIT_URL_HERE)**

A production-grade, full-stack data product that monitors e-commerce checkout transactions in real time and intercepts financial loss anomalies before they hit the ledger. The backend Random Forest inference engine is containerized and cloud-hosted, and the executive Streamlit dashboard — seeded from the US Superstore commerce dataset — routes every live transaction through the model and applies segment-aware financial guardrails on top.

## The Business Problem

Unmonitored checkout discounts create **non-linear margin cliffs**. A markdown that looks reasonable on a single line item compounds across volume, quantity, and fulfillment cost, silently converting profitable carts into net-loss transactions. This pipeline turns that blind spot into a real-time, automated guardrail: every checkout is scored, every loss-anomaly is blocked at the edge, and every safe transaction is allowed to fulfill.

The interactive frontend layers a second, **accounting-driven financial fail-safe** beneath the machine learning classification — guaranteeing that no negative-margin transaction ever reaches the ledger, even on out-of-distribution inputs the model has never seen.

## 6-Stage Engineering Pipeline & Interactive UI

| Stage | Component | Purpose |
|-------|-----------|---------|
| 1 | `src/data_ingestion.py` | Pydantic validation of inbound checkout payloads; `Discount` is force-cast to `float` to prevent integer truncation. |
| 2 | `src/logger_config.py` | Centralized dual-routing logger (console + `logs/pipeline_runtime.log`) with a uniform `[Timestamp] [Level] [file:line]` format. |
| 3 | `src/feature_preprocessor.py` | Matrix padding, key re-alignment, and RobustScaler normalization of continuous fields for the production feature space. |
| 4 | `app/main.py` | FastAPI gateway — `/` health probe and `/predict/risk-intercept` inference endpoint backed by the tuned Random Forest. |
| 5 | `tests/test_prediction_pipeline.py` | CI-grade pytest + TestClient suite verifying preprocessing and HTTP routing end-to-end. |
| 6 | `app_ui.py` | Streamlit executive command center — live KPI cards, Plotly analytics, real-time risk scoring, and segment-aware financial guardrails. |

### Dual Local/Cloud API Routing

The frontend is **environment-agnostic**: a sidebar "Engine target" selector targets either the Dockerized backend at `http://localhost:8000` or the live Render deployment, and the default is chosen automatically from the Streamlit page URL. Open the app on your laptop — it routes to your local container with zero configuration; open the deployed URL — it instantly targets the cloud backend.

| Environment | API endpoint |
|-------------|--------------|
| Local (Docker) | `http://localhost:8000/predict/risk-intercept` |
| Cloud (Render) | `https://us-superstore-ml-pipeline.onrender.com/predict/risk-intercept` |

### Segment-Aware Business Logic Guardrails

On top of the model's 50% classification line, the dashboard enforces an accounting-derived fail-safe that adapts to business strategy per customer segment:

- **Consumer checkouts — strict enforcement:** any transaction whose locally computed profit is negative (`calculated_profit < 0`) is forcibly overridden to `INTERCEPT_BLOCK`, no matter what the model says.
- **Corporate / Home Office — managed 15% promotional buffer:** smaller row-level losses are absorbed to preserve premier B2B relationships, and checkout is only intercepted once the computed net profit margin breaches `-15.0%`.

Every intercepted net-loss order is accumulated into the **Revenue Leakage Shielded** KPI, proving the machine learning security firewall in real time.

## Tournament Metrics

The candidate models were evaluated head-to-head in a model tournament on macro F1-score. **The deadlock was broken by the Random Forest classifier**:

- **Macro F1-Score: 0.88** (converged tournament score)
- **ROC-AUC: 0.984** (Random Forest tie-breaker)
- Production artifacts serialized under `production_models/` via `joblib`.

## Developer Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Spin up the FastAPI backend (terminal 1)

```bash
python3 -m uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/` returns `{"status": "ONLINE"}`.

Inference: `POST http://127.0.0.1:8000/predict/risk-intercept` with a JSON `CheckoutCartRequest` body.

> Alternatively, run the containerized backend: `docker-compose up --build` (health probe included).

### 3. Launch the Streamlit frontend (terminal 2)

```bash
streamlit run app_ui.py
```

Opening `http://localhost:8501` auto-selects the **Local** engine target and streams live transactions to your backend. When run from a deployed Streamlit Cloud URL, the same code auto-selects **Cloud (Render)** — no code changes or manual switching required.

### 4. Run the test suite

```bash
pytest tests/ -v
```

## Repository Layout

```
us-superstore-ml-pipeline/
├── app/
│   └── main.py
├── app_ui.py
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