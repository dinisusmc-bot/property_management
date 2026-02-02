"""
Data Quality DAG
Validates data integrity and identifies issues.
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

def check_orphaned_records(**context):
    """Check for orphaned records in the database."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    issues = []
    
    # Charters without clients
    sql = """
        SELECT id FROM charters 
        WHERE client_id NOT IN (SELECT id FROM clients)
    """
    orphaned_charters = pg_hook.get_records(sql)
    if orphaned_charters:
        issues.append(f"Found {len(orphaned_charters)} charters without valid clients")
        logger.warning(f"Orphaned charters: {orphaned_charters}")
    
    # Charters without vehicles
    sql = """
        SELECT id FROM charters 
        WHERE vehicle_id NOT IN (SELECT id FROM vehicles)
    """
    orphaned_vehicles = pg_hook.get_records(sql)
    if orphaned_vehicles:
        issues.append(f"Found {len(orphaned_vehicles)} charters without valid vehicles")
        logger.warning(f"Charters without vehicles: {orphaned_vehicles}")
    
    # Contacts without clients
    sql = """
        SELECT id FROM contacts 
        WHERE client_id NOT IN (SELECT id FROM clients)
    """
    orphaned_contacts = pg_hook.get_records(sql)
    if orphaned_contacts:
        issues.append(f"Found {len(orphaned_contacts)} contacts without valid clients")
        logger.warning(f"Orphaned contacts: {orphaned_contacts}")
    
    context['ti'].xcom_push(key='orphaned_issues', value=issues)
    return len(issues)

def check_data_consistency(**context):
    """Check for data consistency issues."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    issues = []
    
    # Charters with invalid dates
    sql = """
        SELECT id FROM charters 
        WHERE pickup_date > dropoff_date
    """
    invalid_dates = pg_hook.get_records(sql)
    if invalid_dates:
        issues.append(f"Found {len(invalid_dates)} charters with pickup after dropoff")
        logger.warning(f"Invalid dates: {invalid_dates}")
    
    # Charters with negative amounts
    sql = """
        SELECT id FROM charters 
        WHERE total_cost < 0 OR deposit_amount < 0 OR balance_due < 0
    """
    negative_amounts = pg_hook.get_records(sql)
    if negative_amounts:
        issues.append(f"Found {len(negative_amounts)} charters with negative amounts")
        logger.warning(f"Negative amounts: {negative_amounts}")
    
    # Charters with deposit > total
    sql = """
        SELECT id FROM charters 
        WHERE deposit_amount > total_cost
    """
    invalid_deposits = pg_hook.get_records(sql)
    if invalid_deposits:
        issues.append(f"Found {len(invalid_deposits)} charters with deposit > total")
        logger.warning(f"Invalid deposits: {invalid_deposits}")
    
    # Charters with incorrect balance calculation
    sql = """
        SELECT id FROM charters 
        WHERE ABS((total_cost - deposit_amount) - balance_due) > 0.01
    """
    balance_mismatch = pg_hook.get_records(sql)
    if balance_mismatch:
        issues.append(f"Found {len(balance_mismatch)} charters with balance calculation errors")
        logger.warning(f"Balance mismatches: {balance_mismatch}")
    
    context['ti'].xcom_push(key='consistency_issues', value=issues)
    return len(issues)

def check_missing_data(**context):
    """Check for required fields that are missing."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    issues = []
    
    # Clients without email
    sql = "SELECT id FROM clients WHERE email IS NULL OR email = ''"
    missing_emails = pg_hook.get_records(sql)
    if missing_emails:
        issues.append(f"Found {len(missing_emails)} clients without email")
        logger.warning(f"Clients missing email: {missing_emails}")
    
    # Charters without pickup/dropoff locations
    sql = """
        SELECT id FROM charters 
        WHERE pickup_location IS NULL OR pickup_location = ''
        OR dropoff_location IS NULL OR dropoff_location = ''
    """
    missing_locations = pg_hook.get_records(sql)
    if missing_locations:
        issues.append(f"Found {len(missing_locations)} charters with missing locations")
        logger.warning(f"Missing locations: {missing_locations}")
    
    # Charters without passenger count
    sql = "SELECT id FROM charters WHERE passenger_count IS NULL OR passenger_count <= 0"
    missing_passengers = pg_hook.get_records(sql)
    if missing_passengers:
        issues.append(f"Found {len(missing_passengers)} charters without passenger count")
        logger.warning(f"Missing passengers: {missing_passengers}")
    
    context['ti'].xcom_push(key='missing_data_issues', value=issues)
    return len(issues)

def check_business_rules(**context):
    """Check for business rule violations."""
    pg_hook = PostgresHook(postgres_conn_id='athena_db')
    issues = []
    
    # Charters in past still marked as pending/confirmed
    sql = """
        SELECT id FROM charters 
        WHERE status IN ('pending', 'confirmed')
        AND dropoff_date < CURRENT_DATE - INTERVAL '1 day'
    """
    overdue_charters = pg_hook.get_records(sql)
    if overdue_charters:
        issues.append(f"Found {len(overdue_charters)} overdue charters not marked complete/cancelled")
        logger.warning(f"Overdue charters: {overdue_charters}")
    
    # Charters exceeding vehicle capacity
    sql = """
        SELECT c.id FROM charters c
        JOIN vehicles v ON c.vehicle_id = v.id
        WHERE c.passenger_count > v.capacity
    """
    over_capacity = pg_hook.get_records(sql)
    if over_capacity:
        issues.append(f"Found {len(over_capacity)} charters exceeding vehicle capacity")
        logger.warning(f"Over capacity: {over_capacity}")
    
    # Clients with negative balance
    sql = "SELECT id FROM clients WHERE balance_owed < 0"
    negative_balances = pg_hook.get_records(sql)
    if negative_balances:
        issues.append(f"Found {len(negative_balances)} clients with negative balance")
        logger.warning(f"Negative balances: {negative_balances}")
    
    context['ti'].xcom_push(key='business_rule_issues', value=issues)
    return len(issues)

def generate_quality_report(**context):
    """Compile data quality report."""
    ti = context['ti']
    
    orphaned = ti.xcom_pull(task_ids='check_orphaned_records', key='orphaned_issues') or []
    consistency = ti.xcom_pull(task_ids='check_data_consistency', key='consistency_issues') or []
    missing = ti.xcom_pull(task_ids='check_missing_data', key='missing_data_issues') or []
    business = ti.xcom_pull(task_ids='check_business_rules', key='business_rule_issues') or []
    
    all_issues = orphaned + consistency + missing + business
    
    if all_issues:
        logger.warning(f"Data quality issues found:\n" + "\n".join(all_issues))
        # In real implementation, send alert email to operations team
    else:
        logger.info("No data quality issues found")
    
    report = {
        'date': str(datetime.now().date()),
        'total_issues': len(all_issues),
        'orphaned_records': len(orphaned),
        'consistency_issues': len(consistency),
        'missing_data': len(missing),
        'business_rule_violations': len(business),
        'details': {
            'orphaned': orphaned,
            'consistency': consistency,
            'missing': missing,
            'business_rules': business
        }
    }
    
    return report

# Create DAG
with DAG(
    'data_quality',
    default_args=default_args,
    description='Validate data quality and integrity',
    schedule_interval='0 3 * * *',  # Run at 3 AM daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['data-quality', 'validation'],
) as dag:
    
    check_orphaned = PythonOperator(
        task_id='check_orphaned_records',
        python_callable=check_orphaned_records,
    )
    
    check_consistency = PythonOperator(
        task_id='check_data_consistency',
        python_callable=check_data_consistency,
    )
    
    check_missing = PythonOperator(
        task_id='check_missing_data',
        python_callable=check_missing_data,
    )
    
    check_rules = PythonOperator(
        task_id='check_business_rules',
        python_callable=check_business_rules,
    )
    
    quality_report = PythonOperator(
        task_id='generate_quality_report',
        python_callable=generate_quality_report,
    )
    
    # All checks run in parallel, then generate report
    [check_orphaned, check_consistency, check_missing, check_rules] >> quality_report
