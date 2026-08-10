import warnings
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "production_models"

MODEL_PATHS = {
    "random_forest_risk_classifier.joblib",
    "robust_scaler_pipeline.joblib",
    "training_feature_columns.joblib",
}


@pytest.fixture(scope="session")
def pipeline_assets():
    asset_paths = {}
    for filename in MODEL_PATHS:
        asset_path = MODELS_DIR / filename
        assert asset_path.exists(), f"Missing production asset: {asset_path}"
        asset_paths[filename] = asset_path

    assets = {}
    for filename, asset_path in asset_paths.items():
        assets[filename] = joblib.load(asset_path)
    return assets


@pytest.fixture(scope="session")
def client():
    from app.main import app

    return TestClient(app)


def test_api_health_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ONLINE"}


def test_api_safe_checkout_cart(client):
    safe_cart = {
        "Sales": 1250.0,
        "Quantity": 5.0,
        "Discount": 0.0,
        "Processing_Time_Days": 4.0,
        "Category_Furniture": 0,
        "Category_Office_Supplies": 1,
    }
    response = client.post("/predict/risk-intercept", json=safe_cart)
    assert response.status_code == 200
    assert response.json()["action_directive"] == "ALLOW_CHECKOUT_FULFILLMENT"


def test_api_high_risk_checkout_interception(client):
    high_risk_cart = {
        "Sales": 1250.0,
        "Quantity": 5.0,
        "Discount": 0.70,
        "Processing_Time_Days": 4.0,
        "Category_Furniture": 0,
        "Category_Office_Supplies": 1,
    }
    response = client.post("/predict/risk-intercept", json=high_risk_cart)
    assert response.status_code == 200
    assert response.json()["action_directive"] == "INTERCEPT_BLOCK_TRANSACTION"
