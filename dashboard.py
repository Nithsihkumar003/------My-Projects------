import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

DATA_PATH = "C:\Pond_data_analysis\data\shape-filtering-final.xlsx"
IMG_DIR = "images"

@st.cache_data
def load_data(xlsx_file):
    df = pd.read_excel(xlsx_file, sheet_name=0)

    # Normalize column names (adjust if your sheet differs)
    rename_map = {
        "Pond_ID": "PondID",
        "Month_Year": "MonthYear",
        "NDVI_Mean": "NDVIMean",
        "NDWI_Mean": "NDWIMean",
        "NDTI_Mean": "NDTIMean",
        "VV_Mean": "VVMean",
        "VH_Mean": "VHMean",
        "Shape_Score": "ShapeScore",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Parse month
    df["Date"] = pd.to_datetime(df["MonthYear"], format="%Y-%m", errors="coerce")

    # Force numeric columns (handles blanks)
    num_cols = ["NDVIMean", "NDWIMean", "NDTIMean", "VVMean", "VHMean", "ShapeScore"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

def status_color(status: str):
    s = (status or "").lower()
    if "high confidence" in s: return "navy"
    if "low confidence" in s: return "cyan"
    if "fallow" in s: return "saddlebrown"
    return "gray"

def make_plot(dfp: pd.DataFrame, pond_id: int):
    fig = go.Figure()

    # Optical indices (left axis)
    fig.add_trace(go.Scatter(x=dfp["Date"], y=dfp["NDVIMean"], mode="lines+markers", name="NDVI"))
    fig.add_trace(go.Scatter(x=dfp["Date"], y=dfp["NDTIMean"], mode="lines+markers", name="NDTI"))

    # SAR VV (right axis)
    fig.add_trace(go.Scatter(x=dfp["Date"], y=dfp["VVMean"], mode="lines+markers",
                             name="VV", yaxis="y2", line=dict(dash="dash")))

    # Status markers
    fig.add_trace(go.Scatter(
        x=dfp["Date"],
        y=[0]*len(dfp),  # a reference line
        mode="markers",
        name="Status",
        marker=dict(size=10, color=[status_color(s) for s in dfp["Status"]]),
        hovertext=dfp["Status"].astype(str) + "<br>" + dfp["Reason"].astype(str),
        hoverinfo="text"
    ))

    fig.update_layout(
        title=f"Pond {pond_id}: Multi-Spectral Dashboard",
        xaxis_title="Date",
        yaxis_title="Optical indices",
        yaxis2=dict(title="SAR VV (dB)", overlaying="y", side="right"),
        legend=dict(orientation="h")
    )
    return fig

st.set_page_config(page_title="Pond Water Monitoring", layout="wide")
st.title("Pond Water Monitoring Dashboard")

# OPTION A (client-friendly): allow user to upload Excel in the app
uploaded_xlsx = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])  # file-like object [web:80]

xlsx_to_use = uploaded_xlsx if uploaded_xlsx is not None else DATA_PATH
df = load_data(xlsx_to_use)

pond_ids = sorted(df["PondID"].dropna().unique().astype(int))
pond_id = st.selectbox("Select Pond", pond_ids)

d = df[df["PondID"].astype(int) == int(pond_id)].sort_values("Date")
# 1) make sure Date is valid
d = d.dropna(subset=["Date"])

# 2) convert pandas.Timestamp -> python datetime (fixes Streamlit slider issue)
min_d = d["Date"].min().to_pydatetime()
max_d = d["Date"].max().to_pydatetime()

date_range = st.slider(
    "Date range",
    min_value=min_d,
    max_value=max_d,
    value=(min_d, max_d),
)
start_dt, end_dt = date_range

# 3) filter
d = d[(d["Date"] >= start_dt) & (d["Date"] <= end_dt)]

d = d[(d["Date"] >= date_range[0]) & (d["Date"] <= date_range[1])]

left, right = st.columns([2, 1])

with left:
    fig = make_plot(d, pond_id)
    st.plotly_chart(fig, use_container_width=True)  # renders Plotly in Streamlit [web:76]
    import io

png_bytes = fig.to_image(format="png")  # requires kaleido
st.download_button(
    label="Download chart (PNG)",
    data=png_bytes,
    file_name=f"pond_{pond_id}_{start_dt.date()}_{end_dt.date()}.png",
    mime="image/png",
)


with right:
    st.subheader("Quick stats")
    st.write(d["Status"].value_counts(dropna=False))

    st.download_button(
        "Download filtered data (CSV)",
        data=d.to_csv(index=False).encode("utf-8"),
        file_name=f"pond_{pond_id}_filtered.csv",
        mime="text/csv"
    )

    # Show corresponding pond image if present
    img_path = os.path.join(IMG_DIR, f"Pond_{pond_id}_Final.jpg")
    if os.path.exists(img_path):
        st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
