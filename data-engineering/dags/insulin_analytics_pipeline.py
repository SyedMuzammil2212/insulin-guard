from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG('insulin_analytics_pipeline',start_date=datetime(2025,1,1),schedule='@daily',catchup=False,max_active_runs=1,default_args={'retries':2,'retry_delay':timedelta(minutes=5)},tags=['analytics']) as dag:
    run_pipeline = BashOperator(task_id='extract_validate_transform_load',bash_command='cd /opt/insulin-pipeline && /opt/pipeline-venv/bin/python pipeline.py')
