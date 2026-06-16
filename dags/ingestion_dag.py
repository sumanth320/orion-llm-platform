from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

# Define default execution properties for our pipeline tasks
default_args = {
    'owner': 'orion_data_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Instantiate our workflow graph
with DAG(
    dag_id='orion_news_ingestion_pipeline',
    default_args=default_args,
    description='Orchestrates the local containerized Finnhub ingestion and Qdrant vectorization sync',
    schedule_interval='@daily',  # Runs automatically once every day
    catchup=False,
    is_paused_upon_creation=False,
    tags=['ingestion', 'rag', 'qdrant'],
) as dag:

    # Define the isolated container execution task
    # Define the isolated container execution task
    run_ingestion_container = DockerOperator(
        task_id='execute_vector_ingestion',
        image='orion-ingestion:v1',
        api_version='auto',
        auto_remove=True,
        force_pull=False,
        command='python ingestion/ingestion_pipeline.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='orion-llm-platform_orion-fabric-net',
        environment={
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
            'QDRANT_HOST': 'qdrant',
            'QDRANT_PORT': '6333',
            'EMBED_BATCH_SIZE': '4',
            'FASTEMBED_MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'FASTEMBED_CACHE_DIR': '/app/.cache/fastembed',
            'HF_HUB_DOWNLOAD_TIMEOUT': '120',
            'HF_HUB_ETAG_TIMEOUT': '60',
            'OMP_NUM_THREADS': '1',
            'MKL_NUM_THREADS': '1',
            'TARGET_TICKER': "{{ dag_run.conf.get('ticker', 'NVDA') }}"
        },
        mount_tmp_dir=False,
        mem_limit=os.getenv('INGESTION_MEM_LIMIT', '4g'),
    )