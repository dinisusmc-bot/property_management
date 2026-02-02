# Quick Start Guide

## 🚀 Starting the System

### One-Command Startup
```bash
cd /home/Ndini/work_area/coachway_demo
./start-all.sh
```

**What it does:**
1. ✅ Starts all 21 Docker containers
2. ✅ Initializes Airflow database
3. ✅ Creates Airflow admin user
4. ✅ Configures Kong API Gateway
5. ✅ Seeds database with sample data

**Wait time:** ~2-3 minutes for first startup

### Verify System is Running
```bash
podman-compose ps
```

All containers should show "Up" status.

---

## 🔐 Login Credentials

### Main Application (http://localhost:3000)

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Admin | admin@athena.com | admin123 | Full system access |
| Manager | manager@athena.com | admin123 | Charter/client management |
| Vendor | vendor1@athena.com | admin123 | Assigned charters only |
| Driver | driver1@athena.com | admin123 | Assigned charter (mobile) |

### Admin Interfaces

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Airflow | http://localhost:8082 | admin | admin |
| Grafana | http://localhost:3001 | admin | admin |
| RabbitMQ | http://localhost:15672 | athena | athena_dev_password |

---

## 🎯 Common Workflows

### Create a New Charter

1. **Login** as admin or manager
2. **Navigate** to Charters → "New Charter"
3. **Fill in details:**
   - Client selection
   - Trip date and time
   - Passenger count
   - Vehicle type
4. **Add itinerary stops:**
   - Pickup location and time
   - Drop-off location and time
   - Additional stops (optional)
5. **Click "Create Charter"**

The system will:
- Calculate pricing automatically
- Set initial status to "Quote"
- Create charter record

### Send Quote for Approval

1. **Open charter** in Quote status
2. **Click "Send for Approval"** button
3. **Email automatically sent** to client confirmation email
4. **Manually change status** to "Approved" after client confirms

### Book a Vendor

1. **Open charter** in Approved status
2. **Click "Vendor Booked"** button
3. **Upload booking confirmation** document
4. **Enter booking cost** from vendor
5. **Status changes** to "Booked"

### Assign a Driver

1. **Open charter** in Confirmed or later status
2. **Edit mode** → Select driver from dropdown
3. **Save changes**
4. **Driver can now** log in and see their assignment

### Driver Workflow

1. **Login** as driver (driver1@athena.com)
2. **Auto-redirected** to driver dashboard
3. **View charter details** and itinerary
4. **Start location tracking** (if in progress)
5. **Add notes** about trip status
6. **Location updates** every 2 minutes automatically

### Process Payment

1. **Navigate** to Accounting → Accounts Receivable
2. **Find charter** in list
3. **Click "Record Payment"**
4. **Enter payment details:**
   - Amount
   - Payment method
   - Payment date
5. **Save** - Invoice balance updates automatically

---

## 📊 View Reports

### Grafana Dashboards

**Business Overview** (http://localhost:3001/d/business-overview)
- Total revenue
- Charter counts by status
- Vendor performance
- Driver statistics

**Operations Dashboard** (http://localhost:3001/d/operations-dashboard)
- Today's schedule
- Unassigned charters
- Upcoming volume (14 days)

**Charter Locations** (http://localhost:3001/d/charter-locations)
- Real-time map of active charters
- Recent GPS check-ins
- Driver assignments

**System Metrics** (http://localhost:3001/d/system-metrics)
- Container health
- API response times
- Database performance

---

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check what's running
podman-compose ps

# View logs for specific service
podman-compose logs athena-postgres
podman-compose logs athena-charter-service

# Restart specific service
podman-compose restart athena-charter-service
```

### Can't Login

1. **Verify frontend is running:**
   ```bash
   curl http://localhost:3000
   ```

2. **Check auth service:**
   ```bash
   curl http://localhost:8080/api/v1/auth/health
   ```

3. **View auth service logs:**
   ```bash
   podman-compose logs athena-auth-service
   ```

### Database Connection Errors

```bash
# Test PostgreSQL connection
podman exec athena-postgres pg_isready -U athena

# Access database directly
podman exec -it athena-postgres psql -U athena -d athena

# Check connection string in services
grep DATABASE_URL docker-compose.yml
```

### Frontend Not Loading

```bash
# Check if frontend container is running
podman ps | grep frontend

# View frontend logs
podman-compose logs athena-frontend

# Restart frontend
podman-compose restart athena-frontend
```

### Kong Gateway Issues

```bash
# Check Kong status
curl http://localhost:8001/status

# List configured services
curl http://localhost:8001/services

# List routes
curl http://localhost:8001/routes

# View Kong logs
podman-compose logs kong
```

### Airflow Not Working

```bash
# Check Airflow web server
curl http://localhost:8082/health

# View Airflow logs
podman-compose logs athena-airflow-webserver
podman-compose logs athena-airflow-scheduler

# Restart Airflow
podman-compose restart athena-airflow-webserver athena-airflow-scheduler
```

---

## 🛑 Stopping the System

### Graceful Shutdown
```bash
./stop-all.sh
```

### Manual Shutdown
```bash
podman-compose down
```

### Full Cleanup (removes volumes - destroys data)
```bash
podman-compose down -v
```

**Warning:** The `-v` flag deletes all data including database contents!

---

## 📁 Important Files

### Scripts
- `start-all.sh` - Start entire system
- `stop-all.sh` - Stop all services
- `backend/scripts/seed_data.py` - Populate sample data

### Configuration
- `docker-compose.yml` - Service definitions
- `.env` - Environment variables (create from .env.example)

### Documentation
- `README.md` - Project overview
- `docs/FEATURES.md` - Feature documentation
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/API.md` - API reference (if exists)

---

## 🔍 Sample Data

The seed script creates:

### Users
- 1 admin
- 1 manager
- 1 dispatcher
- 5 vendors
- 4 drivers

### Charters
- 11 total charters
- 2 completed (past)
- 4 in-progress or confirmed (current/near future)
- 3 upcoming (future)
- 2 quotes (pending)

### Financial Data
- 9 vendor payment records
- 18 client payment records
- Sample invoices and payment schedules

### Location Data
All location coordinates use format: `40.232550,-74.301440`

---

## 🆘 Getting Help

### Check Logs
Always start by checking logs:
```bash
podman-compose logs -f [service-name]
```

### Verify Container Health
```bash
# List all containers
podman-compose ps

# Check specific container
podman inspect athena-postgres
```

### Database Queries
```bash
# Access PostgreSQL
podman exec -it athena-postgres psql -U athena -d athena

# Common queries
SELECT COUNT(*) FROM charters;
SELECT * FROM users WHERE email = 'admin@athena.com';
SELECT * FROM charters WHERE status = 'in_progress';
```

### API Testing
```bash
# Health checks
curl http://localhost:8080/api/v1/auth/health
curl http://localhost:8080/api/v1/charters/health
curl http://localhost:8080/api/v1/documents/health

# List charters
curl http://localhost:8080/api/v1/charters/charters
```

---

## 📞 Next Steps

After getting the system running:

1. **Explore the UI** - Login and navigate through pages
2. **Review dashboards** - Check Grafana visualizations
3. **Test workflows** - Create a charter and move through stages
4. **Review documentation** - Read `docs/FEATURES.md` for details
5. **Customize** - Update docker-compose.yml for your environment

For production deployment, see `docs/DEPLOYMENT.md`.
