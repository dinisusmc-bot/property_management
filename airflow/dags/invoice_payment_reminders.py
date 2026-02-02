"""
Automated Invoice and Payment Reminder Emails
Sends invoices and payment reminders on schedule
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import psycopg2
import requests
import os

default_args = {
    'owner': 'athena',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'invoice_payment_reminders',
    default_args=default_args,
    description='Send invoices and payment reminders automatically',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['finance', 'invoicing', 'payments']
)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://athena-notifications:8000')

def send_notification(notification_data):
    """Send notification via notification service"""
    try:
        response = requests.post(
            f'{NOTIFICATION_SERVICE_URL}/notifications',
            json=notification_data,
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False

def send_overdue_invoice_reminders(**context):
    """Send reminders for overdue invoices"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Find overdue invoices that haven't been paid
    cur.execute("""
        SELECT 
            i.id, i.invoice_number, i.charter_id, i.total_amount, 
            i.balance_due, i.due_date, i.last_sent_date,
            c.client_id, cl.name as client_name, cl.email as client_email
        FROM invoices i
        JOIN charters c ON i.charter_id = c.id
        JOIN clients cl ON c.client_id = cl.id
        WHERE i.status IN ('sent', 'overdue')
        AND i.balance_due > 0
        AND i.due_date < CURRENT_DATE
        AND (i.last_sent_date IS NULL OR i.last_sent_date < CURRENT_DATE - INTERVAL '3 days')
        ORDER BY i.due_date ASC
    """)
    
    overdue_invoices = cur.fetchall()
    sent_count = 0
    
    for invoice in overdue_invoices:
        invoice_id, invoice_num, charter_id, total, balance, due_date, last_sent, client_id, client_name, client_email = invoice
        
        days_overdue = (datetime.now().date() - due_date).days
        
        notification_data = {
            "recipient_email": client_email,
            "recipient_name": client_name,
            "notification_type": "email",
            "template_name": "overdue_invoice_reminder",
            "priority": "high",
            "charter_id": charter_id,
            "template_data": {
                "client_name": client_name,
                "invoice_number": invoice_num,
                "total_amount": f"${total:.2f}",
                "balance_due": f"${balance:.2f}",
                "due_date": due_date.strftime("%B %d, %Y"),
                "days_overdue": days_overdue
            }
        }
        
        if send_notification(notification_data):
            # Update last sent date and count
            cur.execute("""
                UPDATE invoices 
                SET last_sent_date = NOW(), 
                    sent_count = sent_count + 1,
                    status = 'overdue'
                WHERE id = %s
            """, (invoice_id,))
            
            # Log email
            cur.execute("""
                INSERT INTO email_logs (invoice_id, charter_id, email_type, recipient_email, recipient_name, subject, status)
                VALUES (%s, %s, 'reminder', %s, %s, %s, 'sent')
            """, (invoice_id, charter_id, client_email, client_name, f"Payment Overdue: Invoice {invoice_num}"))
            
            sent_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Sent {sent_count} overdue invoice reminders")
    return sent_count

def send_upcoming_payment_reminders(**context):
    """Send reminders for upcoming payments"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Find payment schedules due in the next 3 days
    cur.execute("""
        SELECT 
            ps.id, ps.charter_id, ps.payment_type, ps.amount_due, ps.due_date,
            c.client_id, cl.name as client_name, cl.email as client_email,
            ch.invoice_number
        FROM payment_schedules ps
        JOIN charters ch ON ps.charter_id = ch.id
        JOIN clients c ON c.id = ch.client_id
        JOIN clients cl ON cl.id = c.id
        WHERE ps.status = 'pending'
        AND ps.due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days'
        AND (ps.last_reminder_sent IS NULL OR ps.last_reminder_sent < CURRENT_DATE - INTERVAL '1 day')
        ORDER BY ps.due_date ASC
    """)
    
    upcoming_payments = cur.fetchall()
    sent_count = 0
    
    for payment in upcoming_payments:
        schedule_id, charter_id, payment_type, amount, due_date, client_id, client_name, client_email, invoice_num = payment
        
        days_until_due = (due_date - datetime.now().date()).days
        
        notification_data = {
            "recipient_email": client_email,
            "recipient_name": client_name,
            "notification_type": "email",
            "template_name": "upcoming_payment_reminder",
            "priority": "medium",
            "charter_id": charter_id,
            "template_data": {
                "client_name": client_name,
                "payment_type": payment_type.replace("_", " ").title(),
                "amount_due": f"${amount:.2f}",
                "due_date": due_date.strftime("%B %d, %Y"),
                "days_until_due": days_until_due,
                "invoice_number": invoice_num or "N/A"
            }
        }
        
        if send_notification(notification_data):
            # Update reminder tracking
            cur.execute("""
                UPDATE payment_schedules 
                SET last_reminder_sent = NOW(),
                    reminder_sent_count = reminder_sent_count + 1,
                    next_reminder_date = CASE 
                        WHEN due_date - CURRENT_DATE <= 1 THEN NULL
                        ELSE CURRENT_DATE + INTERVAL '1 day'
                    END
                WHERE id = %s
            """, (schedule_id,))
            
            # Log email
            cur.execute("""
                INSERT INTO email_logs (charter_id, email_type, recipient_email, recipient_name, subject, status)
                VALUES (%s, 'reminder', %s, %s, %s, 'sent')
            """, (charter_id, client_email, client_name, f"Payment Reminder: {payment_type} due {due_date.strftime('%m/%d/%Y')}"))
            
            sent_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Sent {sent_count} upcoming payment reminders")
    return sent_count

def send_new_invoices(**context):
    """Send newly created invoices that haven't been sent yet"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Find draft invoices ready to send
    cur.execute("""
        SELECT 
            i.id, i.invoice_number, i.charter_id, i.total_amount, i.due_date,
            c.client_id, cl.name as client_name, cl.email as client_email
        FROM invoices i
        JOIN charters c ON i.charter_id = c.id  
        JOIN clients cl ON c.client_id = cl.id
        WHERE i.status = 'draft'
        AND i.invoice_date <= CURRENT_DATE
        ORDER BY i.created_at ASC
    """)
    
    new_invoices = cur.fetchall()
    sent_count = 0
    
    for invoice in new_invoices:
        invoice_id, invoice_num, charter_id, total, due_date, client_id, client_name, client_email = invoice
        
        notification_data = {
            "recipient_email": client_email,
            "recipient_name": client_name,
            "notification_type": "email",
            "template_name": "invoice_notification",
            "priority": "high",
            "charter_id": charter_id,
            "template_data": {
                "client_name": client_name,
                "invoice_number": invoice_num,
                "total_amount": f"${total:.2f}",
                "due_date": due_date.strftime("%B %d, %Y")
            }
        }
        
        if send_notification(notification_data):
            # Update invoice status
            cur.execute("""
                UPDATE invoices 
                SET status = 'sent',
                    last_sent_date = NOW(),
                    sent_count = 1
                WHERE id = %s
            """, (invoice_id,))
            
            # Log email
            cur.execute("""
                INSERT INTO email_logs (invoice_id, charter_id, email_type, recipient_email, recipient_name, subject, status)
                VALUES (%s, %s, 'invoice', %s, %s, %s, 'sent')
            """, (invoice_id, charter_id, client_email, client_name, f"Invoice {invoice_num}"))
            
            sent_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Sent {sent_count} new invoices")
    return sent_count

# Task definitions
send_overdue_task = PythonOperator(
    task_id='send_overdue_invoice_reminders',
    python_callable=send_overdue_invoice_reminders,
    dag=dag,
)

send_upcoming_task = PythonOperator(
    task_id='send_upcoming_payment_reminders',
    python_callable=send_upcoming_payment_reminders,
    dag=dag,
)

send_new_invoices_task = PythonOperator(
    task_id='send_new_invoices',
    python_callable=send_new_invoices,
    dag=dag,
)

# Task dependencies - all can run in parallel
send_new_invoices_task
send_upcoming_task
send_overdue_task
