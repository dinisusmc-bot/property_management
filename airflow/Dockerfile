FROM docker.io/apache/airflow:2.7.3-python3.11

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p /opt/airflow/logs /opt/airflow/plugins && \
    chown -R airflow:root /opt/airflow/logs /opt/airflow/plugins && \
    chmod -R 775 /opt/airflow/logs /opt/airflow/plugins

USER airflow

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt

# Copy DAGs
COPY dags /opt/airflow/dags
