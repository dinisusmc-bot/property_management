"""
Payment Processing DAG
Runs daily to process pending payments, capture deposits, and charge final balances.
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
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def process_deposit_payments(**context):
    """Process deposit payments for confirmed charters."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Find charters with confirmed status that need deposit payment
    sql = """
        SELECT id, client_id, deposit_amount, total_cost
        FROM charters
        WHERE status = 'confirmed' 
        AND payment_status = 'pending'
        AND deposit_amount > 0
        AND pickup_date > CURRENT_DATE
        LIMIT 100
    """
    
    charters = pg_hook.get_records(sql)
    logger.info(f"Found {len(charters)} charters requiring deposit payment")
    
    for charter_id, client_id, deposit_amount, total_cost in charters:
        try:
            # In real implementation, integrate with payment processor
            # For now, just update payment status
            update_sql = """
                UPDATE charters
                SET payment_status = 'deposit_paid',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            pg_hook.run(update_sql, parameters=(charter_id,))
            logger.info(f"Processed deposit for charter {charter_id}: ${deposit_amount}")
            
        except Exception as e:
            logger.error(f"Failed to process deposit for charter {charter_id}: {str(e)}")
            continue
    
    return len(charters)

def process_final_payments(**context):
    """Process final payments for charters happening within 48 hours."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Find charters happening soon that need final payment
    sql = """
        SELECT id, client_id, balance_due, total_cost
        FROM charters
        WHERE status IN ('confirmed', 'in_progress')
        AND payment_status = 'deposit_paid'
        AND balance_due > 0
        AND pickup_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '2 days'
        LIMIT 100
    """
    
    charters = pg_hook.get_records(sql)
    logger.info(f"Found {len(charters)} charters requiring final payment")
    
    for charter_id, client_id, balance_due, total_cost in charters:
        try:
            # In real implementation, charge balance to payment method on file
            update_sql = """
                UPDATE charters
                SET payment_status = 'paid',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            pg_hook.run(update_sql, parameters=(charter_id,))
            logger.info(f"Processed final payment for charter {charter_id}: ${balance_due}")
            
        except Exception as e:
            logger.error(f"Failed to process final payment for charter {charter_id}: {str(e)}")
            continue
    
    return len(charters)

def send_payment_reminders(**context):
    """Send payment reminders for overdue balances."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    sql = """
        SELECT c.id, c.client_id, c.balance_due, cl.email, cl.name
        FROM charters c
        JOIN clients cl ON c.client_id = cl.id
        WHERE c.payment_status IN ('pending', 'deposit_paid')
        AND c.balance_due > 0
        AND c.pickup_date < CURRENT_DATE + INTERVAL '7 days'
        AND c.pickup_date > CURRENT_DATE
    """
    
    charters = pg_hook.get_records(sql)
    logger.info(f"Sending payment reminders for {len(charters)} charters")
    
    for charter_id, client_id, balance_due, email, client_name in charters:
        # In real implementation, send email via email service
        logger.info(f"Would send payment reminder to {email} for charter {charter_id}")
    
    return len(charters)

# Create DAG
with DAG(
    'payment_processing',
    default_args=default_args,
    description='Process charter payments daily',
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['payments', 'daily'],
) as dag:
    
    process_deposits = PythonOperator(
        task_id='process_deposit_payments',
        python_callable=process_deposit_payments,
    )
    
    process_finals = PythonOperator(
        task_id='process_final_payments',
        python_callable=process_final_payments,
    )
    
    send_reminders = PythonOperator(
        task_id='send_payment_reminders',
        python_callable=send_payment_reminders,
    )
    
    # Set task dependencies
    process_deposits >> process_finals >> send_reminders
