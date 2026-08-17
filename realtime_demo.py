import time

import requests

MODEL_URL = "http://localhost:8000/predict/risk-intercept"
STREAM_DELAY_SECONDS = 1.5

MOCK_TRANSACTIONS = [
    {
        "label": "Standard Profitable Checkout (5% discount)",
        "Sales": 1250.00,
        "Quantity": 5.0,
        "Discount": 0.05,
        "Processing_Time_Days": 4.0,
        "Category_Furniture": 0,
        "Category_Office_Supplies": 1,
    },
    {
        "label": "Margin-Healthy Deal at 20% Discount Cliff",
        "Sales": 940.00,
        "Quantity": 8.0,
        "Discount": 0.20,
        "Processing_Time_Days": 3.0,
        "Category_Furniture": 1,
        "Category_Office_Supplies": 0,
    },
    {
        "label": "TOXIC Predatory Checkout (75% discount)",
        "Sales": 210.00,
        "Quantity": 25.0,
        "Discount": 0.75,
        "Processing_Time_Days": 1.0,
        "Category_Furniture": 0,
        "Category_Office_Supplies": 1,
    },
]


def print_order_metrics(label, metrics):
    print(f"  Order: {label}")
    print(
        f"  Metrics: Sales=${metrics['Sales']:,.2f} | "
        f"Qty={metrics['Quantity']:.0f} | "
        f"Discount={metrics['Discount']*100:.0f}%"
    )


def stream_transactions():
    print("=" * 62)
    print("  LIVE CHECKOUT RISK-INCEPTION STREAM  ")
    print("=" * 62)

    for idx, transaction in enumerate(MOCK_TRANSACTIONS, start=1):
        print(f"\n--- Incoming Order #{idx} ---")
        print_order_metrics(transaction.pop("label"), transaction)

        try:
            response = requests.post(MODEL_URL, json=transaction, timeout=10)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as exc:
            print(f"  !! Model endpoint unreachable: {exc}")
            print("  !! Is the FastAPI container running on localhost:8000?")
        else:
            prediction = result["prediction_class"]
            directive = result["action_directive"]
            risk = result["risk_percentage"]

            prediction_label = "Loss" if prediction == 1 else "Profit"
            print(
                f"  Model Prediction: Class {prediction} ({prediction_label}) | "
                f"Risk={risk:.2f}%"
            )

            if "INTERCEPT_BLOCK" in directive:
                print(f"  🛡️  Action Directive: {directive}")
            else:
                print(f"  🛡️  Action Directive: {directive}")

        time.sleep(STREAM_DELAY_SECONDS)

    print("\n" + "=" * 62)
    print("  STREAM COMPLETE — DEMO FINISHED  ")
    print("=" * 62)


if __name__ == "__main__":
    stream_transactions()
