import time
import os
import json
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.express as px
import joblib
import numpy as np
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# -------- Settings --------
st.set_page_config(page_title="My Portfolio Dashboard", layout="wide")
REFRESH_SECONDS = 60
KITE_PRICE_FILE = "kite_prices.json"
KITE_STALE_SECONDS = 30  # if file older than this, we consider it stale

MODEL_PATH = "nextday_model.pkl"
PRED_THRESHOLD = 0.55  # probability threshold to label UP/DOWN

# Auto-refresh safely
st_autorefresh(interval=REFRESH_SECONDS * 1000, key="refresh")

st.title("Live ETF Tracker (Kite LTP preferred, Yahoo fallback)")

def load_kite_prices():
    """
    Expected JSON format:
    {
      "ts": 1737830000.0,
      "prices": { "MIDCAPETF": 217.04, "NIFTYBEES": 284.0, ... }
    }
    """
    if not os.path.exists(KITE_PRICE_FILE):
        return {}, None, "kite_prices.json not found"
    try:
        with open(KITE_PRICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("ts", None)
        prices = data.get("prices", {})
        if not isinstance(prices, dict):
            return {}, ts, "Invalid prices format"
        return prices, ts, None
    except Exception as e:
        return {}, None, f"Error reading kite_prices.json: {e}"

@st.cache_data(ttl=REFRESH_SECONDS)
def fetch_intraday(tickers: list[str]) -> pd.DataFrame:
    return yf.download(
        tickers=tickers,
        period="1d",
        interval="1m",
        group_by="ticker",
        progress=False,
        threads=True
    )

@st.cache_data(ttl=3600)  # cache daily history for 1 hour [web:422]
def fetch_daily(ticker: str) -> pd.DataFrame:
    # yfinance daily history [web:350]
    df = yf.download(ticker, period="2y", interval="1d", progress=False)
    df = df.dropna().reset_index()
    return df

@st.cache_data(ttl=3600)
def load_prediction_model():
    if not os.path.exists(MODEL_PATH):
        return None, None, f"{MODEL_PATH} not found. Run train_predict.py first."
    try:
        pack = joblib.load(MODEL_PATH)
        model = pack.get("model")
        feature_cols = pack.get("feature_cols")
        if model is None or feature_cols is None:
            return None, None, f"{MODEL_PATH} is missing 'model' or 'feature_cols'. Retrain."
        return model, feature_cols, None
    except Exception as e:
        return None, None, f"Error loading {MODEL_PATH}: {e}"

def compute_features_for_today(df: pd.DataFrame):
    df = df.copy()

    if "Close" not in df.columns or "Volume" not in df.columns:
        return None

    df["ret_1"] = df["Close"].pct_change(1)
    df["ret_5"] = df["Close"].pct_change(5)
    df["vol_chg"] = df["Volume"].pct_change(1)

    ma_5 = df["Close"].rolling(5).mean()
    ma_10 = df["Close"].rolling(10).mean()
    df["ma_ratio"] = ma_5 / ma_10 - 1.0

    # keep last valid row
    df = df.replace([np.inf, -np.inf], np.nan)
    row = df.dropna().tail(1)
    if row.empty:
        return None

    feats = {
        "ret_1": float(row["ret_1"].iloc[0]),
        "ret_5": float(row["ret_5"].iloc[0]),
        "vol_chg": float(row["vol_chg"].iloc[0]),
        "ma_ratio": float(row["ma_ratio"].iloc[0]),
    }

    # clip similar to training
    for k in feats:
        feats[k] = float(np.clip(feats[k], -5, 5))

    return feats


# -------- Load holdings.csv (robust) --------
holdings = pd.read_csv("holdings.csv", skipinitialspace=True)
holdings.columns = holdings.columns.str.strip()

# Normalize column lookup
col_map = {c.strip().lower(): c for c in holdings.columns}

def find_col(possible_names: list[str], contains_all: list[str] | None = None):
    for n in possible_names:
        if n in col_map:
            return col_map[n]
    if contains_all:
        for c in holdings.columns:
            cl = c.lower()
            if all(x in cl for x in contains_all):
                return c
    return None

name_col = find_col(["name"])
ticker_col = find_col(["ticker", "symbol", "tradingsymbol"], contains_all=["tick"])
qty_col = find_col(["quantity", "qty", "q"], contains_all=["quant"])
avg_col = find_col(["avgbuyprice", "avg_buy_price", "avgprice", "avg"], contains_all=["avg", "buy"])

with st.expander("Debug: CSV loaded"):
    st.write("CSV columns:", list(holdings.columns))
    st.write(holdings.head())

if name_col is None or ticker_col is None or qty_col is None or avg_col is None:
    st.error(
        "Your holdings.csv must contain columns for Name, Ticker, Quantity, AvgBuyPrice.\n\n"
        f"Found columns: {list(holdings.columns)}"
    )
    st.stop()

# Clean values
holdings[name_col] = holdings[name_col].astype(str).str.strip()
holdings[ticker_col] = holdings[ticker_col].astype(str).str.strip()
holdings[qty_col] = pd.to_numeric(holdings[qty_col], errors="coerce")
holdings[avg_col] = pd.to_numeric(holdings[avg_col], errors="coerce")

holdings = holdings.dropna(subset=[ticker_col, qty_col, avg_col])
holdings = holdings[(holdings[qty_col] > 0) & (holdings[avg_col] > 0)]

# ---- Load Kite prices ----
kite_prices, kite_ts, kite_err = load_kite_prices()
kite_age = None
if kite_ts is not None:
    kite_age = time.time() - float(kite_ts)

if kite_err:
    st.info(f"Kite LTP source not active: {kite_err}. Using Yahoo fallback. (Yahoo may differ from broker LTP)")
elif kite_age is not None and kite_age > KITE_STALE_SECONDS:
    st.warning(f"Kite LTP file is stale (~{int(kite_age)}s old). Using it anyway; refresh your scraper if needed.")
else:
    st.success("Kite LTP source is active. Table/P&L will prefer Kite prices.")

# ---- Prediction model load ----
model, feature_cols, model_err = load_prediction_model()
if model_err:
    st.info(f"Prediction model not active: {model_err}")
else:
    st.success("Next-day prediction model loaded.")

# yfinance used for intraday chart + fallback prev close/Δ
tickers = holdings[ticker_col].tolist()
raw = fetch_intraday(tickers)

# -------- Build holdings table --------
rows = []
for _, r in holdings.iterrows():
    name = r[name_col]
    tkr = r[ticker_col]
    qty = float(r[qty_col])
    avg_buy = float(r[avg_col])

    last = None
    prev = None
    chg = None
    chg_pct = None

    # Prefer Kite LTP
    if name in kite_prices:
        try:
            last = float(kite_prices[name])
        except Exception:
            last = None

    # yfinance fallback + prev for Δ
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            series = raw[(tkr, "Close")].dropna()
        else:
            series = raw["Close"].dropna()

        if last is None and len(series) > 0:
            last = float(series.iloc[-1])

        if len(series) >= 2:
            prev = float(series.iloc[-2])
        elif last is not None:
            prev = last

        if last is not None and prev is not None:
            chg = last - prev
            chg_pct = (chg / prev * 100) if prev != 0 else 0.0
    except Exception:
        if last is not None:
            prev = last
            chg = 0.0
            chg_pct = 0.0

    invested = avg_buy * qty
    value = (last * qty) if last is not None else None
    pnl = (value - invested) if value is not None else None
    pnl_pct = (pnl / invested * 100) if (pnl is not None and invested != 0) else None

    rows.append({
        "Name": name,
        "Ticker": tkr,
        "Qty": qty,
        "AvgBuy": avg_buy,
        "Last": last,
        "Invested": invested,
        "Value": value,
        "PnL": pnl,
        "PnL%": pnl_pct,
        "Δ": chg,
        "Δ%": chg_pct
    })

table = pd.DataFrame(rows)

# Totals
total_invested = float(table["Invested"].dropna().sum()) if "Invested" in table else 0.0
total_value = float(table["Value"].dropna().sum()) if "Value" in table else 0.0
total_pnl = total_value - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested != 0 else 0.0

# -------- Prediction table --------
pred_df = None
if model is not None:
    pred_rows = []
    for _, r in holdings.iterrows():
        tkr = r[ticker_col]
        hist = fetch_daily(tkr)
        feats = compute_features_for_today(hist)

        if feats is None:
            pred_rows.append({"Ticker": tkr, "P(up tomorrow)": None, "Signal": "NA"})
            continue

        Xp = pd.DataFrame([feats])[feature_cols]
        p_up = float(model.predict_proba(Xp)[0, 1])
        sig = "UP" if p_up >= PRED_THRESHOLD else "DOWN"
        pred_rows.append({"Ticker": tkr, "P(up tomorrow)": p_up, "Signal": sig})

    pred_df = pd.DataFrame(pred_rows)

# -------- Layout --------
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("Portfolio KPIs")
    st.metric("Total invested", f"₹{total_invested:,.0f}")
    st.metric("Total value", f"₹{total_value:,.0f}")
    st.metric("Total P&L", f"₹{total_pnl:,.0f}", f"{total_pnl_pct:.2f}%")

    if pred_df is not None:
        st.subheader("Next-day prediction (model)")
        st.caption(f"Signal rule: UP if P(up tomorrow) ≥ {PRED_THRESHOLD:.2f}")
        st.dataframe(pred_df, hide_index=True, use_container_width=True)

    st.subheader("Holdings (Kite LTP preferred)")
    st.dataframe(table, hide_index=True, use_container_width=True)

    if kite_ts is not None and kite_age is not None:
        st.caption(
            f"Auto-refresh: every {REFRESH_SECONDS}s • Local time: {time.strftime('%H:%M:%S')} • "
            f"Kite LTP age: {int(kite_age)}s"
        )
    else:
        st.caption(f"Auto-refresh: every {REFRESH_SECONDS}s • Local time")


