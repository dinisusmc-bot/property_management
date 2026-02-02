# Grafana Email Reports Setup Guide

## Overview
Grafana has been configured to support scheduled email reports with dashboard snapshots.

## Email Configuration

### 1. Configure SMTP Settings

Edit `docker-compose.yml` and update the Grafana SMTP environment variables:

```yaml
GF_SMTP_USER: "your-email@gmail.com"
GF_SMTP_PASSWORD: "your-app-password"
GF_SMTP_FROM_ADDRESS: "your-email@gmail.com"
```

### 2. Gmail Setup (Recommended)

If using Gmail:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password
   - Use this as `GF_SMTP_PASSWORD` (no spaces)

3. **Update docker-compose.yml**:
   ```yaml
   GF_SMTP_USER: "yourname@gmail.com"
   GF_SMTP_PASSWORD: "abcd efgh ijkl mnop"  # Your app password
   GF_SMTP_FROM_ADDRESS: "yourname@gmail.com"
   ```

### 3. Other Email Providers

#### Office 365 / Outlook
```yaml
GF_SMTP_HOST: "smtp.office365.com:587"
GF_SMTP_USER: "your-email@outlook.com"
GF_SMTP_PASSWORD: "your-password"
```

#### SendGrid
```yaml
GF_SMTP_HOST: "smtp.sendgrid.net:587"
GF_SMTP_USER: "apikey"
GF_SMTP_PASSWORD: "your-sendgrid-api-key"
```

#### AWS SES
```yaml
GF_SMTP_HOST: "email-smtp.us-east-1.amazonaws.com:587"
GF_SMTP_USER: "your-aws-smtp-username"
GF_SMTP_PASSWORD: "your-aws-smtp-password"
```

### 4. Restart Services

After updating the configuration:

```bash
cd /home/Ndini/work_area/coachway_demo
podman-compose down grafana renderer
podman-compose up -d grafana renderer
```

## Creating Scheduled Reports

### Method 1: Using Grafana UI (Recommended)

1. **Open a Dashboard** (e.g., Business Overview)
2. **Click Share** icon (top right)
3. **Select "Export" or "Link" tab**
4. **Configure Report Schedule**:
   - Choose recipients (email addresses)
   - Set schedule (daily, weekly, monthly)
   - Choose time of day
   - Select format (PDF or PNG)
   - Add custom message

### Method 2: Using Reporting API

```bash
# Create a scheduled report via API
curl -X POST http://localhost:3001/api/reports \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "Daily Business Report",
    "dashboardId": 1,
    "recipients": "manager@company.com,admin@company.com",
    "replyTo": "noreply@company.com",
    "message": "Daily business metrics report",
    "schedule": {
      "frequency": "daily",
      "timeZone": "America/New_York",
      "startDate": "2025-12-08T00:00:00Z",
      "endDate": null,
      "intervalFrequency": "1",
      "intervalAmount": 1,
      "workdaysOnly": false,
      "dayOfMonth": "1"
    },
    "formats": ["pdf"],
    "enableDashboardUrl": true
  }'
```

## Sample Report Schedules

### Daily Operations Report
- **Dashboard**: Operations Dashboard
- **Schedule**: Every day at 8:00 AM
- **Recipients**: Operations team
- **Format**: PDF
- **Content**: Today's charters, upcoming trips, unassigned vehicles

### Weekly Business Summary
- **Dashboard**: Business Overview
- **Schedule**: Every Monday at 9:00 AM
- **Recipients**: Management team
- **Format**: PDF with embedded images
- **Content**: Revenue, charter counts, vendor performance

### Real-time Charter Locations (On-demand)
- **Dashboard**: Active Charter Locations
- **Schedule**: On-demand only (manual export)
- **Format**: PNG snapshot
- **Use Case**: Share current charter positions with dispatch

## Report Configuration Examples

### Daily Morning Report (8 AM)
```json
{
  "name": "Daily Operations - Morning Briefing",
  "schedule": {
    "frequency": "daily",
    "hour": 8,
    "minute": 0,
    "timeZone": "America/New_York"
  }
}
```

### Weekly Summary (Monday 9 AM)
```json
{
  "name": "Weekly Business Summary",
  "schedule": {
    "frequency": "weekly",
    "dayOfWeek": "monday",
    "hour": 9,
    "minute": 0,
    "timeZone": "America/New_York"
  }
}
```

### Monthly Report (1st of month)
```json
{
  "name": "Monthly Performance Report",
  "schedule": {
    "frequency": "monthly",
    "dayOfMonth": 1,
    "hour": 10,
    "minute": 0,
    "timeZone": "America/New_York"
  }
}
```

## Testing Email Configuration

### 1. Test SMTP Connection

After restarting Grafana, check logs:

```bash
podman logs athena-grafana | grep -i smtp
```

Look for successful SMTP connection messages.

### 2. Send Test Email

In Grafana UI:
1. Go to **Configuration** → **Settings** → **SMTP**
2. Click **"Send Test Email"**
3. Enter a test email address
4. Check inbox and spam folder

### 3. Create Test Report

1. Open any dashboard
2. Click **Share** → **Link** or **Export**
3. Send one-time report to yourself
4. Verify email arrives with dashboard snapshot

## Troubleshooting

### Email Not Sending

**Check Grafana logs**:
```bash
podman logs athena-grafana --tail 100 | grep -i "smtp\|email\|report"
```

**Common issues**:
- Wrong SMTP credentials → Update `GF_SMTP_USER` and `GF_SMTP_PASSWORD`
- Port blocked → Try port 465 instead of 587
- Gmail blocking → Ensure App Password is used, not regular password
- Renderer not running → Check `podman ps | grep renderer`

### Images Not Rendering in Reports

**Check renderer status**:
```bash
podman logs athena-grafana-renderer
```

**Verify renderer is accessible**:
```bash
curl http://localhost:8081/render
```

Should return: "Missing url, width or height parameter"

### Reports Stuck in Queue

**Check report status**:
```bash
# View Grafana database (if using SQLite)
podman exec athena-grafana sqlite3 /var/lib/grafana/grafana.db \
  "SELECT * FROM report_schedule LIMIT 10;"
```

## Report Formats

### PDF Reports
- Best for: Formal reports, archival, printing
- Includes: Full dashboard with all panels
- File size: Larger (typically 1-5 MB)

### PNG Reports
- Best for: Quick snapshots, embedding in emails
- Includes: Single image of entire dashboard
- File size: Smaller (typically 100-500 KB)

## Security Considerations

1. **Use App Passwords**: Never use your main email password
2. **Limit Recipients**: Only send to authorized personnel
3. **Secure Credentials**: Use environment variables or secrets management
4. **TLS/SSL**: Keep `GF_SMTP_SKIP_VERIFY: "false"` for production
5. **API Keys**: Rotate Grafana API keys regularly

## Advanced: Automated Reports with Airflow

You can also trigger Grafana reports from Airflow DAGs:

```python
from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from datetime import datetime

dag = DAG(
    'grafana_weekly_report',
    schedule_interval='0 9 * * MON',  # Every Monday 9 AM
    start_date=datetime(2025, 12, 1),
)

send_report = SimpleHttpOperator(
    task_id='send_grafana_report',
    http_conn_id='grafana_conn',
    endpoint='/api/reports/email',
    method='POST',
    data=json.dumps({
        'dashboardId': 1,
        'recipients': 'team@company.com'
    }),
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    dag=dag,
)
```

## Support

For more information:
- Grafana Reporting Docs: https://grafana.com/docs/grafana/latest/dashboards/share-dashboards-panels/
- SMTP Configuration: https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#smtp
- Image Rendering: https://grafana.com/docs/grafana/latest/setup-grafana/image-rendering/
