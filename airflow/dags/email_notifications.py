"""
Email Notification DAG
Sends charter confirmations, reminders, and follow-ups.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'athena',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

def send_charter_confirmations(**context):
    """Send confirmation emails for newly booked charters."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Find charters confirmed in last 24 hours that haven't been emailed
    sql = """
        SELECT c.id, c.pickup_date, c.total_cost, cl.name, cl.email,
               v.vehicle_type, c.passenger_count
        FROM charters c
        JOIN clients cl ON c.client_id = cl.id
        JOIN vehicles v ON c.vehicle_id = v.id
        WHERE c.status = 'confirmed'
        AND c.created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        AND NOT EXISTS (
            SELECT 1 FROM email_log 
            WHERE charter_id = c.id AND email_type = 'confirmation'
        )
        LIMIT 50
    """
    
    charters = pg_hook.get_records(sql)
    logger.info(f"Sending confirmation emails for {len(charters)} charters")
    
    for charter_id, pickup_date, total_cost, client_name, email, vehicle_type, passenger_count in charters:
        # In real implementation, use email service API
        logger.info(f"Sending confirmation to {email} for charter {charter_id}")
        
        # Log email sent
        log_sql = """
            INSERT INTO email_log (charter_id, email_type, sent_to, sent_at)
            VALUES (%s, 'confirmation', %s, CURRENT_TIMESTAMP)
        """
        pg_hook.run(log_sql, parameters=(charter_id, email))
    
    return len(charters)

def send_upcoming_reminders(**context):
    """Send reminders for charters happening tomorrow."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    sql = """
        SELECT c.id, c.pickup_date, c.pickup_location, cl.name, cl.email,
               v.vehicle_type, c.passenger_count
        FROM charters c
        JOIN clients cl ON c.client_id = cl.id
        JOIN vehicles v ON c.vehicle_id = v.id
        WHERE c.status = 'confirmed'
        AND c.pickup_date::date = CURRENT_DATE + INTERVAL '1 day'
        AND NOT EXISTS (
            SELECT 1 FROM email_log 
            WHERE charter_id = c.id 
            AND email_type = 'reminder'
            AND sent_at > CURRENT_DATE
        )
        LIMIT 100
    """
    
    charters = pg_hook.get_records(sql)
    logger.info(f"Sending reminders for {len(charters)} charters happening tomorrow")
    
    for charter_id, pickup_date, pickup_location, client_name, email, vehicle_type, passenger_count in charters:
        logger.info(f"Sending reminder to {email} for charter {charter_id}")
        
        log_sql = """
            INSERT INTO email_log (charter_id, email_type, sent_to, sent_at)
            VALUES (%s, 'reminder', %s, CURRENT_TIMESTAMP)
        """
        pg_hook.run(log_sql, parameters=(charter_id, email))
    
    return len(charters)

def send_followup_surveys(**context):
    """Send follow-up surveys for completed charters."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Send survey 1 day after charter completion
    sql = """
        SELECT c.id, cl.name, cl.email, c.dropoff_date
        FROM charters c
        JOIN clients cl ON c.client_id = cl.id
        WHERE c.status = 'completed'
        AND c.dropoff_date::date = CURRENT_DATE - INTERVAL '1 day'
        AND NOT EXISTS (
            SELECT 1 FROM email_log 
            WHERE charter_id = c.id AND email_type = 'survey'
        )
        LIMIT 50
    """
    
    charters = pg_hook.get_records(sql)
    logger.info(f"Sending surveys for {len(charters)} completed charters")
    
    for charter_id, client_name, email, dropoff_date in charters:
        logger.info(f"Sending survey to {email} for charter {charter_id}")
        
        log_sql = """
            INSERT INTO email_log (charter_id, email_type, sent_to, sent_at)
            VALUES (%s, 'survey', %s, CURRENT_TIMESTAMP)
        """
        pg_hook.run(log_sql, parameters=(charter_id, email))
    
    return len(charters)

# Create DAG
with DAG(
    'email_notifications',
    default_args=default_args,
    description='Send charter-related email notifications',
    schedule_interval='0 * * * *',  # Run every hour
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['email', 'notifications'],
) as dag:
    
    confirmations = PythonOperator(
        task_id='send_charter_confirmations',
        python_callable=send_charter_confirmations,
    )
    
    reminders = PythonOperator(
        task_id='send_upcoming_reminders',
        python_callable=send_upcoming_reminders,
    )
    
    surveys = PythonOperator(
        task_id='send_followup_surveys',
        python_callable=send_followup_surveys,
    )
    
    # Tasks run independently
    [confirmations, reminders, surveys]
