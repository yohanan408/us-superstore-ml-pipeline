import sys
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException

from src.data_ingestion import CheckoutCartRequest
from src.feature_preprocessor import transform_and_align_features
from src.logger_config import logger

MODELS_DIR = Path(__file__).resolve().parent.parent / "production_models"
MODEL_PATH = MODELS_DIR / "random_forest_risk_classifier.joblib"
SCALER_PATH = MODELS_DIR / "robust_scaler_pipeline.joblib"
FEATURE_COLUMNS_PATH = MODELS_DIR / "training_feature_columns.joblib"

try:
    risk_model = joblib.load(MODEL_PATH)
    robust_scaler = joblib.load(SCALER_PATH)
    feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
    logger.info("ML assets loaded successfully")
except Exception as exc:
    logger.critical("Failed to load ML assets: %s", exc, exc_info=True)
    raise SystemExit(1) from exc

app = FastAPI(title="US Superstore ML Pipeline", version="0.3.0")


@app.get("/")
def root_health_check():
    return {"status": "ONLINE"}


@app.post("/predict/risk-intercept")
def predict_risk_intercept(payload: CheckoutCartRequest):
    try:
        transaction = payload.model_dump()
        logger.info("Incoming transaction received: %s", transaction)

        if payload.Discount > 0.50:
            logger.warning("Extreme markdown detected: Discount=%.2f", payload.Discount)

        aligned_row = transform_and_align_features(transaction, feature_columns, robust_scaler)

        prediction = int(risk_model.predict(aligned_row)[0])
        risk_probability = float(risk_model.predict_proba(aligned_row)[0][1])
        risk_percentage = round(risk_probability * 100, 2)

        if prediction == 1:
            logger.error(
                "Financial Loss Anomaly intercepted: prediction=%d risk=%.2f%%",
                prediction,
                risk_percentage,
            )
            return {
                "action_directive": "INTERCEPT_BLOCK_TRANSACTION",
                "prediction_class": prediction,
                "risk_percentage": risk_percentage,
            }

        logger.info("Safe profit transaction passed: prediction=%d risk=%.2f%%", prediction, risk_percentage)
        return {
            "action_directive": "ALLOW_CHECKOUT_FULFILLMENT",
            "prediction_class": prediction,
            "risk_percentage": risk_percentage,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.critical("Operational failure in inference route: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal inference failure")
