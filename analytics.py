import os
import random
import pandas as pd
import streamlit as st
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Pond Analytics Pro",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🟢 SETUP: IMAGE FOLDER ---
# Ensure this matches your actual folder name
IMG_DIR = "images"

# --- 🎨 STYLING (Dark Mode Friendly) ---
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }
    .metric-title {
        color: #B0B0B0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        color: #FFFFFF;
        font-size: 28px;
        font-weight: 700;
        margin-top: 5px;
    }
    /* Remove default dataframe index */
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

# --- 📥 DATA LOADING ---
DATA_PATH = "data/shape-filtering-final.xlsx"


@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    df = pd.read_excel(DATA_PATH, sheet_name=0)

    # Standardize column names
    rename_map = {
        "Pond_ID": "PondID", "Month_Year": "MonthYear",
        "NDVI_Mean": "NDVIMean", "VV_Mean": "VVMean"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Process types
    df["Date"] = pd.to_datetime(df["MonthYear"], format="%Y-%m", errors="coerce")
    for c in ["NDVIMean", "VVMean"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


df = load_data()

if df is None:
    st.error(f"❌ Critical Error: Data file not found at '{DATA_PATH}'. Please check the 'data' folder.")
    st.stop()

# --- 🔍 SIDEBAR FILTERS ---
st.sidebar.title("📊 Settings")
years = sorted(df["Date"].dt.year.dropna().unique())
selected_year = st.sidebar.selectbox("📅 Filter by Year", ["All"] + list(years))

if selected_year != "All":
    df_filtered = df[df["Date"].dt.year == selected_year]
else:
    df_filtered = df

# --- 🏠 MAIN DASHBOARD HEADER ---
st.title("💧 Pond Water Monitoring Analytics")
st.markdown("### Executive Summary of Water Availability & Pond Health")
st.markdown("---")

# --- 1️⃣ KEY PERFORMANCE INDICATORS (KPIs) ---
total_ponds = df_filtered["PondID"].nunique()
total_records = len(df_filtered)
water_count = df_filtered["Status"].astype(str).str.contains("Water", case=False).sum()
fallow_count = df_filtered["Status"].astype(str).str.contains("Fallow", case=False).sum()

c1, c2, c3, c4 = st.columns(4)


def metric_card(label, value, color_hex="#FFF"):
    return f"""
    <div class="metric-card">
        <div class="metric-title">{label}</div>
        <div class="metric-value" style="color: {color_hex}">{value:,}</div>
    </div>
    """


c1.markdown(metric_card("Total Ponds", total_ponds, "#3498db"), unsafe_allow_html=True)  # Blue
c2.markdown(metric_card("Total Observations", total_records, "#ecf0f1"), unsafe_allow_html=True)  # White
c3.markdown(metric_card("Water Detected (Months)", water_count, "#2ecc71"), unsafe_allow_html=True)  # Green
c4.markdown(metric_card("Dry / Fallow (Months)", fallow_count, "#e74c3c"), unsafe_allow_html=True)  # Red

st.write("")  # Spacer

# --- 2️⃣ VISUAL ANALYTICS ---
col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.subheader("📌 Status Distribution")
    status_counts = df_filtered["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    # Professional Color Scheme
    color_map = {
        "Water Present - High Confidence": "#004d99",  # Deep Navy
        "Water Present - Low Confidence": "#3399ff",  # Bright Blue
        "Fallow": "#a0522d",  # Sienna Brown
        "Cant determine": "#7f8c8d"  # Gray
    }

    fig_donut = px.pie(
        status_counts, values="Count", names="Status",
        color="Status", color_discrete_map=color_map,
        hole=0.5
    )
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(t=30, b=30, l=20, r=20),
        annotations=[dict(text='Status', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.subheader("📈 Seasonal Water Trends")
    df_filtered["MonthStr"] = df_filtered["Date"].dt.strftime("%Y-%m")

    # Filter only water records for trend
    water_mask = df_filtered["Status"].astype(str).str.contains("Water", case=False)
    trend = df_filtered[water_mask].groupby("MonthStr")["PondID"].nunique().reset_index()

    if not trend.empty:
        fig_trend = px.area(
            trend, x="MonthStr", y="PondID",
            markers=True,
            color_discrete_sequence=["#2ecc71"]  # Green area
        )
        fig_trend.update_layout(
            xaxis_title="Month",
            yaxis_title="Ponds with Water",
            margin=dict(t=10, b=10, l=10, r=10),
            hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No water data available for the selected period.")

st.markdown("---")

# --- 3️⃣ DETAILED TABLES (Reliability & Risk) ---
c_rank, c_risk = st.columns(2)

with c_rank:
    st.subheader("🏆 Most Reliable Ponds")
    st.caption("Ponds that had water most frequently.")

    # Calculate % as integer 0-100
    ranking = df.groupby("PondID")["Status"].apply(
        lambda x: (x.astype(str).str.contains("Water", case=False).sum()) / len(x) * 100
    ).sort_values(ascending=False).head(10).reset_index(name="Consistency")

    st.dataframe(
        ranking,
        column_config={
            "PondID": st.column_config.NumberColumn("Pond ID", format="%d"),
            "Consistency": st.column_config.ProgressColumn(
                "Water Consistency",
                format="%d%%",  # Integer percentage format
                min_value=0,
                max_value=100
            )
        },
        hide_index=True,
        use_container_width=True
    )

with c_risk:
    st.subheader("⚠️ High-Risk (Dry) Ponds")
    st.caption("Ponds that are frequently fallow/dry.")

    # Calculate % as integer 0-100
    risk_stats = df.assign(
        IsFallow=df["Status"].astype(str).str.contains("Fallow", case=False)
    ).groupby("PondID").agg(
        Total=("PondID", "size"),
        Fallow=("IsFallow", "sum")
    )
    risk_stats["DryRatio"] = (risk_stats["Fallow"] / risk_stats["Total"]) * 100

    high_risk = risk_stats[risk_stats["DryRatio"] >= 50].sort_values("DryRatio", ascending=False).head(10)

    st.dataframe(
        high_risk.reset_index(),
        column_config={
            "PondID": st.column_config.NumberColumn("Pond ID", format="%d"),
            "DryRatio": st.column_config.ProgressColumn(
                "Dryness Risk",
                format="%d%%",  # Integer percentage format
                min_value=0,
                max_value=100,
            )
        },
        hide_index=True,
        use_container_width=True
    )

# --- 4️⃣ IMAGE GALLERY PREVIEW ---
# --- 4️⃣ FULL IMAGE GALLERY ---
st.markdown("---")
st.subheader("📸 Pond Image Gallery")

if os.path.exists(IMG_DIR):
    all_files = sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    if all_files:
        # OPTION A: Select specific image
        col_sel, col_view = st.columns([1, 3])

        with col_sel:
            st.markdown("**🔍 View Specific Pond**")
            # Try to extract numbers from filenames for easier sorting
            selected_file = st.selectbox("Select Image File", all_files)

        with col_view:
            if selected_file:
                img_path = os.path.join(IMG_DIR, selected_file)
                st.image(img_path, caption=f"Displaying: {selected_file}", width=600)

        # OPTION B: Browse All (Grid View)
        with st.expander("📂 Click to View All Images (Scrollable Grid)"):
            st.write(f"Found {len(all_files)} images.")

            # Create a 4-column grid
            cols = st.columns(4)
            for idx, file_name in enumerate(all_files):
                img_path = os.path.join(IMG_DIR, file_name)
                with cols[idx % 4]:
                    st.image(img_path, caption=file_name, use_container_width=True)

    else:
        st.warning(f"No images found in '{IMG_DIR}'. Please check file extensions.")
else:
    st.info("ℹ️ Image gallery hidden (Image folder not found).")

# --- 5️⃣ AUTOMATED INSIGHTS ---
st.markdown("---")
st.subheader("💡 Smart Insights")

with st.container():
    st.info(f"""
    **1. Overall Health:** The dataset tracks **{total_ponds} ponds**. We found **{water_count}** confirmed water instances versus **{fallow_count}** dry instances.

    **2. Seasonal Pattern:** As shown in the *Seasonal Water Trends* chart, water availability varies significantly by month. Use the **Year Filter** on the left to analyze specific drought or monsoon years.

    **3. Critical Areas:** The *High-Risk Table* identifies ponds (like ID **{high_risk.index[0] if not high_risk.empty else 'N/A'}**) that are dry more than 50% of the time. These require immediate field verification.
    """)
