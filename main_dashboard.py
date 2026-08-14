import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Global Budget Analytics Core", layout="wide")

def get_engine():
    password_quoted = urllib.parse.quote_plus("yourpassword")
    return create_engine(
        f"mysql+mysqlconnector://yourusername:{password_quoted}@localhost/global_budget_db"
    )

st.title("🏛️ Global Government Budget Analytics Core")
st.markdown("An interactive platform exploring public finance shifts, sector dominance, and predictive trajectories.")

# SIDEBAR REGIONAL FILTERS
engine = get_engine()
countries_df = pd.read_sql_query("SELECT country_name FROM countries ORDER BY country_name",engine)
engine.dispose()

selected_country = st.sidebar.selectbox("Select a Country to Filter",countries_df["country_name"].tolist())

# NAVIGATION TABS FOR CLEAN PROCESS SEPARATION
tab_macro, tab_sectors, tab_anomalies, tab_research_lab = st.tabs([
    "📈 Macro Historical Trends",
    "🧱 Sector Structural Spreads",
    "🔍 Statistical Anomalies",
    "🔬 Macro Economic Research Lab"
])

with tab_macro:
    st.header("Global Spending Growth Pathways")
    engine = get_engine()
    q = """
        SELECT b.year, b.total_budget_billions_usd
        FROM budgets b JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s ORDER BY b.year 
    """
    df_macro = pd.read_sql_query(q, engine, params=(selected_country,))
    engine.dispose()

    if not df_macro.empty:
        fig = px.line(df_macro,x="year",y="total_budget_billions_usd",
                title=f"Historical Expenditure Strategy: {selected_country}",
                template="plotly_dark",labels={"total_budget_billions_usd": "Total Budget (Billions USD)"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No records found for the selection.")

with tab_sectors:
    st.header("Allocation Distribution Analysis")
    engine = get_engine()
    q_sec = """
        SELECT b.year,sa.sector_name,sa.allocated_percentage,sa.allocated_amount_billions_usd
        FROM sector_allocations sa
        JOIN budgets b ON sa.budget_id = b.budget_id
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s
    """
    df_sec = pd.read_sql_query(q_sec, engine, params=(selected_country,))
    engine.dispose()

    if not df_sec.empty:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_area = px.area(df_sec,x="year",y="allocated_percentage",color="sector_name",
                            title="Structural Budget Shifts Over Time",template="plotly_dark")
            st.plotly_chart(fig_area, use_container_width=True)
        with col_c2:
            fig_box = px.box(df_sec,x="sector_name",y="allocated_percentage",color="sector_name",
                            title="Variance and Spread Across Sectors",template="plotly_dark")
            st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No sector records found.")

with tab_anomalies:
    st.header("Descriptive Outlier Detection")
    st.markdown("Identifies fiscal years where spending shifted sharply outside normal historical baselines.")

    if not df_macro.empty:
        mean_val = df_macro["total_budget_billions_usd"].mean()
        std_val = df_macro["total_budget_billions_usd"].std()

        df_macro["z_score"] = (df_macro["total_budget_billions_usd"] - mean_val) / std_val
        anomalies = df_macro[df_macro["z_score"].abs() > 1.96]

        st.write("### Flagged Fiscal Outlier Periods (Z-Score > 1.96):")
        if not anomalies.empty:
            st.dataframe(anomalies.style.background_gradient(cmap="Reds",subset=["total_budget_billions_usd"]),use_container_width=True)
        else:
            st.success("Excellent budget structural stability! No extreme statistical outliers discovered.")

with tab_research_lab:
    st.header("🧠 Deep Exploratory Research Workspace")
    st.markdown("Advanced analytical modules calculating structural correlation shifts and spending volatility.")

    # Render Analysis C (Correlation Matrix) visually as an interactive heatmap
    st.subheader("Cross-Sector Allocation Correlation Matrix")
    engine = get_engine()
    q_corr = """
        SELECT b.year,sa.sector_name,sa.allocated_percentage
        FROM sector_allocations sa
        JOIN budgets b ON sa.budget_id = b.budget_id
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s;
    """
    df_corr_raw = pd.read_sql(q_corr, engine, params=(selected_country,))
    engine.dispose()

    if not df_corr_raw.empty:
        pivot_df = df_corr_raw.pivot(index="year",columns="sector_name",values="allocated_percentage")
    corr_matrix = pivot_df.corr()

    # Build an interactive Plotly Heatmap chart layout
    fig_heat = px.imshow(
        corr_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu",  # Red-Blue scale highlights positive vs negative relationships clearly
        labels=dict(color="Correlation Coefficient"),
        template="plotly_dark"
    )
    st.plotly_chart(fig_heat, use_container_width=True)
# --- Volatility Index & Rolling Statistics ---
st.subheader("Volatility Index & Rolling Statistics")
engine = get_engine()
q_vol = """
    SELECT b.year,b.total_budget_billions_usd
    FROM budgets b JOIN countries c ON b.country_id = c.country_id
    WHERE c.country_name = %s ORDER BY b.year ASC
"""
df_vol = pd.read_sql(q_vol, engine, params=(selected_country,))
engine.dispose()

if not df_vol.empty:
    df_vol = df_vol.sort_values("year")
    df_vol["rolling_mean"] = df_vol["total_budget_billions_usd"].rolling(window=10).mean()
    df_vol["rolling_std"] = df_vol["total_budget_billions_usd"].rolling(window=10).std()
    df_vol["volatility_index"] = (df_vol["rolling_std"] / df_vol["rolling_mean"]) * 100

    st.markdown("Rolling 10-year Volatility Index (Coefficient of Variation)")
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Scatter(x=df_vol["year"],y=df_vol["volatility_index"],mode="lines+markers",name="Volatility Index",line=dict(color="#FFA500")))
    fig_vol.update_layout(template="plotly_dark",yaxis_title="Volatility Index (%)")
    st.plotly_chart(fig_vol, use_container_width=True)

    st.write("Recent rolling statistics (non-null rows):")
    st.dataframe(df_vol.dropna().tail(10), use_container_width=True)
else:
    st.info("Not enough historical data to compute volatility metrics for this country.")

# --- Polynomial Projection (Analytical) ---
st.subheader("Polynomial Projection (Analytical)")
col_p1, col_p2 = st.columns(2)
with col_p1:
    proj_degree = st.selectbox("Projection degree",[1, 2, 3],index=1)
    proj_horizon = st.number_input("Forecast horizon year",min_value=2025,max_value=2050,value=2035)
with col_p2:
    apply_scenario = st.checkbox("Apply scenario shock to projection")
    shock_pct = st.slider("Shock %",-50,100,0)

if not df_vol.empty:
    x = df_vol["year"].astype(int).values
    y = df_vol["total_budget_billions_usd"].astype(float).values
    if len(x) > proj_degree:
        coeffs = np.polyfit(x, y, deg=proj_degree)
        poly = np.poly1d(coeffs)
        years_future = np.arange(int(x.max()) + 1,int(proj_horizon) + 1)
        proj_vals = poly(years_future)
        if apply_scenario and shock_pct != 0:
            proj_vals = proj_vals * (1 + shock_pct / 100.0)

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(x=x,y=y,mode="markers+lines",name="Historical",marker=dict(color="#888888")))
        fig_proj.add_trace(go.Scatter(x=years_future,y=proj_vals,mode="lines",name="Projection",line=dict(color="#00FFAA", dash="dash")))
        fig_proj.update_layout(title=f"Polynomial Projection (deg {proj_degree}) for {selected_country}",template="plotly_dark",xaxis_title="Year",yaxis_title="Budget (Billions USD)")
        st.plotly_chart(fig_proj, use_container_width=True)

        df_proj_out = pd.DataFrame({"year": years_future,"projected_budget": proj_vals})
        st.dataframe(df_proj_out.style.format({"projected_budget": "${:,.2f}"}),use_container_width=True)
    else:
        st.warning("Not enough historical points for the selected polynomial degree.")
