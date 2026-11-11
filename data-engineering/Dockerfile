FROM apache/airflow:2.10.5-python3.12
USER root
RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless && apt-get clean && rm -rf /var/lib/apt/lists/* && python -m venv /opt/pipeline-venv && chown -R airflow:root /opt/pipeline-venv
USER airflow
COPY requirements.txt /tmp/pipeline-requirements.txt
RUN /opt/pipeline-venv/bin/pip install --no-cache-dir -r /tmp/pipeline-requirements.txt
COPY --chown=airflow:root . /opt/insulin-pipeline
