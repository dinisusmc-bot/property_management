"""
Daily Reports DAG
Generates and sends daily business summary reports.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging
import json

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'athena',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def generate_daily_summary(**context):
    """Generate daily summary statistics."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Get key metrics for yesterday
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    metrics = {}
    
    # New charters created
    sql = "SELECT COUNT(*) FROM charters WHERE created_at::date = %s"
    metrics['new_charters'] = pg_hook.get_first(sql, parameters=(yesterday,))[0]
    
    # Revenue booked
    sql = "SELECT COALESCE(SUM(total_cost), 0) FROM charters WHERE created_at::date = %s"
    metrics['revenue_booked'] = float(pg_hook.get_first(sql, parameters=(yesterday,))[0])
    
    # Charters completed
    sql = "SELECT COUNT(*) FROM charters WHERE status = 'completed' AND dropoff_date::date = %s"
    metrics['charters_completed'] = pg_hook.get_first(sql, parameters=(yesterday,))[0]
    
    # New clients
    sql = "SELECT COUNT(*) FROM clients WHERE created_at::date = %s"
    metrics['new_clients'] = pg_hook.get_first(sql, parameters=(yesterday,))[0]
    
    # Active charters today
    sql = "SELECT COUNT(*) FROM charters WHERE status = 'in_progress' AND pickup_date::date = CURRENT_DATE"
    metrics['active_charters'] = pg_hook.get_first(sql)[0]
    
    # Upcoming charters (next 7 days)
    sql = """
        SELECT COUNT(*) FROM charters 
        WHERE status = 'confirmed' 
        AND pickup_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
    """
    metrics['upcoming_charters'] = pg_hook.get_first(sql)[0]
    
    logger.info(f"Daily metrics: {json.dumps(metrics, indent=2)}")
    
    # Store metrics
    context['ti'].xcom_push(key='daily_metrics', value=metrics)
    return metrics

def generate_financial_summary(**context):
    """Generate financial summary for yesterday."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    financial = {}
    
    # Total revenue
    sql = """
        SELECT 
            COALESCE(SUM(total_cost), 0) as total_revenue,
            COALESCE(SUM(deposit_amount), 0) as deposits_collected,
            COALESCE(SUM(balance_due), 0) as balance_outstanding
        FROM charters
        WHERE created_at::date = %s
    """
    result = pg_hook.get_first(sql, parameters=(yesterday,))
    financial['total_revenue'] = float(result[0])
    financial['deposits_collected'] = float(result[1])
    financial['balance_outstanding'] = float(result[2])
    
    # Payment status breakdown
    sql = """
        SELECT payment_status, COUNT(*), SUM(total_cost)
        FROM charters
        WHERE created_at::date = %s
        GROUP BY payment_status
    """
    payment_breakdown = {}
    for status, count, total in pg_hook.get_records(sql, parameters=(yesterday,)):
        payment_breakdown[status] = {
            'count': count,
            'amount': float(total)
        }
    financial['payment_breakdown'] = payment_breakdown
    
    logger.info(f"Financial summary: {json.dumps(financial, indent=2)}")
    
    context['ti'].xcom_push(key='financial_summary', value=financial)
    return financial

def generate_operations_summary(**context):
    """Generate operations summary."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    operations = {}
    
    # Vehicle utilization
    sql = """
        SELECT 
            v.vehicle_type,
            COUNT(DISTINCT c.id) as charters_count,
            SUM(c.total_cost) as revenue
        FROM vehicles v
        LEFT JOIN charters c ON v.id = c.vehicle_id 
            AND c.pickup_date::date = CURRENT_DATE - INTERVAL '1 day'
        GROUP BY v.vehicle_type
    """
    vehicle_util = []
    for vehicle_type, count, revenue in pg_hook.get_records(sql):
        vehicle_util.append({
            'type': vehicle_type,
            'charters': count,
            'revenue': float(revenue or 0)
        })
    operations['vehicle_utilization'] = vehicle_util
    
    # Charter status breakdown
    sql = """
        SELECT status, COUNT(*)
        FROM charters
        WHERE pickup_date >= CURRENT_DATE
        GROUP BY status
    """
    status_breakdown = {}
    for status, count in pg_hook.get_records(sql):
        status_breakdown[status] = count
    operations['status_breakdown'] = status_breakdown
    
    logger.info(f"Operations summary: {json.dumps(operations, indent=2)}")
    
    context['ti'].xcom_push(key='operations_summary', value=operations)
    return operations

def send_daily_report(**context):
    """Compile and send daily report email."""
    ti = context['ti']
    
    metrics = ti.xcom_pull(task_ids='generate_daily_summary', key='daily_metrics')
    financial = ti.xcom_pull(task_ids='generate_financial_summary', key='financial_summary')
    operations = ti.xcom_pull(task_ids='generate_operations_summary', key='operations_summary')
    
    report = {
        'date': str((datetime.now() - timedelta(days=1)).date()),
        'metrics': metrics,
        'financial': financial,
        'operations': operations
    }
    
    # In real implementation, format as HTML email and send
    logger.info(f"Daily report:\n{json.dumps(report, indent=2)}")
    
    # Would send email to management here
    logger.info("Daily report would be emailed to management")
    
    return report

# Create DAG
with DAG(
    'daily_reports',
    default_args=default_args,
    description='Generate and send daily business reports',
    schedule_interval='0 8 * * *',  # Run at 8 AM daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['reports', 'daily'],
) as dag:
    
    daily_summary = PythonOperator(
        task_id='generate_daily_summary',
        python_callable=generate_daily_summary,
    )
    
    financial_summary = PythonOperator(
        task_id='generate_financial_summary',
        python_callable=generate_financial_summary,
    )
    
    operations_summary = PythonOperator(
        task_id='generate_operations_summary',
        python_callable=generate_operations_summary,
    )
    
    send_report = PythonOperator(
        task_id='send_daily_report',
        python_callable=send_daily_report,
    )
    
    # All summaries run in parallel, then send report
    [daily_summary, financial_summary, operations_summary] >> send_report
