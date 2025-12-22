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
IMG_DIR = "images"  # change if your folder name is different

# --- 🎨 STYLING (Dark Mode Friendly) ---
st.markdown("""
<style>
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

    rename_map = {
        "Pond_ID": "PondID",
        "Month_Year": "MonthYear",
        "NDVI_Mean": "NDVIMean",
        "VV_Mean": "VVMean"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

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


# --- 🧠 POND-LEVEL CONDITION CLASSIFICATION ---
def classify_pond(group: pd.DataFrame) -> pd.Series:
    total = len(group)
    water = group["Status"].astype(str).str.contains("Water", case=False, na=False).sum()
    fallow = group["Status"].astype(str).str.contains("Fallow", case=False, na=False).sum()

    water_ratio = water / total if total > 0 else 0
    fallow_ratio = fallow / total if total > 0 else 0
    ndvi_mean = group["NDVIMean"].mean()

    # Rule-based classification (you can tune thresholds later)
    if water_ratio >= 0.7:
        label = "Stable Water Pond"
    elif 0.3 <= water_ratio < 0.7:
        label = "Seasonal / Intermediate Pond"
    elif fallow_ratio >= 0.7 and ndvi_mean is not None and ndvi_mean > 0.3:
        label = "Not a Pond (Agriculture / Land)"
    else:
        label = "Uncertain / Needs Field Check"

    return pd.Series({
        "TotalMonths": total,
        "WaterMonths": water,
        "FallowMonths": fallow,
        "WaterRatio": water_ratio,
        "FallowRatio": fallow_ratio,
        "NDVI_Mean": ndvi_mean,
        "Condition": label
    })


pond_summary = df.groupby("PondID").apply(classify_pond).reset_index()

# --- 🏠 MAIN DASHBOARD HEADER ---
st.title("💧 Pond Water Monitoring Analytics")
st.markdown("### Executive Summary of Water Availability & Pond Health")
st.markdown("---")

# --- 1️⃣ KEY PERFORMANCE INDICATORS (KPIs) ---
total_ponds = df_filtered["PondID"].nunique()
total_records = len(df_filtered)
water_count = df_filtered["Status"].astype(str).str.contains("Water", case=False, na=False).sum()
fallow_count = df_filtered["Status"].astype(str).str.contains("Fallow", case=False, na=False).sum()

c1, c2, c3, c4 = st.columns(4)


def metric_card(label, value, color_hex="#FFF"):
    return f"""
    <div class="metric-card">
        <div class="metric-title">{label}</div>
        <div class="metric-value" style="color: {color_hex}">{value:,}</div>
    </div>
    """


c1.markdown(metric_card("Total Ponds", total_ponds, "#3498db"), unsafe_allow_html=True)
c2.markdown(metric_card("Total Observations", total_records, "#ecf0f1"), unsafe_allow_html=True)
c3.markdown(metric_card("Water Detected (Months)", water_count, "#2ecc71"), unsafe_allow_html=True)
c4.markdown(metric_card("Dry / Fallow (Months)", fallow_count, "#e74c3c"), unsafe_allow_html=True)

st.write("")

# --- 2️⃣ CONDITION OVERVIEW (WHAT YOUR MANAGER ASKED) ---
st.subheader("🧩 Pond Condition Classification")

cond_counts = pond_summary["Condition"].value_counts().reset_index()
cond_counts.columns = ["Condition", "Count"]

fig_cond = px.bar(
    cond_counts,
    x="Condition",
    y="Count",
    color="Condition",
    color_discrete_map={
        "Stable Water Pond": "#2ecc71",
        "Seasonal / Intermediate Pond": "#f1c40f",
        "Not a Pond (Agriculture / Land)": "#e74c3c",
        "Uncertain / Needs Field Check": "#95a5a6"
    }
)
fig_cond.update_layout(xaxis_title="", yaxis_title="Number of Ponds")
st.plotly_chart(fig_cond, use_container_width=True)

# Condition table with filter
st.markdown("#### 🔎 Pond-wise Condition Table")
cond_filter = st.selectbox(
    "Filter by condition",
    ["All"] + cond_counts["Condition"].tolist()
)

if cond_filter != "All":
    pond_view = pond_summary[pond_summary["Condition"] == cond_filter]
else:
    pond_view = pond_summary

st.dataframe(
    pond_view.sort_values("WaterRatio", ascending=False),
    use_container_width=True,
    height=400
)

st.markdown("---")

# --- 3️⃣ VISUAL ANALYTICS (STATUS + SEASONAL TRENDS) ---
col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.subheader("📌 Status Distribution")
    status_counts = df_filtered["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = {
        "Water Present - High Confidence": "#004d99",
        "Water Present - Low Confidence": "#3399ff",
        "Fallow": "#a0522d",
        "Cant determine": "#7f8c8d"
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

    water_mask = df_filtered["Status"].astype(str).str.contains("Water", case=False, na=False)
    trend = df_filtered[water_mask].groupby("MonthStr")["PondID"].nunique().reset_index()

    if not trend.empty:
        fig_trend = px.area(
            trend, x="MonthStr", y="PondID",
            markers=True,
            color_discrete_sequence=["#2ecc71"]
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

# --- 4️⃣ RELIABILITY & RISK TABLES (ALL PONDS, SCROLLABLE) ---
c_rank, c_risk = st.columns(2)

with c_rank:
    st.subheader("🏆 Most Reliable Ponds")
    st.caption("Ponds that had water most frequently (scroll to see all).")

    ranking = df.groupby("PondID")["Status"].apply(
        lambda x: (x.astype(str).str.contains("Water", case=False, na=False).sum()) / len(x) * 100
    ).sort_values(ascending=False).reset_index(name="Consistency")

    st.dataframe(
        ranking,
        column_config={
            "PondID": st.column_config.NumberColumn("Pond ID", format="%d"),
            "Consistency": st.column_config.ProgressColumn(
                "Water Consistency",
                format="%d%%",
                min_value=0,
                max_value=100
            )
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

with c_risk:
    st.subheader("⚠️ High-Risk (Dry) Ponds")
    st.caption("Ponds that are frequently fallow/dry (scroll to see all).")

    risk_stats = df.assign(
        IsFallow=df["Status"].astype(str).str.contains("Fallow", case=False, na=False)
    ).groupby("PondID").agg(
        Total=("PondID", "size"),
        Fallow=("IsFallow", "sum")
    )
    risk_stats["DryRatio"] = (risk_stats["Fallow"] / risk_stats["Total"]) * 100

    high_risk = risk_stats[risk_stats["DryRatio"] >= 50].sort_values("DryRatio", ascending=False)

    st.dataframe(
        high_risk.reset_index(),
        column_config={
            "PondID": st.column_config.NumberColumn("Pond ID", format="%d"),
            "DryRatio": st.column_config.ProgressColumn(
                "Dryness Risk",
                format="%d%%",
                min_value=0,
                max_value=100,
            )
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

# --- 5️⃣ FULL IMAGE GALLERY ---
st.markdown("---")
st.subheader("📸 Pond Image Gallery")

if os.path.exists(IMG_DIR):
    all_files = sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    if all_files:
        col_sel, col_view = st.columns([1, 3])

        with col_sel:
            st.markdown("**🔍 View Specific Pond**")
            selected_file = st.selectbox("Select Image File", all_files)

        with col_view:
            if selected_file:
                img_path = os.path.join(IMG_DIR, selected_file)
                st.image(img_path, caption=f"Displaying: {selected_file}", width=600)

        with st.expander("📂 Click to View All Images (Scrollable Grid)"):
            st.write(f"Found {len(all_files)} images.")
            cols = st.columns(4)
            for idx, file_name in enumerate(all_files):
                img_path = os.path.join(IMG_DIR, file_name)
                with cols[idx % 4]:
                    st.image(img_path, caption=file_name, use_container_width=True)
    else:
        st.warning(f"No images found in '{IMG_DIR}'. Please check file extensions.")
else:
    st.info("ℹ️ Image gallery hidden (image folder not found).")

# --- 6️⃣ SMART INSIGHTS ---
st.markdown("---")
st.subheader("💡 Smart Insights")

with st.container():
    # Fix: Access the index instead of column "PondID"
    top_risk_pond = int(high_risk.index[0]) if not high_risk.empty else "N/A"

    st.info(f"""
    **1. Condition-based Analytics:** Each pond is classified as *Stable Water*, *Seasonal*, 
    *Not a Pond (Agriculture / Land)*, or *Uncertain* based on water/fallow frequency and NDVI behaviour.

    **2. Monitoring Focus:** Use the *High-Risk (Dry) Ponds* table and the 
    *Not a Pond (Agriculture / Land)* filter in the condition table to quickly locate 
    features that behave like agriculture fields instead of true ponds.

    **3. Critical Areas:** Pond ID **{top_risk_pond}** and other high-risk ponds are dry more than 50% of the time 
    and should be prioritised for field verification or remedial action.
    """)

