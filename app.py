from __future__ import annotations
import json
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
from datetime import datetime
from pathlib import Path

from src.agent.graph import run_agent
from src.config import CITIES, LANGFUSE_HOST, REPORTS_DIR
from src.tools.aqi import aqi_color, aqi_category

# Page Config
st.set_page_config(page_title="Autonomous Air Quality Agent", page_icon="🌍", layout="wide")

# Custom CSS for premium dark theme
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    /* Highlight Teal */
    .highlight-teal {
        color: #00D4AA;
        font-weight: 600;
    }
    
    /* Badges */
    .badge-safe { background-color: rgba(0, 228, 0, 0.2); color: #00E400; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
    .badge-warning { background-color: rgba(255, 179, 71, 0.2); color: #FFB347; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
    .badge-critical { background-color: rgba(255, 107, 107, 0.2); color: #FF6B6B; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Session State
if 'last_result' not in st.session_state:
    # Auto-load the most recent saved report so data shows without re-running
    st.session_state['last_result'] = None
    try:
        report_files = sorted(Path(REPORTS_DIR).glob("*.json"))
        if report_files:
            with open(report_files[-1], "r", encoding="utf-8") as f:
                st.session_state['last_result'] = json.load(f)
    except Exception:
        pass
if 'is_running' not in st.session_state:
    st.session_state['is_running'] = False

def trigger_agent_run():
    st.session_state['is_running'] = True
    with st.spinner("Agent is fetching and analyzing data..."):
        try:
            res = run_agent()
            st.session_state['last_result'] = res
        except Exception as e:
            st.error(f"Agent run failed: {e}")
    st.session_state['is_running'] = False

# Sidebar
with st.sidebar:
    st.title("🌍 AQ Monitoring")
    st.markdown("Autonomous AI Agent powered by **LangGraph**.")
    
    if st.button("🚀 Run Agent Now", use_container_width=True, disabled=st.session_state['is_running']):
        trigger_agent_run()
        st.rerun()
        
    res = st.session_state['last_result']
    if res:
        alert = res.get("alert_level", "UNKNOWN")
        badge_class = f"badge-{alert.lower()}"
        st.markdown(f"**Status**: <span class='{badge_class}'>{alert}</span>", unsafe_allow_html=True)
        st.markdown(f"**Last Run**: {datetime.now().strftime('%H:%M:%S')}")
        st.markdown(f"**Duration**: {res.get('run_duration_seconds')}s")
        st.markdown(f"**Cities Monitored**: {len(res.get('city_aqi', {}))}")
        
    st.divider()
    st.markdown("### Tech Stack")
    st.markdown("`LangGraph` `Folium` `OpenAQ` `IsolationForest`")

# Main Content
tab1, tab2, tab3 = st.tabs(["🗺️ Live AQI Map", "🚨 Anomalies & Correl", "🔍 Observability"])

with tab1:
    st.markdown("<h2 class='highlight-teal'>Live AQI Map</h2>", unsafe_allow_html=True)
    res = st.session_state['last_result']
    
    if not res:
        st.info("No data available. Click 'Run Agent Now' to start the monitoring pipeline.")
    else:
        alert_level = res.get("alert_level", "")
        if alert_level == "CRITICAL":
            critical = res.get("critical_cities", [])
            st.error(f"🚨 CRITICAL AIR QUALITY — {', '.join(critical)} exceed AQI 200. Immediate action required.")
        elif alert_level == "WARNING":
            warning = res.get("warning_cities", [])
            st.warning(f"⚠️ WARNING — {', '.join(warning)} have elevated AQI (100–200).")
        else:
            st.success("✅ All cities within safe AQI levels.")
            
        # Folium Map
        m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="cartodbdark_matter")
        
        for city, aqi in res.get("city_aqi", {}).items():
            if aqi is None:
                continue
            coords = CITIES.get(city)
            if not coords:
                continue
            
            color = aqi_color(aqi)
            cat = aqi_category(aqi)
            pm25 = res.get("clean_measurements", {}).get(city, {}).get("pm25", "N/A")
            
            popup_html = f"""
            <div style="font-family: Arial; min-width: 150px;">
                <h4>{city}</h4>
                <p><b>AQI:</b> {aqi} ({cat})</p>
                <p><b>PM2.5:</b> {pm25} µg/m³</p>
            </div>
            """
            
            folium.CircleMarker(
                location=[coords["lat"], coords["lon"]],
                radius=10,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{city}: {aqi}"
            ).add_to(m)
            
        st_folium(m, width=1000, height=500, returned_objects=[])

with tab2:
    st.markdown("<h2 class='highlight-teal'>Analysis Dashboard</h2>", unsafe_allow_html=True)
    res = st.session_state['last_result']
    
    if not res:
        st.info("No data available.")
    else:
        # Anomalies
        st.subheader("Detected Anomalies")
        anomalies = res.get("anomaly_details", [])
        if anomalies:
            df_an = pd.DataFrame(anomalies)
            st.dataframe(df_an, use_container_width=True)
        else:
            st.success("No anomalies detected today.")
            
        st.divider()
        
        # City PM2.5 Bar Chart
        st.subheader("City PM2.5 Levels")
        clean = res.get("clean_measurements", {})
        data_list = []
        for city, data in clean.items():
            aqi = res["city_aqi"].get(city)
            if aqi:
                data_list.append({
                    "City": city,
                    "PM2.5": data.get("pm25", 0),
                    "AQI": aqi,
                    "Category": aqi_category(aqi)
                })
        if data_list:
            df_bar = pd.DataFrame(data_list)
            fig = px.bar(df_bar, x="City", y="PM2.5", color="Category", 
                         title="PM2.5 Concentration by City",
                         color_discrete_map={
                             "Good": "#00E400", "Moderate": "#FFFF00", 
                             "Unhealthy for Sensitive": "#FF7E00", "Unhealthy": "#FF0000",
                             "Very Unhealthy": "#8F3F97", "Hazardous": "#7E0023"
                         })
            fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        
        # Weather Correlation
        st.subheader("Weather Correlator (Temperature vs PM2.5)")
        corr = res.get("pm25_correlation")
        if corr:
            col1, col2, col3 = st.columns(3)
            col1.metric("Pearson r", f"{corr['pearson_r']:.2f}")
            col2.metric("p-value", f"{corr['p_value']:.4f}")
            col3.markdown(f"**Interpretation**: {corr['interpretation']}")
        else:
            st.write("Insufficient data for correlation.")

with tab3:
    st.markdown("<h2 class='highlight-teal'>Observability (LangFuse)</h2>", unsafe_allow_html=True)
    res = st.session_state['last_result']
    
    if not res:
        st.info("No data available.")
    else:
        run_id = res.get("run_id", "")
        run_date = res.get("run_date", "")
        
        st.markdown(f"**Run ID:** `{run_id}`")
        st.markdown(f"**Run Date:** `{run_date}`")
        st.markdown(f"**Total Duration:** `{res.get('run_duration_seconds')}s`")
        
        st.markdown("### Node Execution Times")
        timings = res.get("node_timings", {})
        if timings:
            df_time = pd.DataFrame(list(timings.items()), columns=["Node", "Duration (s)"])
            st.dataframe(df_time, use_container_width=True)
            
        st.divider()
        st.markdown(f"🔗 [Open LangFuse Dashboard]({LANGFUSE_HOST})")
        st.caption(f"All agent traces are visible in your LangFuse project at {LANGFUSE_HOST}")
