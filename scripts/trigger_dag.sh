#!/bin/sh
set -e

docker compose exec airflow airflow dags trigger news_pipeline_daily_4x
