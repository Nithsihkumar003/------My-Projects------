import pandas as pd
import streamlit as st
import plotly.express as px
import os

st.set_page_config(page_title="AI Anomaly Detection", layout="wide")
st.title("🤖 AI Anomaly Detection (Statistical)")

# ✅ FIXED: Use relative path
DATA_PATH = "data/shape-filtering-final.xlsx"


@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH): 
        return None
    df = pd.read_excel(DATA_PATH, sheet_name=0)
    rename_map = {"Pond_ID": "PondID", "Month_Year": "MonthYear", "NDVI_Mean": "NDVIMean"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df["Date"] = pd.to_datetime(df["MonthYear"], format="%Y-%m", errors="coerce")
    
    # ✅ ADDED: Convert NDVI to numeric (prevents errors)
    df["NDVIMean"] = pd.to_numeric(df["NDVIMean"], errors="coerce")
    
    return df


df = load_data()
if df is None: 
    st.error("❌ Data file not found. Make sure 'data/shape-filtering-final.xlsx' exists.")
    st.stop()

# --- TYPE B: STATISTICAL ANOMALY DETECTION (Z-SCORE) ---
st.header("1. Statistical Outlier Detection")
st.info("Identifying data points that deviate significantly from the pond's historical average (Z-Score > 2).")

anomalies = []

# Analyze each pond individually
for pond in df["PondID"].unique():
    pond_data = df[df["PondID"] == pond].copy()

    # Need at least 5 months of data to calculate stats
    if len(pond_data) < 5:
        continue

    # ✅ FIXED: Drop NaN values before calculating statistics
    pond_data = pond_data.dropna(subset=["NDVIMean"])
    
    if len(pond_data) < 5:  # Check again after dropping NaN
        continue

    # Calculate Statistics
    mean_ndvi = pond_data["NDVIMean"].mean()
    std_ndvi = pond_data["NDVIMean"].std()
    
    # ✅ FIXED: Prevent division by zero
    if std_ndvi == 0 or pd.isna(std_ndvi):
        continue

    # Calculate Z-Score for every month
    pond_data["Z_Score"] = (pond_data["NDVIMean"] - mean_ndvi) / std_ndvi

    # Find Anomalies (Z-Score < -1.96 means unusually LOW water)
    outliers = pond_data[pond_data["Z_Score"] < -1.96]

    for _, row in outliers.iterrows():
        anomalies.append({
            "PondID": pond,
            "Date": row["Date"],
            "NDVI": round(row["NDVIMean"], 2),
            "Average_NDVI": round(mean_ndvi, 2),
            "Deviation_Score": round(row["Z_Score"], 2),
            "Type": "Statistical Anomaly"
        })

anomaly_df = pd.DataFrame(anomalies)

# --- VISUALIZATION ---

if not anomaly_df.empty:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Detected Anomalies")
        st.write(f"Found **{len(anomaly_df)}** unusual events across all ponds.")
        st.dataframe(
            anomaly_df[["PondID", "Date", "NDVI", "Deviation_Score"]],
            use_container_width=True,
            height=400
        )

    with col2:
        st.subheader("Deep Dive Inspector")
        selected_pond = st.selectbox("Select Pond to Inspect", sorted(anomaly_df["PondID"].unique()))

        # Get data for that pond
        chart_data = df[df["PondID"] == selected_pond].sort_values("Date")

        # Plot
        fig = px.line(chart_data, x="Date", y="NDVIMean", title=f"Pond {selected_pond}: Normal vs Anomaly")

        # Add the 'Average' line
        avg_val = chart_data["NDVIMean"].mean()
        fig.add_hline(y=avg_val, line_dash="dash", annotation_text="Average", line_color="gray")

        # Highlight the anomalies (Red Dots)
        pond_anomalies = anomaly_df[anomaly_df["PondID"] == selected_pond]
        fig.add_scatter(
            x=pond_anomalies["Date"],
            y=pond_anomalies["NDVI"],
            mode='markers',
            marker=dict(color='red', size=12, symbol='x'),
            name='Anomaly'
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "🔴 Red X marks months where water/vegetation was statistically much lower than normal for this pond.")

else:
    st.success("✅ No statistical anomalies found in the dataset.")
