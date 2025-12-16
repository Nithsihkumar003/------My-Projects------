import pandas as pd
import streamlit as st
import plotly.express as px
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Pond Analytics", layout="wide")
st.title("📊 Pond Water Analytics Report")

# --- DATA LOADING ---
# Use raw string (r"...") or forward slashes for Windows paths to avoid errors
DATA_PATH = r"C:\Pond_data_analysis\data\shape-filtering-final.xlsx"


@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None

    df = pd.read_excel(DATA_PATH, sheet_name=0)

    # Rename & Clean
    rename_map = {
        "Pond_ID": "PondID",
        "Month_Year": "MonthYear",
        "NDVI_Mean": "NDVIMean",
        "VV_Mean": "VVMean"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Process Dates and Numeric Columns
    df["Date"] = pd.to_datetime(df["MonthYear"], format="%Y-%m", errors="coerce")
    for c in ["NDVIMean", "VVMean"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


df = load_data()

if df is None:
    st.error(f"Data missing! Could not find file at: {DATA_PATH}")
    st.stop()

# --- ANALYTICS SECTIONS ---

# 1. KPIs
st.header("1. Project Overview")
c1, c2, c3 = st.columns(3)

total_ponds = df["PondID"].nunique()
total_months = len(df)
# Count rows where 'Status' contains "Water" (case-insensitive)
water_months = df[df["Status"].astype(str).str.contains("Water", case=False, na=False)].shape[0]

c1.metric("Total Ponds", total_ponds)
c2.metric("Total Months Analyzed", total_months)
c3.metric("Water Detected (Months)", water_months)

# 2. Trends
st.header("2. Seasonal Water Trends")
trend = df.groupby(["Date", "Status"]).size().reset_index(name="Count")

fig1 = px.bar(
    trend,
    x="Date",
    y="Count",
    color="Status",
    title="Status Count per Month",
    color_discrete_map={
        "Water Present - High Confidence": "navy",
        "Fallow": "brown",
        "Cant determine": "gray"
    }
)
st.plotly_chart(fig1, use_container_width=True)

# 3. Ranking
st.header("3. Top Reliable Ponds")
ranking = df.groupby("PondID")["Status"].apply(
    lambda x: (x.astype(str).str.contains("Water", case=False).sum()) / len(x) * 100
).sort_values(ascending=False).reset_index(name="Water %")

st.dataframe(
    ranking,
    column_config={
        "Water %": st.column_config.ProgressColumn(
            "Water Consistency",
            format="%.1f%%",
            min_value=0,
            max_value=100
        )
    },
    use_container_width=True
)
