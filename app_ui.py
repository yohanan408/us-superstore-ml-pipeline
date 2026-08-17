"""US Superstore Risk Interception Command Center.

Production Streamlit frontend that connects to the containerized FastAPI
ML gateway at http://localhost:8000/predict/risk-intercept and renders a
Power-BI-style executive dashboard seeded from the local historical dataset.

Run:
    streamlit run app_ui.py
"""

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# --------------------------------------------------------------------------- #
# Static configuration
# --------------------------------------------------------------------------- #
LOCAL_API_BASE = "http://localhost:8000"
CLOUD_API_BASE = "https://us-superstore-ml-pipeline.onrender.com"
API_ENDPOINT_PATH = "/predict/risk-intercept"

API_URL = f"{LOCAL_API_BASE}{API_ENDPOINT_PATH}"
PROCESSING_TIME_DAYS = 4.0

DATA_FILENAMES = ["US Superstore data.xls", "US Superstore data.xlsx"]
PROJECT_ROOT = Path(__file__).resolve().parent

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

LIVE_ORDER_YEAR = 2017
LIVE_MONTH_NAME = "Dec"
LIVE_MONTH_INDEX = 12

CATEGORY_FLAGS = {
    "Furniture": {"Category_Office_Supplies": 0, "Category_Technology": 0},
    "Office Supplies": {"Category_Office_Supplies": 1, "Category_Technology": 0},
    "Technology": {"Category_Office_Supplies": 0, "Category_Technology": 1},
}

SEGMENT_FLAGS = {
    "Consumer": {"Segment_Corporate": 0, "Segment_Home_Office": 0},
    "Corporate": {"Segment_Corporate": 1, "Segment_Home_Office": 0},
    "Home Office": {"Segment_Corporate": 0, "Segment_Home_Office": 1},
}

REGION_FLAGS = {
    "Central": {"Region_East": 0, "Region_South": 0, "Region_West": 0},
    "East": {"Region_East": 1, "Region_South": 0, "Region_West": 0},
    "South": {"Region_East": 0, "Region_South": 1, "Region_West": 0},
    "West": {"Region_East": 0, "Region_South": 0, "Region_West": 1},
}

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="US Superstore Risk Interception Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------- #
# Sidebar: deploy environment selection
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("## 🌐 Environment")
    page_url = st.context.url or ""
    is_local = page_url.startswith("http://localhost") or page_url.startswith(
        "http://127.0.0.1"
    )
    default_index = 0 if is_local else 1
    env_option = st.selectbox(
        "Engine target",
        ("Local (localhost:8000)", "Cloud (Render)"),
        index=default_index,
    )
    api_base = (
        LOCAL_API_BASE
        if env_option.startswith("Local")
        else CLOUD_API_BASE
    )
    API_URL = f"{api_base}{API_ENDPOINT_PATH}"
    st.caption(f"Targeting\n\n`{API_URL}`")

# --------------------------------------------------------------------------- #
# Session state initialization
# --------------------------------------------------------------------------- #
if "ledger" not in st.session_state:
    st.session_state.ledger = None
if "live_order_counter" not in st.session_state:
    st.session_state.live_order_counter = 0
if "session_leakage_shielded" not in st.session_state:
    st.session_state.session_leakage_shielded = 0.0
if "boot_leakage" not in st.session_state:
    st.session_state.boot_leakage = None
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None


# --------------------------------------------------------------------------- #
# Data seeding baseline
# --------------------------------------------------------------------------- #
def locate_data_file() -> Path | None:
    candidates = [PROJECT_ROOT / name for name in DATA_FILENAMES]
    candidates += [PROJECT_ROOT / "data" / name for name in DATA_FILENAMES]
    for path in candidates:
        if path.exists():
            return path
    return None


@st.cache_data(show_spinner=False)
def load_historical_ledger(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Order_Year"] = df["Order Date"].dt.year
    df["Order_Month_Name"] = df["Order Date"].dt.strftime("%b")
    df["Month_Index"] = df["Order Date"].dt.month
    return df


def initialize_ledger() -> None:
    if st.session_state.ledger is not None:
        return
    data_path = locate_data_file()
    if data_path is None:
        st.warning(
            "Historical dataset not found. Place `US Superstore data.xls` / "
            "`.xlsx` in the project root or `data/` folder."
        )
        return
    with st.spinner("Seeding historical ledger baseline..."):
        st.session_state.ledger = load_historical_ledger(data_path)
    if st.session_state.boot_leakage is None:
        st.session_state.boot_leakage = float(
            st.session_state.ledger.loc[
                st.session_state.ledger["Profit"] < 0, "Profit"
            ]
            .abs()
            .sum()
        )


initialize_ledger()

# --------------------------------------------------------------------------- #
# Helpers: category-specific accounting
# --------------------------------------------------------------------------- #
def compute_average_unit_cost(category: str, ledger: pd.DataFrame) -> float:
    df_cat = ledger.loc[ledger["Category"] == category]
    if df_cat.empty:
        return 0.0
    unit_costs = (df_cat["Sales"] - df_cat["Profit"]) / df_cat["Quantity"]
    return float(unit_costs.mean())


def calculate_transaction_metrics(
    sales_input: float,
    quantity_input: int,
    discount: float,
    category: str,
    ledger: pd.DataFrame,
) -> dict:
    discount_amount = sales_input * discount
    net_selling_price = sales_input - discount_amount
    avg_unit_cost = compute_average_unit_cost(category, ledger)
    total_cost_price = quantity_input * avg_unit_cost
    calculated_profit = net_selling_price - total_cost_price
    profit_margin = (
        (calculated_profit / net_selling_price) * 100.0
        if net_selling_price > 0
        else 0.0
    )
    return {
        "discount_amount": discount_amount,
        "net_selling_price": net_selling_price,
        "avg_unit_cost": avg_unit_cost,
        "total_cost_price": total_cost_price,
        "calculated_profit": calculated_profit,
        "profit_margin": profit_margin,
    }


# --------------------------------------------------------------------------- #
# Helpers: backend call
# --------------------------------------------------------------------------- #
def build_risk_payload(transaction: dict) -> dict:
    category = transaction["Category"]
    region = transaction["Region"]
    segment = transaction["Segment"]
    return {
        "Sales": transaction["Sales"],
        "Quantity": transaction["Quantity"],
        "Category": category,
        "Discount": transaction["Discount"],
        "Region": region,
        "Segment": segment,
        "Processing_Time_Days": PROCESSING_TIME_DAYS,
        "Category_Furniture": 0,
        **CATEGORY_FLAGS[category],
        **SEGMENT_FLAGS[segment],
        **REGION_FLAGS[region],
    }


def call_risk_intercept_engine(payload: dict) -> dict:
    global API_URL
    response = requests.post(API_URL, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


# --------------------------------------------------------------------------- #
# Top tier: global high-level filters
# --------------------------------------------------------------------------- #
ledger = st.session_state.ledger

if ledger is None:
    st.stop()

st.markdown("## 🛡️ US Superstore Risk Interception Command Center")
st.caption(
    "Live checkout guardrail powered by the containerized FastAPI Random Forest "
    f"engine at `{API_URL}` · background `Processing_Time_Days` baseline = "
    f"{PROCESSING_TIME_DAYS:g}"
)

filter_left, filter_right, _ = st.columns([2, 2, 8])
region_options = ["All"] + sorted(ledger["Region"].dropna().unique().tolist())
segment_options = ["All"] + sorted(ledger["Segment"].dropna().unique().tolist())

with filter_left:
    region_filter = st.selectbox("🌍 Global Region Filter", region_options)
with filter_right:
    segment_filter = st.selectbox("🧑‍💼 Global Segment Filter", segment_options)

ledger_filtered = ledger.copy()
if region_filter != "All":
    ledger_filtered = ledger_filtered.loc[ledger_filtered["Region"] == region_filter]
if segment_filter != "All":
    ledger_filtered = ledger_filtered.loc[ledger_filtered["Segment"] == segment_filter]

# --------------------------------------------------------------------------- #
# Top tier: 4 live cumulative KPI cards (always global / unfiltered)
# --------------------------------------------------------------------------- #
total_transactions = int(ledger["Order ID"].nunique())
total_sales = float(ledger["Sales"].sum())
total_profit = float(ledger["Profit"].sum())
leakage_shielded = float(st.session_state.boot_leakage) + float(
        st.session_state.session_leakage_shielded
    )

kpi_cols = st.columns(4)
kpi_cols[0].metric(
    "Total Transactions",
    f"{total_transactions:,}"
)
kpi_cols[1].metric(
    "Total Sales",
    f"${total_sales:,.0f}",
)
kpi_cols[2].metric(
    "Total Profit",
    f"${total_profit:,.0f}",
)
kpi_cols[3].metric(
    "Revenue Leakage Shielded",
    f"${leakage_shielded:,.0f}",
    delta=(
        f"${st.session_state.session_leakage_shielded:,.0f} preserved live"
        if st.session_state.session_leakage_shielded > 0
        else "No live losses intercepted this session"
    ),
    delta_color="off",
)

st.divider()

# --------------------------------------------------------------------------- #
# Execution feedback from last live transaction
# --------------------------------------------------------------------------- #
if st.session_state.last_feedback is not None:
    feedback_kind, feedback_body = st.session_state.last_feedback
    if feedback_kind == "success":
        st.success(feedback_body)
    else:
        st.error(feedback_body)

# --------------------------------------------------------------------------- #
# Middle tier: live transaction form + category pie chart
# --------------------------------------------------------------------------- #
middle_left, middle_right = st.columns([1, 1], gap="large")

with middle_left:
    st.markdown("### 🧾 Live Risk Assessment")
    form_submitted = None
    with st.form("live_transaction_form"):
        sales_input = st.number_input(
            "Sales (gross invoice value, $)",
            min_value=0.0,
            value=1250.0,
            step=50.0,
            format="%.2f",
        )
        quantity_input = st.number_input(
            "Quantity (line item volume)",
            min_value=1,
            value=5,
            step=1,
            format="%d",
        )
        category_input = st.selectbox(
            "Category", sorted(ledger["Category"].dropna().unique().tolist())
        )
        region_input = st.selectbox(
            "Region", sorted(ledger["Region"].dropna().unique().tolist())
        )
        segment_input = st.selectbox(
            "Segment", sorted(ledger["Segment"].dropna().unique().tolist())
        )
        discount_input = st.slider(
            "Discount rate",
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.01,
            format="%.2f",
        )
        form_submitted = st.form_submit_button("Run Risk Assessment", type="primary")

with middle_right:
    st.markdown("### 🥧 Proportion by Category")
    if ledger_filtered.empty:
        st.info("No data for the active filter combination.")
    else:
        pie_fig = px.pie(
            ledger_filtered,
            names="Category",
            values="Sales",
            title="Proportion by Category",
            hole=0.35,
        )
        pie_fig.update_traces(textposition="inside", textinfo="percent+label")
        pie_fig.update_layout(
            height=430,
            margin=dict(l=10, r=10, t=45, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        )
        st.plotly_chart(pie_fig, width="stretch")

# --------------------------------------------------------------------------- #
# Live transaction execution block
# --------------------------------------------------------------------------- #
if form_submitted:
    metrics = calculate_transaction_metrics(
        sales_input, quantity_input, discount_input, category_input, ledger
    )

    transaction = {
        "Sales": sales_input,
        "Quantity": quantity_input,
        "Category": category_input,
        "Discount": discount_input,
        "Region": region_input,
        "Segment": segment_input,
    }

    try:
        with st.spinner("Scoring checkout against the ML risk engine..."):
            result = call_risk_intercept_engine(build_risk_payload(transaction))
    except requests.exceptions.RequestException as exc:
        st.error(
            "❌ ML engine unreachable. Is the FastAPI container running on "
            f"`localhost:8000`?\n\n`{exc}`"
        )
    except Exception as exc:
        st.error(f"❌ Unexpected failure during risk assessment.\n\n`{exc}`")
    else:
        model_directive = result.get("action_directive", "")
        prediction = result.get("prediction_class", result.get("prediction", None))
        risk_percentage = result.get("risk_percentage", None)

        profit = metrics["calculated_profit"]
        margin = metrics["profit_margin"]

        # Tier 1: native ML model interception (Risk > 50%) is credited to the model.
        # Tier 2: fail-safe override fires ONLY on a model false-negative (ALLOW),
        # when the segment-aware local accounting rule still flags the order.
        model_blocked = "INTERCEPT_BLOCK" in model_directive
        action_directive = model_directive

        override_engaged = False
        if not model_blocked:
            if segment_input == "Consumer" and profit < 0:
                action_directive = "INTERCEPT_BLOCK"
                override_engaged = True
            elif segment_input in ("Corporate", "Home Office") and margin < -15.0:
                action_directive = "INTERCEPT_BLOCK"
                override_engaged = True
        metrics_summary = (
            f"Discount Applied: **${metrics['discount_amount']:,.2f}** · "
            f"Net Selling Price: **${metrics['net_selling_price']:,.2f}** · "
            f"Avg Unit Cost ({category_input}): **${metrics['avg_unit_cost']:,.2f}** · "
            f"Total Cost: **${metrics['total_cost_price']:,.2f}** · "
            f"Calculated Profit: **${profit:,.2f}** · "
            f"Margin: **{metrics['profit_margin']:.2f}%**"
        )

        is_allowed = "ALLOW" in action_directive
        if is_allowed:
            st.session_state.live_order_counter += 1
            order_id = (
                f"LIVE-{dt.date.today():%Y%m%d}-{st.session_state.live_order_counter:04d}"
            )
            new_row = {column: "" for column in ledger.columns}
            new_row.update(
                {
                    "Order ID": order_id,
                    "Order Date": pd.Timestamp(LIVE_ORDER_YEAR, LIVE_MONTH_INDEX, 31),
                    "Ship Date": pd.Timestamp(LIVE_ORDER_YEAR, LIVE_MONTH_INDEX, 31),
                    "Customer ID": "LIVE-CUSTOMER",
                    "Customer Name": "Live Transaction",
                    "Segment": segment_input,
                    "Country": "United States",
                    "City": "Live",
                    "State": "Live",
                    "Postal Code": 0,
                    "Region": region_input,
                    "Category": category_input,
                    "Product Name": "Live Checkout Order",
                    "Sales": metrics["net_selling_price"],
                    "Quantity": quantity_input,
                    "Discount": discount_input,
                    "Profit": profit,
                    "Order_Year": LIVE_ORDER_YEAR,
                    "Order_Month_Name": LIVE_MONTH_NAME,
                    "Month_Index": LIVE_MONTH_INDEX,
                }
            )
            st.session_state.ledger = pd.concat(
                [ledger, pd.DataFrame([new_row])], ignore_index=True
            )

            risk_note = (
                f" · Risk: **{risk_percentage:.2f}%**" if risk_percentage is not None else ""
            )
            st.session_state.last_feedback = (
                "success",
                f"✅ **ALLOWED — checkout fulfilled** (Directive: `{action_directive}`"
                f"{risk_note})\n\n{metrics_summary}",
            )
        else:
            if profit < 0:
                st.session_state.session_leakage_shielded += abs(profit)
            risk_note = (
                f" · Risk:**{risk_percentage:.2f}%** " if risk_percentage is not None else ""
            )
            if override_engaged:
                block_heading = "🚫 **INTERCEPTED & BLOCKED**"
                block_reason = (
                    f"⚠️ **Financial fail-safe engaged — negative profit overrode the "
                    f"false-negative model directive** "
                    f"(`{segment_input}` segment: calculated profit "
                    f"${profit:,.2f}, margin {margin:.2f}%)."
                )
            else:
                block_heading = "🤖 **ML MODEL INTERCEPTED**"
                block_reason = (
                    f"The Random Forest engine identified the margin risk threshold "
                    f"from its risk score{risk_note}— no fail-safe override required."
                )
            st.session_state.last_feedback = (
                "error",
                f"{block_heading} (Directive: `{action_directive}`"
                f"{risk_note})\n\n{block_reason}\n\n{metrics_summary}",
            )
        st.rerun()

# --------------------------------------------------------------------------- #
# Bottom tier: annual sales bar + monthly margin line
# --------------------------------------------------------------------------- #
bottom_left, bottom_right = st.columns(2, gap="large")

with bottom_left:
    st.markdown("### 📊 Total Sales Year by Year")
    if ledger_filtered.empty:
        st.info("No data for the active filter combination.")
    else:
        monthly_sales = (
            ledger_filtered.groupby(
                ["Order_Month_Name", "Month_Index", "Order_Year"],
                as_index=False,
            )["Sales"]
            .sum()
            .sort_values(["Month_Index", "Order_Year"])
        )
        bar_fig = px.bar(
            monthly_sales,
            x="Order_Month_Name",
            y="Sales",
            color="Order_Year",
            barmode="group",
            title="Total Sales Year by Year",
            labels={"Order_Month_Name": "Month", "Sales": "Total Sales ($)", "Order_Year": "Year"},
        )
        bar_fig.update_layout(
            height=430,
            legend_title_text="Order Year",
            xaxis=dict(categoryorder="array", categoryarray=MONTH_NAMES),
            margin=dict(l=10, r=10, t=45, b=10),
        )
        st.plotly_chart(bar_fig, width="stretch")

with bottom_right:
    st.markdown("### 📈 Net Profit Margin Distribution Year by Year")
    if ledger_filtered.empty:
        st.info("No data for the active filter combination.")
    else:
        monthly = (
            ledger_filtered.groupby(
                ["Order_Month_Name", "Month_Index", "Order_Year"],
                as_index=False,
            )[["Sales", "Profit"]]
            .sum()
            .sort_values(["Month_Index", "Order_Year"])
        )
        monthly["Margin"] = np.where(
            monthly["Sales"] > 0,
            (monthly["Profit"] / monthly["Sales"] * 100.0).round(2),
            0.0,
        )
        line_fig = px.line(
            monthly,
            x="Order_Month_Name",
            y="Margin",
            color="Order_Year",
            markers=True,
            title="Net Profit Margin Distribution Year by Year",
            labels={
                "Order_Month_Name": "Month",
                "Margin": "Net Profit Margin (%)",
                "Order_Year": "Year",
            },
        )
        line_fig.update_layout(
            height=430,
            legend_title_text="Order Year",
            xaxis=dict(categoryorder="array", categoryarray=MONTH_NAMES),
            margin=dict(l=10, r=10, t=45, b=10),
        )
        line_fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(line_fig, width="stretch")

st.divider()
st.caption(
    "Live engine status — every submitted transaction is scored in real time "
    "by the Dockerized Random Forest (0.984 ROC-AUC). Allowed orders append to "
    "the ledger (stamped Dec 2017); intercepted net-loss orders accumulate into "
    "the Revenue Leakage Shielded accumulator."
)
