FROM apache/airflow:2.8.4-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-venv \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/pipeline_venv
COPY services/backend/requirements.txt /opt/airflow/requirements-backend.txt
RUN PIP_USER=0 /opt/pipeline_venv/bin/pip install --no-cache-dir -r /opt/airflow/requirements-backend.txt

USER airflow
