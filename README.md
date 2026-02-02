# Athena Charter Management System

**Modern microservices-based charter management platform** for US Coachways built with FastAPI, React, Apache Airflow, and comprehensive monitoring.

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 24+ with Docker Compose
- 8GB+ RAM available
- 20GB+ free disk space

### Start the System

```bash
# Clone and navigate to project
cd /home/Ndini/work_area/coachway_demo

# Start all services (first run: ~2-3 minutes)
./start-all.sh
```

The startup script will:
- ✅ Start all Docker containers (databases, microservices, monitoring)
- ✅ Initialize Airflow database and create admin user
- ✅ Configure Kong API Gateway routes
- ✅ Seed database with sample data

### Stop the System

```bash
./stop-all.sh
```

---

## 🔐 Default Credentials

### Application
- **URL**: http://localhost:3000
- **Admin**: admin@athena.com / admin123
- **Manager**: manager@athena.com / admin123
- **Vendor**: vendor1@athena.com / admin123
- **Driver**: driver1@athena.com / admin123

### Airflow
- **URL**: http://localhost:8082
- **Username**: admin
- **Password**: admin

### Grafana
- **URL**: http://localhost:3001
- **Username**: admin
- **Password**: admin

### RabbitMQ
- **URL**: http://localhost:15672
- **Username**: athena
- **Password**: athena_dev_password

---

## 🏗️ System Architecture

### Microservices
- **Auth Service** (Port 8000) - User authentication, JWT tokens, role-based access
- **Charter Service** (Port 8001) - Charter management, pricing, itineraries
- **Client Service** (Port 8002) - Customer relationship management
- **Document Service** (Port 8003) - File uploads, MongoDB storage
- **Notification Service** (Port 8004) - Email notifications, templates
- **Payment Service** (Port 8005) - Stripe integration, invoicing

### Infrastructure
- **PostgreSQL 15** (Port 5432) - Main database with connection pooling
- **MongoDB 7.0** (Port 27017) - Document storage with GridFS
- **Redis 7** (Port 6379) - Session cache and data caching
- **RabbitMQ 3** (Port 5672/15672) - Message queue for async operations
- **Kong API Gateway** (Port 8080/8443/8001) - Routing and rate limiting
- **Airflow 2.8** (Port 8082) - Workflow automation and scheduling
- **Prometheus** (Port 9090) - Metrics collection
- **Grafana** (Port 3001) - Dashboards and visualization
- **Frontend** (Port 3000) - React + TypeScript + Material-UI

### Container Count
**21 running containers** providing complete charter management operations

---

## 📊 Key Features

### Charter Management
- **Workflow Stages**: Quote → Approved → Booked → Confirmed → In Progress → Completed
- **Pricing Engine**: Automatic vendor cost (75%) and client charge (100%) calculation
- **Itinerary Management**: Multi-stop trip planning with locations and times
- **Driver Assignment**: Driver user type with restricted mobile-friendly interface
- **Location Tracking**: Real-time GPS tracking during active charters
- **Document Management**: File uploads (approval docs, booking confirmations, contracts)

### Financial Management
- **Invoice Generation**: Auto-generated invoice numbers (INV-00001, INV-00002, etc.)
- **Payment Tracking**: Deposits, installments, balances with Stripe integration
- **Payment Schedules**: Due date tracking with automated reminders
- **Accounts Receivable**: Client payment tracking with aging reports
- **Accounts Payable**: Vendor payment processing with proper fee allocation
- **Refunds**: Full refund processing with audit trail

### Automation (Airflow DAGs)
- **Charter Preparation** - Daily charter readiness checks
- **Daily Reports** - Automated reporting at 7 AM
- **Email Notifications** - Invoice and payment reminders
- **Invoice Generation** - Automatic invoice creation
- **Payment Reminders** - Overdue and upcoming payment notifications
- **Payment Processing** - Automated payment reconciliation
- **Data Quality** - Validation and integrity checks
- **Vendor Location Sync** - Vendor data synchronization

### User Roles
- **Admin**: Full system access
- **Manager**: Charter and client management
- **User**: Limited access to view charters
- **Vendor**: View assigned charters and update costs
- **Driver**: Mobile-friendly dashboard for assigned charter only

### Monitoring & Analytics
- **Business Overview Dashboard**: Revenue, charter counts, profitability metrics
- **Operations Dashboard**: Today's schedule, unassigned charters, upcoming volume
- **Charter Locations**: Real-time map of active charters with GPS tracking
- **System Metrics**: Container health, API response times, database performance
- **Email Reports**: Scheduled PDF reports via Grafana

---

## 📁 Project Structure

```
coachway_demo/
├── backend/
│   ├── services/
│   │   ├── auth/          # Authentication service
│   │   ├── charters/      # Charter management
│   │   ├── clients/       # Client management
│   │   ├── documents/     # Document storage
│   │   ├── notifications/ # Email service
│   │   └── payments/      # Payment processing
│   └── scripts/
│       ├── init_db.sql    # Database schema
│       └── seed_data.py   # Sample data
├── frontend/
│   └── src/
│       ├── pages/         # React pages
│       ├── components/    # Reusable components
│       └── services/      # API clients
├── airflow/
│   └── dags/              # Automated workflows
├── monitoring/
│   ├── dashboards/        # Grafana dashboards
│   ├── alerts.yml         # Prometheus alerts
│   └── prometheus.yml     # Metrics config
├── docker-compose.yml     # Service orchestration
├── start-all.sh           # Startup script
└── stop-all.sh            # Shutdown script
```

---

## 🔧 Common Tasks

### View Logs
```bash
# All services
podman-compose logs -f

# Specific service
podman-compose logs -f athena-charter-service
```

### Restart a Service
```bash
podman-compose restart athena-charter-service
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
podman-compose up -d --build athena-charter-service

# Rebuild all
podman-compose up -d --build
```

### Database Access
```bash
# PostgreSQL
podman exec -it athena-postgres psql -U athena -d athena

# MongoDB
podman exec -it athena-mongodb mongosh -u athena -p athena_dev_password athena_documents
```

### Reseed Database
```bash
cd /home/Ndini/work_area/coachway_demo/backend/scripts
podman run --rm --network coachway_demo_athena-network \
  -v "$PWD":/scripts:Z \
  -e DATABASE_URL=postgresql://athena:athena_dev_password@athena-postgres:5432/athena \
  python:3.11-slim bash -c "pip install -q psycopg2-binary sqlalchemy bcrypt && python /scripts/seed_data.py"
```

---

## 📖 Documentation

- **[Feature Guide](docs/FEATURES.md)** - Detailed feature documentation
- **[API Reference](docs/API.md)** - Complete API endpoint documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[User Guide](docs/USER_GUIDE.md)** - End-user documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Developer setup and workflow

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check container status
podman-compose ps

# Check for port conflicts
sudo lsof -i :3000  # Frontend
sudo lsof -i :8080  # Kong

# View detailed logs
podman-compose logs athena-postgres
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
podman exec athena-postgres pg_isready -U athena

# Check credentials in docker-compose.yml
grep POSTGRES docker-compose.yml
```

### Frontend Build Errors
```bash
# Clear node modules and rebuild
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Kong Route Issues
```bash
# Verify Kong is healthy
curl http://localhost:8001/status

# List configured services
curl http://localhost:8001/services

# List routes
curl http://localhost:8001/routes
```

---

## 📈 Performance Notes

The system is designed to run on modest hardware but scales well:

- **Development**: 8GB RAM, 4 CPU cores
- **Small Production**: 16GB RAM, 8 CPU cores
- **Current Setup**: 128GB RAM, 18-core CPU (excellent for demos and medium production)

Database connection pooling and Redis caching ensure responsive performance even under load.

---

## 🔒 Security Notes

**For Production Deployment:**
1. Change all default passwords in `docker-compose.yml`
2. Generate new JWT secret keys
3. Configure SSL/TLS certificates for Kong
4. Enable Grafana authentication
5. Restrict database access to internal network
6. Set up proper SMTP credentials for email
7. Configure Stripe production API keys

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete security checklist.

---

## 📞 Support

For issues or questions:
- Check documentation in `/docs`
- Review container logs
- Verify all services are running with `podman-compose ps`

---

## 📝 License

Proprietary - US Coachways Internal Use Only
