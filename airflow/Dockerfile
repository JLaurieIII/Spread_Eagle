FROM apache/airflow:2.8.1-python3.11

# Install your project's Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install dbt
RUN pip install --no-cache-dir dbt-postgres==1.7.4
