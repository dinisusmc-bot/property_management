"""
Invoice Generation DAG
Automatically generates monthly invoices for clients.
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
    'retry_delay': timedelta(minutes=5),
}

def generate_monthly_invoices(**context):
    """Generate invoices for completed charters from last month."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Get first and last day of previous month
    today = datetime.now()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    
    # Find completed charters from last month that haven't been invoiced
    sql = """
        SELECT 
            c.id, c.client_id, c.total_cost, c.deposit_amount, c.balance_due,
            cl.name, cl.email, cl.billing_address
        FROM charters c
        JOIN clients cl ON c.client_id = cl.id
        WHERE c.status = 'completed'
        AND c.dropoff_date >= %s
        AND c.dropoff_date < %s
        AND NOT EXISTS (
            SELECT 1 FROM invoices WHERE charter_id = c.id
        )
        ORDER BY cl.id, c.dropoff_date
    """
    
    charters = pg_hook.get_records(sql, parameters=(first_day_last_month, first_day_this_month))
    logger.info(f"Generating invoices for {len(charters)} completed charters")
    
    # Group by client
    client_charters = {}
    for row in charters:
        charter_id, client_id, total_cost, deposit, balance, name, email, address = row
        if client_id not in client_charters:
            client_charters[client_id] = {
                'client_name': name,
                'email': email,
                'address': address,
                'charters': []
            }
        client_charters[client_id]['charters'].append({
            'id': charter_id,
            'total_cost': float(total_cost),
            'deposit': float(deposit),
            'balance': float(balance)
        })
    
    # Generate invoice for each client
    invoice_count = 0
    for client_id, data in client_charters.items():
        total_amount = sum(c['total_cost'] for c in data['charters'])
        
        # Create invoice record
        insert_sql = """
            INSERT INTO invoices (
                client_id, invoice_date, due_date, total_amount, 
                status, created_at
            ) VALUES (%s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP)
            RETURNING id
        """
        invoice_date = last_day_last_month
        due_date = invoice_date + timedelta(days=30)
        
        invoice_id = pg_hook.get_first(
            insert_sql, 
            parameters=(client_id, invoice_date, due_date, total_amount)
        )[0]
        
        # Link charters to invoice
        for charter in data['charters']:
            link_sql = "UPDATE charters SET invoice_id = %s WHERE id = %s"
            pg_hook.run(link_sql, parameters=(invoice_id, charter['id']))
        
        logger.info(f"Created invoice {invoice_id} for client {client_id}: ${total_amount}")
        invoice_count += 1
        
        # In real implementation, generate PDF and email to client
    
    return invoice_count

def send_invoice_emails(**context):
    """Send invoice emails to clients."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Find invoices created today that haven't been emailed
    sql = """
        SELECT i.id, i.total_amount, i.due_date, c.name, c.email
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        WHERE i.created_at::date = CURRENT_DATE
        AND NOT EXISTS (
            SELECT 1 FROM email_log WHERE invoice_id = i.id
        )
    """
    
    invoices = pg_hook.get_records(sql)
    logger.info(f"Sending {len(invoices)} invoice emails")
    
    for invoice_id, amount, due_date, client_name, email in invoices:
        # In real implementation, attach PDF and send via email service
        logger.info(f"Sending invoice {invoice_id} to {email} for ${amount}")
        
        # Log email sent
        log_sql = """
            INSERT INTO email_log (invoice_id, email_type, sent_to, sent_at)
            VALUES (%s, 'invoice', %s, CURRENT_TIMESTAMP)
        """
        pg_hook.run(log_sql, parameters=(invoice_id, email))
    
    return len(invoices)

# Create DAG
with DAG(
    'invoice_generation',
    default_args=default_args,
    description='Generate monthly invoices for clients',
    schedule_interval='0 9 1 * *',  # Run at 9 AM on 1st of each month
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['invoices', 'monthly'],
) as dag:
    
    generate_invoices = PythonOperator(
        task_id='generate_monthly_invoices',
        python_callable=generate_monthly_invoices,
    )
    
    send_emails = PythonOperator(
        task_id='send_invoice_emails',
        python_callable=send_invoice_emails,
    )
    
    generate_invoices >> send_emails
