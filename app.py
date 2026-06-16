import streamlit as st
import requests
import os
from retrieval.search_engine import execute_hybrid_reranked_search

st.set_page_config(page_title="Orion Search Engine", page_icon="🔭", layout="wide")

st.title("🔭 Orion LLM Platform: Automated Control Center")

# Configuration for Airflow communication mesh

# Force an explicit IPv4 address target loopback routing path
AIRFLOW_URL = "http://127.0.0.1:8080/api/v1/dags/orion_news_ingestion_pipeline/dagRuns"
AIRFLOW_DAG_URL = "http://127.0.0.1:8080/api/v1/dags/orion_news_ingestion_pipeline"
# Standard default credentials matching your persistent stack layout configuration
AIRFLOW_AUTH = ("admin", "admin")

# 1. Sidebar Panel for Controls
st.sidebar.header("Data Management Center")
selected_ticker = st.sidebar.text_input("Stock Ticker Symbol", value="NVDA").upper().strip()

st.sidebar.subheader("Pipeline Actions")
if st.sidebar.button(f"▶ Run Ingestion Pipeline for {selected_ticker}"):
    with st.sidebar.spinner(f"Spawning Airflow worker for {selected_ticker}..."):
        try:
            request_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Content-Type": "application/json"
            }

            # Step 1: Ensure the DAG is unpaused before triggering
            requests.patch(
                AIRFLOW_DAG_URL,
                json={"is_paused": False},
                auth=AIRFLOW_AUTH,
                headers=request_headers,
                timeout=10
            )

            # Step 2: Trigger the DAG run
            payload = {"conf": {"ticker": selected_ticker}}

            response = requests.post(
                AIRFLOW_URL,
                json=payload,
                auth=AIRFLOW_AUTH,
                headers=request_headers,
                timeout=10
            )

            if response.status_code in (200, 201):
                run_data = response.json()
                state = run_data.get("state", "queued")
                run_id = run_data.get("dag_run_id", "")
                st.sidebar.success(f"Pipeline kicked off for **{selected_ticker}** — state: `{state}`")
                st.sidebar.caption(f"Run ID: `{run_id}`")
                st.sidebar.info("Monitor progress in the Airflow Web UI at http://localhost:8080")
            else:
                st.sidebar.error(f"Airflow rejection: {response.status_code} - {response.text}")
        except Exception as e:
            st.sidebar.error(f"Failed to communicate with orchestrator service: {e}")

st.sidebar.markdown("---")
st.sidebar.header("Retrieval Tuners")
candidate_pool = st.sidebar.slider("Vector Candidate Search Range (Top-K)", 5, 50, 20)

# 2. Main Retrieval Screen Area
user_query = st.text_input(
    f"Enter your analysis question concerning {selected_ticker}:",
    placeholder=f"What are the major growth factors or bottlenecks facing {selected_ticker}?"
)

if user_query:
    with st.spinner("Calculating hybrid weights and processing cross-attention loops..."):
        # Match against whatever string is currently resting inside the UI input field
        filters = {"ticker": selected_ticker}
        vetted_results = execute_hybrid_reranked_search(
            query_text=user_query,
            metadata_filters=filters,
            candidate_limit=candidate_pool,
            final_top_k=5
        )

    if not vetted_results:
        st.warning(f"No indexed metrics found in Qdrant database matching ticker symbol: {selected_ticker}")
    else:
        st.subheader(f"Top Vetted Market Intelligence for {selected_ticker}")

        for rank, point in enumerate(vetted_results, 1):
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.metric(label=f"Relevance Rank {rank}", value=f"{point.score:.4f}")
                    st.caption(f"Source: {point.payload.get('source', 'Unknown')}")
                with col2:
                    st.markdown(f"### {point.payload.get('headline')}")
                    st.write(point.payload.get('summary'))
                    if point.payload.get('url'):
                        st.markdown(f"[Read Article Source]({point.payload.get('url')})")
                st.markdown("---")