"""
Vendor Location Sync DAG
Monitors vendor location updates and alerts for stale GPS data.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.email import EmailOperator
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'athena',
    'depends_on_past': False,
    'email': ['operations@athena.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def check_stale_locations(**context):
    """Check for in-progress charters with stale GPS data."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Find in-progress charters without recent location updates
    sql = """
        SELECT 
            c.id,
            v.name as vehicle_name,
            u.full_name as vendor_name,
            u.email as vendor_email,
            c.last_checkin_time,
            EXTRACT(EPOCH FROM (NOW() - c.last_checkin_time))/60 as minutes_stale
        FROM charters c
        JOIN vehicles v ON c.vehicle_id = v.id
        LEFT JOIN users u ON c.vendor_id = u.id
        WHERE c.status = 'in_progress'
        AND (
            c.last_checkin_time IS NULL 
            OR c.last_checkin_time < NOW() - INTERVAL '30 minutes'
        )
        ORDER BY c.last_checkin_time ASC NULLS FIRST
    """
    
    stale_charters = pg_hook.get_records(sql)
    
    if stale_charters:
        logger.warning(f"Found {len(stale_charters)} charters with stale location data")
        
        # Push to XCom for email notification
        alert_data = []
        for charter in stale_charters:
            alert_data.append({
                'charter_id': charter[0],
                'vehicle': charter[1],
                'vendor': charter[2],
                'vendor_email': charter[3],
                'last_checkin': str(charter[4]) if charter[4] else 'Never',
                'minutes_stale': int(charter[5]) if charter[5] else 'N/A'
            })
        
        context['task_instance'].xcom_push(key='stale_charters', value=alert_data)
        return alert_data
    else:
        logger.info("All in-progress charters have recent location updates")
        return []

def send_vendor_reminders(**context):
    """Send reminders to vendors with stale location data."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    stale_charters = context['task_instance'].xcom_pull(
        task_ids='check_stale_locations',
        key='stale_charters'
    )
    
    if not stale_charters:
        logger.info("No reminders to send")
        return
    
    # In production, this would send emails/SMS to vendors
    for charter in stale_charters:
        logger.info(
            f"Would send reminder to {charter['vendor']} ({charter['vendor_email']}) "
            f"for Charter #{charter['charter_id']}"
        )
    
    # Update charter notes with reminder timestamp
    for charter in stale_charters:
        sql = """
            UPDATE charters 
            SET vendor_notes = COALESCE(vendor_notes || E'\n', '') || %s
            WHERE id = %s
        """
        note = f"[{datetime.now()}] Auto-reminder sent: Please update GPS location"
        pg_hook.run(sql, parameters=(note, charter['charter_id']))

def generate_location_heatmap(**context):
    """Generate location heatmap data for active charters."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    sql = """
        SELECT 
            c.id,
            c.last_checkin_location,
            c.last_checkin_time,
            v.name as vehicle_name,
            CAST(SPLIT_PART(c.last_checkin_location, ',', 1) AS FLOAT) as latitude,
            CAST(TRIM(SPLIT_PART(c.last_checkin_location, ',', 2)) AS FLOAT) as longitude
        FROM charters c
        JOIN vehicles v ON c.vehicle_id = v.id
        WHERE c.status = 'in_progress'
        AND c.last_checkin_location IS NOT NULL
        AND c.last_checkin_location ~ '^-?[0-9]+\\.?[0-9]*, -?[0-9]+\\.?[0-9]*$'
    """
    
    locations = pg_hook.get_records(sql)
    
    logger.info(f"Found {len(locations)} active charter locations for heatmap")
    
    # Push to XCom for downstream processing or visualization
    location_data = [
        {
            'charter_id': loc[0],
            'location': loc[1],
            'timestamp': str(loc[2]),
            'vehicle': loc[3],
            'lat': float(loc[4]),
            'lon': float(loc[5])
        }
        for loc in locations
    ]
    
    context['task_instance'].xcom_push(key='location_data', value=location_data)
    return location_data

# Define the DAG
with DAG(
    'vendor_location_sync',
    default_args=default_args,
    description='Monitor and sync vendor GPS locations',
    schedule_interval='*/15 * * * *',  # Every 15 minutes
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=['monitoring', 'gps', 'vendors'],
) as dag:

    check_locations = PythonOperator(
        task_id='check_stale_locations',
        python_callable=check_stale_locations,
        provide_context=True,
    )

    send_reminders = PythonOperator(
        task_id='send_vendor_reminders',
        python_callable=send_vendor_reminders,
        provide_context=True,
    )

    generate_heatmap = PythonOperator(
        task_id='generate_location_heatmap',
        python_callable=generate_location_heatmap,
        provide_context=True,
    )

    # Task dependencies
    check_locations >> [send_reminders, generate_heatmap]
