from __future__ import annotations

import os
import uuid
import time
import base64
import logging
from datetime import date
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START

# Ensure .env is loaded before anything reads env vars
load_dotenv()

from src.agent.state import AgentState
from src.agent.nodes.fetcher import fetch_data
from src.agent.nodes.validator import validate
from src.agent.nodes.anomaly import detect_anomalies
from src.agent.nodes.weather import correlate_weather
from src.agent.nodes.alert import route_alert

log = logging.getLogger(__name__)


def build_graph():
    """Compile the 5-node LangGraph StateGraph."""
    graph = StateGraph(AgentState)
    graph.add_node("fetch_data",        fetch_data)
    graph.add_node("validate",          validate)
    graph.add_node("detect_anomalies",  detect_anomalies)
    graph.add_node("correlate_weather", correlate_weather)
    graph.add_node("route_alert",       route_alert)

    graph.add_edge(START,               "fetch_data")
    graph.add_edge("fetch_data",        "validate")
    graph.add_edge("validate",          "detect_anomalies")
    graph.add_edge("detect_anomalies",  "correlate_weather")
    graph.add_edge("correlate_weather", "route_alert")
    graph.add_edge("route_alert",       END)

    return graph.compile()


def _setup_langfuse():
    """Set up LangFuse 4.x CallbackHandler with correct OTLP endpoint.

    Sets OTEL env vars BEFORE importing CallbackHandler so the OTel exporter
    picks up the right endpoint. For EU region:
        OTLP endpoint = https://eu.cloud.langfuse.com/api/public/otel
    Returns (handler, dashboard_url) or (None, '') if setup fails — never raises.
    """
    try:
        pk   = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        sk   = os.getenv("LANGFUSE_SECRET_KEY", "")
        host = os.getenv("LANGFUSE_HOST", "https://eu.cloud.langfuse.com").rstrip("/")

        if not (pk and sk):
            log.warning("LangFuse keys not set — tracing disabled")
            return None, ""

        # Build OTLP auth header Basic base64(pk:sk)
        auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
        otlp = f"{host}/api/public/otel"
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"]  = f"Authorization=Basic {auth}"

        from langfuse.langchain import CallbackHandler
        handler       = CallbackHandler()
        dashboard_url = f"{host}/traces"
        log.info(f"LangFuse tracing enabled → {otlp}")
        return handler, dashboard_url

    except Exception as e:
        log.warning(f"LangFuse setup failed (tracing disabled): {e}")
        return None, ""


def run_agent(cities=None) -> AgentState:
    """Run the full AQ monitoring agent pipeline and return the final state."""
    run_id   = str(uuid.uuid4())[:8]
    run_date = date.today().isoformat()

    # ── LangFuse (non-blocking) ────────────────────────────────────────────
    lf_handler, dashboard_url = _setup_langfuse()

    # ── Build initial state ────────────────────────────────────────────────
    initial_state = AgentState(
        run_id               = run_id,
        run_date             = run_date,
        raw_measurements     = {},
        fetch_errors         = [],
        sensor_ids           = {},
        clean_measurements   = {},
        validation_warnings  = [],
        city_aqi             = {},
        anomaly_flags        = {},
        anomaly_details      = [],
        anomaly_summary      = "",
        weather_data         = {},
        pm25_correlation     = None,
        alert_level          = "",
        critical_cities      = [],
        warning_cities       = [],
        run_duration_seconds = 0.0,
        node_timings         = {},
        langfuse_trace_url   = dashboard_url,
    )

    # ── Run the graph ──────────────────────────────────────────────────────
    t0  = time.time()
    app = build_graph()
    try:
        invoke_config = {"run_name": f"aq-agent-{run_date}"}
        if lf_handler:
            invoke_config["callbacks"] = [lf_handler]

        result = app.invoke(initial_state, config=invoke_config)
    except Exception as e:
        log.error(f"Agent graph failed: {e}")
        raise

    result["run_duration_seconds"] = round(time.time() - t0, 2)
    result["langfuse_trace_url"]   = dashboard_url
    return result
