from datetime import datetime

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

SEOUL_TZ = pendulum.timezone("Asia/Seoul")
PIPELINE_PYTHON = "/opt/pipeline_venv/bin/python"
PIPELINE_CLI = "/opt/project/services/backend/app/pipeline/cli.py"


def pipeline_cmd(task_name: str) -> str:
    return f"PYTHONPATH=/opt/project/services/backend {PIPELINE_PYTHON} {PIPELINE_CLI} {task_name}"

with DAG(
    dag_id="news_pipeline_daily_4x",
    start_date=datetime(2024, 1, 1, tzinfo=SEOUL_TZ),
    schedule="0 0,8,12,18 * * *",
    catchup=False,
    tags=["news", "batch"],
    default_args={"owner": "news-pipeline"},
) as dag:
    t1 = BashOperator(task_id="fetch_articles", bash_command=pipeline_cmd("fetch_articles"))
    t2 = BashOperator(task_id="clean_normalize", bash_command=pipeline_cmd("clean_normalize"))
    t3 = BashOperator(task_id="deduplicate", bash_command=pipeline_cmd("deduplicate"))
    t4 = BashOperator(task_id="extract_keywords", bash_command=pipeline_cmd("extract_keywords"))
    t5 = BashOperator(task_id="assign_topics", bash_command=pipeline_cmd("assign_topics"))
    t6 = BashOperator(task_id="generate_newsletters", bash_command=pipeline_cmd("generate_newsletters"))
    t7 = BashOperator(task_id="embed_newsletters", bash_command=pipeline_cmd("embed_newsletters"))
    t8 = BashOperator(task_id="update_popularity", bash_command=pipeline_cmd("update_popularity"))

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7 >> t8
