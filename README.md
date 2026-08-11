# Autonomous Air Quality Monitoring Agent

## Project Description
The Autonomous Air Quality Monitoring Agent is a data-driven agentic pipeline designed to monitor, validate, analyze, and alert on air quality index (AQI) data across major Indian cities. It integrates real-time air quality data from OpenAQ, historical weather data from Open-Meteo, and utilizes LangGraph to orchestrate the workflow.

## Why Agentic AI (LangGraph)?
1. **Orchestration & State Management**: LangGraph provides robust state management across various analytical nodes.
2. **Modularity**: Individual steps (fetching, validation, ML anomaly detection) are decoupled into discrete nodes, making the system easy to maintain.
3. **Observability**: Seamless integration with LangFuse enables tracking node execution times, overall agent health, and detailed trace history.
4. **Resilience**: The graph architecture enables elegant error handling and graceful degradation during network failures or API rate limits.

## Architecture Diagram
```
START → fetch_data → validate → detect_anomalies → correlate_weather → route_alert → END
```

## Setup Instructions

1. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

2. **Install Dependencies**:
   Install the necessary packages into the shared virtual environment:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit Dashboard**:
   ```bash
   streamlit run app.py
   ```

4. **Run via CLI or Scheduler**:
   ```bash
   python scripts/run_agent.py
   python scripts/scheduler.py
   ```

## Tech Stack
| Component | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| Dashboard | Streamlit, Folium, Plotly |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-Learn (IsolationForest) |
| Observability | LangFuse |
| Job Scheduling | APScheduler |

## Observability with LangFuse
The pipeline uses LangFuse's `@observe` decorator to monitor the duration and success of each step in the graph. You can access all traces via the LangFuse dashboard at your configured `LANGFUSE_HOST`.

## Sample Outputs
*Sample outputs will be generated upon running the pipeline and viewable in the dashboard.*
