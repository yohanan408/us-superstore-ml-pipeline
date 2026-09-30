# US Superstore ML Pipeline

**(https://us-superstore-ml-pipeline-eqs3urcmbhwadrejhg6fzy.streamlit.app/)**

# US Superstore ML Pipeline

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://us-superstore-ml-pipeline-eqs3urcmbhwadrejhg6fzy.streamlit.app/)

An end-to-end e-commerce analytics and machine-learning project built around the US Superstore dataset.

The project combines exploratory analysis, financial-risk classification, API inference, automated testing, Docker, and an interactive Streamlit application to examine how discounting and transaction characteristics relate to negative-profit outcomes.

**Key components:** Python • scikit-learn • FastAPI • Streamlit • Docker • pytest • PostgreSQL
## Business Problem

Discounting can increase sales volume while also creating transactions with negative profit.

This project investigates that trade-off by using transaction-level features to identify patterns associated with negative-profit outcomes and by building a machine-learning workflow that can score new checkout transactions.

The objective is not to replace business judgment, but to demonstrate how analytical models can be integrated into a transaction-monitoring workflow.

## 6-Stage Engineering Pipeline & Interactive UI

| Stage | Component | Purpose |
|-------|-----------|---------|
| 1 | `src/data_ingestion.py` | Pydantic validation of inbound checkout payloads; `Discount` is force-cast to `float` to prevent integer truncation. |
| 2 | `src/logger_config.py` | Centralized dual-routing logger (console + `logs/pipeline_runtime.log`) with a uniform `[Timestamp] [Level] [file:line]` format. |
| 3 | `src/feature_preprocessor.py` | Matrix padding, key re-alignment, and RobustScaler normalization of continuous fields for the production feature space. |
| 4 | `app/main.py` | FastAPI gateway: `/` FastAPI gateway with a health endpoint and /predict/risk-intercept inference endpoint backed by the Random Forest model. |
| 5 | `tests/test_prediction_pipeline.py` | CI-grade pytest + TestClient suite verifying preprocessing and HTTP routing end-to-end. |
| 6 | `app_ui.py` | Streamlit interface with KPI cards, Plotly analytics, transaction-level risk scoring, and segment-based financial rules.|

---

## Stage 7: Demand-Aware Supply Chain Analytics Warehouse (dbt + Postgres)

To complement real-time inline predictions, the repository features an offline enterprise **Data Engineering & Governance Pipeline** located in the `demand_aware_pipeline/` subdirectory. This architecture processes historical transactional ledgers to capture logistical latencies and revenue leak trends over multi-month windows.

```text
                       [RAW SCHEMA]                                   [STAGING SCHEMA]
              superstore_transactions (9,994 rows)           dim_products (1,894 Cryptographic SKUs)
                               │                                             ▲
                               ▼                                             │ Many-to-One (*:1)
                        [dbt core] ──────────────────────────────────────────┴ Star Schema Link
                               │
                               ▼
                        fact_orders (9,994 rows w/ calculated Lead Times & Margin Leaks)
```

###  Analytics Infrastructure Specifications

- **Data Inspection Layer:** Programmatic Python (`SQLAlchemy`) ingestion engine executing strict character-stripping, type-normalizations, and regional date conversions directly into local **PostgreSQL partitions via Port 5432**.
- **Transformation Layer (dbt Core):** Decoupled, modular SQL models restructuring raw operational inputs into an optimized, single-direction **Many-to-One (1:1) Star Schema** layout.
- **Governance Layer:** Automated data integrity validations (`dbt test`) enforcing uniqueness constraints on your primary relational fields to block pipeline drift.
- **BI Visualization Layer:** Star schema relational coordinates exposed to **Power BI Desktop** to plot operational SLA violations alongside structural margin leakage rations.

###  Core Analytics Engineering Discoveries

- **Cryptographic Surrogate Keys:** Intercepted **32 recycled product ID schema duplication anomalies** in the raw source file. Cleanly resolved the M2M filtering collision by hashing composite columns into an MD5 cryptographic surrogate string.
- **Logistical Bottlenecks Captured:** Isolated a massive Q4 supply chain breakdown peaking aggressively in September with over **160 SLA shipping violations** within Office Supplies inventory clusters.
- **The First-Class Paradox:** Charted a visual dual-axis correlation proving that while *First-Class* express shipping drastically minimizes fulfillment latency, its premium courier overhead spikes the *Margin Leakage Rate* close to **19%**, making *Second-Class* transit your ultimate retail financial sweet spot.

---

### Dual Local/Cloud API Routing

The frontend is **environment-agnostic**: a sidebar "Engine target" selector targets either the Dockerized backend at `http://localhost:8000` or the live Render deployment, and the default is chosen automatically from the Streamlit page URL. Open the app on your laptop, it routes to your local container with zero configuration; open the deployed URL, it instantly targets the cloud backend.

| Environment | API endpoint |
|-------------|--------------|
| Local (Docker) | `http://localhost:8000/predict/risk-intercept` |
| Cloud (Render) | `https://us-superstore-ml-pipeline.onrender.com/predict/risk-intercept` |

### Segment-Aware Business Logic Guardrails

On top of the model's 50% classification line, the dashboard enforces an accounting-derived fail-safe that adapts to business strategy per customer segment:

- **Consumer checkouts — strict enforcement:** any transaction whose locally computed profit is negative (`calculated_profit < 0`) is forcibly overridden to `INTERCEPT_BLOCK`, no matter what the machine learning model says.
- **Corporate / Home Office — managed 15% promotional buffer:** smaller row-level losses are absorbed to preserve premier B2B relationships, and checkout is only intercepted once the computed net profit margin breaches `-15.0%`.

Every intercepted net-loss order is accumulated into the **Revenue Leakage Shielded** KPI, proving the machine learning security firewall in real time.

## Model Evaluation

Candidate classification models were evaluated using macro F1-score, with ROC-AUC used as an additional evaluation metric.

| Metric | Result |
|---|---:|
| Macro F1 | 0.88 |
| ROC-AUC | 0.984 |

The Random Forest classifier was selected for the deployed inference workflow.

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

Opening `http://localhost:8501` auto-selects the **Local** engine target and streams live transactions to your backend. When run from a deployed Streamlit Cloud URL, the same code auto-selects **Cloud (Render)**. No code changes or manual switching required.

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
