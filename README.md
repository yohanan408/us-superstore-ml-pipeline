# US Superstore ML Pipeline

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://us-superstore-ml-pipeline-eqs3urcmbhwadrejhg6fzy.streamlit.app/)

A machine-learning project built on the US Superstore sales dataset. It covers exploratory analysis, negative-profit classification, a FastAPI inference service, automated tests, Docker, and a Streamlit application.

**Stack:** Python • scikit-learn • FastAPI • Streamlit • Plotly • Docker • pytest

> **Note on scope:** The dataset is historical. The "real-time" checkout scoring in this project is a simulation that replays historical transactions against the API; it is a demonstration of how a model could sit in a transaction-monitoring workflow, not a production system.

> **Related project:** The SQL side of this dataset (PostgreSQL ingestion, a dbt star schema, and a Power BI shipping analysis) lives in its own repository: [superstore-dbt-warehouse](TODO-add-link).

## Business Problem

Discounting can increase sales volume while also creating transactions that lose money.

This project uses transaction-level features to identify patterns associated with negative-profit outcomes, and builds a machine-learning workflow that can score a transaction at the point of sale. The goal is to support business judgment, not replace it.

**What the data shows:**
- 1,871 of the 9,994 order lines (18.7%) have negative profit, totalling about $156,131 in losses.
- Profitability collapses at deep discounts: every line at the 70% and 80% discount tiers loses money.
- In every shipping mode, 95–99% of lines discounted above 20% lose money, versus about 5–7% of the rest (see the "Shipping Mode vs. Loss Rate" section of the notebook).

## Inference Pipeline and UI

| Stage | Component | Purpose |
| ----- | --------- | ------- |
| 1 | `src/data_ingestion.py` | Pydantic validation of inbound checkout payloads. `Discount` is cast to `float` to prevent integer truncation. |
| 2 | `src/logger_config.py` | Centralized logger writing to the console and `logs/pipeline_runtime.log`, with a uniform `[Timestamp] [Level] [file:line]` format. |
| 3 | `src/feature_preprocessor.py` | Column alignment and padding to the training feature space, plus `RobustScaler` normalization of continuous fields. |
| 4 | `app/main.py` | FastAPI service with a health endpoint (`GET /`) and an inference endpoint (`POST /predict/risk-intercept`) backed by the Random Forest model. |
| 5 | `tests/test_prediction_pipeline.py` | pytest + `TestClient` suite covering preprocessing and HTTP routing end to end. |
| 6 | `app_ui.py` | Streamlit interface with KPI cards, Plotly analytics, transaction-level risk scoring, and segment-based financial rules. |

## Dual Local/Cloud API Routing

The Streamlit frontend has an "Engine target" selector that points either at the Dockerized backend on `http://localhost:8000` or at the Render deployment. The default is chosen automatically from the page URL: opened locally it targets the local container, opened from the deployed URL it targets the cloud backend.

| Environment | API endpoint |
| ----------- | ------------ |
| Local (Docker) | `http://localhost:8000/predict/risk-intercept` |
| Cloud (Render) | `https://us-superstore-ml-pipeline.onrender.com/predict/risk-intercept` |

> The live demo may take up to a minute to respond on first load if the hosting instances have gone to sleep.

## Model

**Task:** Binary classification of whether an order line has negative profit (about 19% of rows are loss-making).

**Setup:** Stratified 80/20 split (`random_state=42`), giving 7,995 training rows and 1,999 test rows (374 loss-making). Features are `Sales`, `Quantity`, `Discount`, processing days, ship mode, customer segment, region, category, sub-category, and a VIP-customer flag. All profit-derived columns (profit margin, ROI, buying price) are excluded to avoid target leakage. Models use `class_weight='balanced'` and a 0.5 decision threshold.

| Model | Macro F1 | ROC-AUC | Loss recall | Loss precision |
| ----- | -------- | ------- | ----------- | -------------- |
| Random Forest (deployed) | 0.88 | 0.983 | 0.89 | 0.75 |
| Extra Trees | 0.88 | 0.982 | 0.91 | 0.74 |
| Logistic Regression | 0.88 | 0.982 | 0.93 | 0.71 |
| Decision Tree | 0.87 | 0.969 | 0.92 | 0.70 |

The Random Forest is the deployed model because it balances recall and precision and is more stable than a single tree. All four models perform similarly, so the choice is mostly a precision/recall trade-off. Results come from a single hold-out split.

**Context for these numbers:**
- `Discount` accounts for about 67% of the Random Forest's feature importance. A model-free rule that flags any order with a discount above 20% reaches macro F1 0.90 (precision 0.96, recall 0.72) on the same test set. The models add better ranking (ROC-AUC 0.98 vs. 0.94 for discount alone) and the option of much higher recall (0.89–0.93 vs. 0.72) at lower precision.
- `Processing_Time_Days` is only known after an order ships, so it would not be available at checkout time. A production version should drop it and retrain.
- The `RobustScaler` was fit on the full dataset before the train/test split. This has little effect on tree-based models, but the scaler should be fit on training data only in a stricter setup.
- Random Forest results can differ slightly across scikit-learn versions, so pin the version used for training.

**Notes on the model files:** The `.joblib` files in `production_models/` were created with a specific scikit-learn version and should be loaded with the version pinned in `requirements.txt`. Joblib files are pickles, so only load files from sources you trust. The models are trained in `notebooks/E-Commerce Platform Analysis.ipynb`.

## Developer Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the FastAPI backend (terminal 1)

```bash
python3 -m uvicorn app.main:app --reload
```

- Health check: `GET http://127.0.0.1:8000/` returns `{"status": "ONLINE"}`.
- Inference: `POST http://127.0.0.1:8000/predict/risk-intercept` with a JSON `CheckoutCartRequest` body.

Alternatively, run the containerized backend:

```bash
docker compose up --build
```

### 3. Launch the Streamlit frontend (terminal 2)

```bash
streamlit run app_ui.py
```

Opening `http://localhost:8501` selects the **Local** engine target automatically.

### 4. Run the tests

```bash
pytest tests/ -v
```

## Repository Layout

```
us-superstore-ml-pipeline/
├── app/
│   └── main.py
├── dashboard/
├── data/
│   └── US Superstore data.xls
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
├── app_ui.py
├── realtime_demo.py
└── requirements.txt
```

`logs/` is created at runtime by the logger and is not tracked in the repository.

## Data

The project uses the US Superstore sales dataset (`data/US Superstore data.xls`, 9,994 rows). [[TODO: add the source and any license or attribution requirements.](https://www.kaggle.com/datasets/juhi1994/superstore)]

## License

MIT. See [LICENSE](LICENSE).
