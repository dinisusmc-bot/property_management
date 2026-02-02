"""
Charter Preparation DAG
Automated tasks for preparing upcoming charters.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'athena',
    'depends_on_past': False,
    'email': ['operations@athena.com'],
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def check_tomorrows_charters(**context):
    """Check for charters scheduled for tomorrow."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    
    sql = """
        SELECT 
            c.id,
            c.trip_date,
            c.passengers,
            c.status,
            v.name as vehicle_name,
            v.capacity,
            cl.name as client_name,
            cl.email as client_email,
            u.full_name as vendor_name,
            u.email as vendor_email
        FROM charters c
        JOIN vehicles v ON c.vehicle_id = v.id
        JOIN clients cl ON c.client_id = cl.id
        LEFT JOIN users u ON c.vendor_id = u.id
        WHERE c.trip_date = %s
        ORDER BY c.trip_date
    """
    
    charters = pg_hook.get_records(sql, parameters=(tomorrow,))
    
    if charters:
        logger.info(f"Found {len(charters)} charters scheduled for {tomorrow}")
        
        charter_data = []
        for charter in charters:
            charter_data.append({
                'id': charter[0],
                'trip_date': str(charter[1]),
                'passengers': charter[2],
                'status': charter[3],
                'vehicle': charter[4],
                'capacity': charter[5],
                'client': charter[6],
                'client_email': charter[7],
                'vendor': charter[8],
                'vendor_email': charter[9]
            })
        
        context['task_instance'].xcom_push(key='tomorrows_charters', value=charter_data)
        return 'process_charters'
    else:
        logger.info(f"No charters scheduled for {tomorrow}")
        return 'no_charters'

def check_vehicle_assignments(**context):
    """Verify all charters have vehicles assigned."""
    charters = context['task_instance'].xcom_pull(
        task_ids='check_tomorrows_charters',
        key='tomorrows_charters'
    )
    
    unassigned = []
    capacity_issues = []
    
    for charter in charters:
        if not charter['vehicle']:
            unassigned.append(charter)
        elif charter['passengers'] > charter['capacity']:
            capacity_issues.append(charter)
    
    if unassigned:
        logger.warning(f"{len(unassigned)} charters without vehicle assignments")
        context['task_instance'].xcom_push(key='unassigned_vehicles', value=unassigned)
    
    if capacity_issues:
        logger.warning(f"{len(capacity_issues)} charters exceed vehicle capacity")
        context['task_instance'].xcom_push(key='capacity_issues', value=capacity_issues)
    
    return {
        'total': len(charters),
        'unassigned': len(unassigned),
        'capacity_issues': len(capacity_issues)
    }

def check_vendor_assignments(**context):
    """Verify all charters have vendors assigned."""
    charters = context['task_instance'].xcom_pull(
        task_ids='check_tomorrows_charters',
        key='tomorrows_charters'
    )
    
    unassigned_vendors = [c for c in charters if not c['vendor']]
    
    if unassigned_vendors:
        logger.warning(f"{len(unassigned_vendors)} charters without vendor assignments")
        context['task_instance'].xcom_push(key='unassigned_vendors', value=unassigned_vendors)
    else:
        logger.info("All charters have vendor assignments")
    
    return len(unassigned_vendors)

def send_client_reminders(**context):
    """Send confirmation reminders to clients."""
    charters = context['task_instance'].xcom_pull(
        task_ids='check_tomorrows_charters',
        key='tomorrows_charters'
    )
    
    for charter in charters:
        # In production, send actual emails
        logger.info(
            f"Sending reminder to {charter['client']} ({charter['client_email']}) "
            f"for Charter #{charter['id']} - {charter['passengers']} passengers"
        )
    
    return len(charters)

def send_vendor_notifications(**context):
    """Send trip details to vendors."""
    charters = context['task_instance'].xcom_pull(
        task_ids='check_tomorrows_charters',
        key='tomorrows_charters'
    )
    
    assigned_charters = [c for c in charters if c['vendor']]
    
    for charter in assigned_charters:
        # In production, send actual emails/SMS
        logger.info(
            f"Sending trip details to {charter['vendor']} ({charter['vendor_email']}) "
            f"for Charter #{charter['id']} - Vehicle: {charter['vehicle']}"
        )
    
    return len(assigned_charters)

def prepare_vehicle_checklist(**context):
    """Generate pre-trip vehicle inspection checklist."""
    charters = context['task_instance'].xcom_pull(
        task_ids='check_tomorrows_charters',
        key='tomorrows_charters'
    )
    
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    # Get vehicle IDs from charters
    vehicle_ids = list(set([c['vehicle'] for c in charters if c['vehicle']]))
    
    checklists = []
    for charter in charters:
        checklist = {
            'charter_id': charter['id'],
            'vehicle': charter['vehicle'],
            'items': [
                'Fuel tank full',
                'Tire pressure checked',
                'Brake lights working',
                'Emergency equipment stocked',
                'Interior cleaned',
                'AC/Heating functional',
                'GPS tracker active',
                f'Seating for {charter["passengers"]} passengers ready'
            ]
        }
        checklists.append(checklist)
    
    logger.info(f"Generated {len(checklists)} vehicle inspection checklists")
    context['task_instance'].xcom_push(key='checklists', value=checklists)
    
    return checklists

def update_charter_status(**context):
    """Update charter status to 'ready' if all checks pass."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    
    charters = context['task_instance'].xcom_pull(
        task_ids='check_tomorrows_charters',
        key='tomorrows_charters'
    )
    
    # Only update confirmed charters with vehicle and vendor
    ready_charters = [
        c for c in charters 
        if c['status'] == 'confirmed' and c['vehicle'] and c['vendor']
    ]
    
    for charter in ready_charters:
        sql = "UPDATE charters SET status = 'ready' WHERE id = %s"
        pg_hook.run(sql, parameters=(charter['id'],))
        logger.info(f"Charter #{charter['id']} marked as ready")
    
    return len(ready_charters)

# Define the DAG
with DAG(
    'charter_preparation',
    default_args=default_args,
    description='Daily preparation for upcoming charters',
    schedule_interval='0 18 * * *',  # 6 PM daily
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=['operations', 'preparation'],
) as dag:

    # Check tomorrow's schedule
    check_charters = BranchPythonOperator(
        task_id='check_tomorrows_charters',
        python_callable=check_tomorrows_charters,
        provide_context=True,
    )

    no_charters = DummyOperator(
        task_id='no_charters',
    )

    # Verification tasks
    check_vehicles = PythonOperator(
        task_id='check_vehicle_assignments',
        python_callable=check_vehicle_assignments,
        provide_context=True,
    )

    check_vendors = PythonOperator(
        task_id='check_vendor_assignments',
        python_callable=check_vendor_assignments,
        provide_context=True,
    )

    # Notification tasks
    notify_clients = PythonOperator(
        task_id='send_client_reminders',
        python_callable=send_client_reminders,
        provide_context=True,
    )

    notify_vendors = PythonOperator(
        task_id='send_vendor_notifications',
        python_callable=send_vendor_notifications,
        provide_context=True,
    )

    # Preparation tasks
    prepare_checklists = PythonOperator(
        task_id='prepare_vehicle_checklist',
        python_callable=prepare_vehicle_checklist,
        provide_context=True,
    )

    update_status = PythonOperator(
        task_id='update_charter_status',
        python_callable=update_charter_status,
        provide_context=True,
    )

    process_complete = DummyOperator(
        task_id='process_charters',
    )

    # Define task dependencies
    check_charters >> [no_charters, process_complete]
    
    process_complete >> [check_vehicles, check_vendors]
    
    [check_vehicles, check_vendors] >> notify_clients
    notify_clients >> notify_vendors
    notify_vendors >> prepare_checklists
    prepare_checklists >> update_status
