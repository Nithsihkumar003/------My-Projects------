import pandas as pd
import numpy as np
import joblib
import yfinance as yf

from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


TICKERS = ["NIFTYBEES.NS", "GOLDBEES.NS", "BANKBEES.NS", "MID150BEES.NS"]
MODEL_PATH = "nextday_model.pkl"
FEATURE_COLS = ["ret_1", "ret_5", "vol_chg", "ma_ratio"]


def download_daily(ticker: str) -> pd.DataFrame:
    # Force single-level columns; avoids ("Close", "TICKER") MultiIndex issues. [web:406]
    df = yf.download(
        tickers=ticker,
        period="max",
        interval="1d",
        progress=False,
        multi_level_index=False
    )
    df = df.dropna().reset_index()

    # Some yfinance versions may return lowercase/odd columns; normalize
    df.columns = [str(c).strip() for c in df.columns]

    required = {"Close", "Volume", "Date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{ticker}: missing columns {missing}. Got columns: {list(df.columns)[:20]}")

    return df


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ret_1"] = df["Close"].pct_change(1)
    df["ret_5"] = df["Close"].pct_change(5)
    df["vol_chg"] = df["Volume"].pct_change(1)

    ma_5 = df["Close"].rolling(5).mean()
    ma_10 = df["Close"].rolling(10).mean()
    df["ma_ratio"] = ma_5 / ma_10 - 1.0

    # Target: next-day direction (tomorrow close > today close)
    df["y"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    return df


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ensure columns exist (prevents your KeyError)
    for c in FEATURE_COLS + ["y"]:
        if c not in df.columns:
            raise ValueError(f"Feature column '{c}' missing. Columns are: {list(df.columns)[:30]}")

    # Replace inf with NaN then drop; sklearn needs finite values. [web:399][web:388]
    df[FEATURE_COLS] = df[FEATURE_COLS].replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=FEATURE_COLS + ["y"]).reset_index(drop=True)

    # Clip extreme values (stability)
    df[FEATURE_COLS] = df[FEATURE_COLS].clip(lower=-5, upper=5)

    return df


def build_dataset(ticker: str) -> pd.DataFrame:
    df = download_daily(ticker)
    df = make_features(df)
    df["ticker"] = ticker
    df = clean_features(df)
    return df


def main():
    all_df = pd.concat([build_dataset(t) for t in TICKERS], ignore_index=True)

    X = all_df[FEATURE_COLS]
    y = all_df["y"]

    # Final safety
    if np.isinf(X.to_numpy()).any() or np.isnan(X.to_numpy()).any():
        raise ValueError("X still has NaN/inf after cleaning. Something is wrong in data.")

    tscv = TimeSeriesSplit(n_splits=5)

    model = Pipeline(steps=[
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=300))
    ])

    scores = []
    for train_idx, test_idx in tscv.split(X):
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        scores.append(accuracy_score(y.iloc[test_idx], pred))

    print("TimeSeriesSplit accuracy (per fold):", [round(s, 4) for s in scores])
    print("Avg accuracy:", round(float(np.mean(scores)), 4))

    model.fit(X, y)
    joblib.dump({"model": model, "feature_cols": FEATURE_COLS}, MODEL_PATH)
    print("Saved:", MODEL_PATH)

    latest = all_df.groupby("ticker").tail(1).copy()
    proba_up = model.predict_proba(latest[FEATURE_COLS])[:, 1]
    latest["P(up tomorrow)"] = proba_up
    latest["Signal"] = np.where(latest["P(up tomorrow)"] >= 0.55, "UP", "DOWN")
    print(latest[["ticker", "Date", "Close", "P(up tomorrow)", "Signal"]])


if __name__ == "__main__":
    main()
