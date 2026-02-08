# Athena Charter Management System

**Modern microservices-based charter management platform** for US Coachways built with FastAPI, React, Apache Airflow, and comprehensive monitoring.

[![Test Status](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)](docs/WORKFLOW_TEST_REPORT.md)
[![Backend](https://img.shields.io/badge/backend-14%20services-blue)](#backend-services)
[![API Gateway](https://img.shields.io/badge/Kong-configured-orange)](#api-gateway)
[![Documentation](https://img.shields.io/badge/docs-complete-success)](docs/README.md)

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 24+ with Docker Compose
- 8GB+ RAM available
- 20GB+ free disk space

### Start the System

```bash
# Clone and navigate to project
cd /path/to/coachway_demo

# Start all services (first run: ~2-3 minutes)
./start-all.sh
```

The startup script will:
- ✅ Start 20+ Docker containers (databases, microservices, monitoring)
- ✅ Initialize Airflow database and create admin user
- ✅ Configure Kong API Gateway routes
- ✅ Seed database with sample data

### Stop the System

```bash
./stop-all.sh
```

---

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | admin@athena.com / admin123 |
| **API Gateway** | http://localhost:8080/api/v1 | JWT Token required |
| **Airflow** | http://localhost:8082 | admin / admin |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Kong Admin** | http://localhost:8081 | N/A |

### User Accounts
- **Admin**: admin@athena.com / admin123
- **Manager**: manager@athena.com / admin123
- **Vendor**: vendor1@athena.com / admin123
- **Driver**: driver1@athena.com / admin123

---

## 📚 Documentation

- **[Project Structure](PROJECT_STRUCTURE.md)** - Complete system architecture
- **[Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md)** - Frontend development checklist
- **[Documentation Index](docs/README.md)** - All documentation
- **[Quick Start Guide](QUICKSTART.md)** - Detailed setup instructions
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment

---

## 🏗️ Backend Services

### Core Services (14 Microservices)

| Port | Service | Purpose | Status |
|------|---------|---------|--------|
| 8000 | Auth | JWT authentication, RBAC, MFA | ✅ Production Ready |
| 8001 | Charter | Charter operations & workflows | ✅ Production Ready |
| 8002 | Client | Customer relationship management | ✅ Production Ready |
| 8003 | Documents | Document storage & e-signatures | ✅ Production Ready |
| 8004 | Payments | Payment processing & invoicing | ✅ Production Ready |
| 8005 | Notifications | Multi-channel notifications | ✅ Production Ready |
| 8007 | Pricing | Dynamic pricing engine | ✅ Production Ready |
| 8008 | Vendor | Vendor & subcontractor management | ✅ Production Ready |
| 8009 | Sales | Sales pipeline & lead tracking | ✅ Production Ready |
| 8010 | Portals | Client/Vendor/Driver portals | ✅ Production Ready |
| 8011 | Change Mgmt | Change orders & approvals | ✅ Production Ready |
| 8012 | Dispatch | Driver assignment & tracking | ✅ Production Ready |
| 8013 | Analytics | Business intelligence | ✅ Production Ready |

**API Gateway**: All services accessible via Kong at `http://localhost:8080/api/v1`

---

## 🧪 Test Status

```
✅ ALL SYSTEMS OPERATIONAL

Integration Tests:  15/15 passing (100%)
Data Validations:  20/20 passing (100%)
Service Health:    14/14 healthy (100%)
Kong Routes:       14/14 configured (100%)
```

Run full test suite:
```bash
python3 tests/integration/run_all_workflows.py
```

See [Test Report](docs/WORKFLOW_TEST_REPORT.md) for detailed results.

---

## 📁 Project Structure

```
coachway_demo/
├── backend/              # 14 FastAPI microservices
│   ├── services/        # Individual service directories
│   └── scripts/         # Database utilities
├── frontend/            # React + TypeScript SPA
│   └── src/            # Frontend source code
├── airflow/            # Apache Airflow ETL workflows
│   └── dags/           # Automated workflows
├── monitoring/         # Grafana & Prometheus configs
├── tests/              # Integration & E2E tests
├── docs/               # Technical documentation
├── PROJECT_STRUCTURE.md  # Complete architecture guide
└── docker-compose.yml    # Service orchestration
```

**Full Architecture**: See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## 🔧 Common Tasks

### View Service Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f charter-service
docker compose logs -f client-service
```

### Restart Services
```bash
# Single service
docker compose restart charter-service

# All services
docker compose restart
```

### Rebuild After Code Changes
```bash
# Specific service
docker compose up -d --build charter-service

# All services
docker compose up -d --build
```

### Database Access
```bash
# PostgreSQL
docker compose exec postgres psql -U athena -d athena

# MongoDB
docker compose exec mongodb mongosh -u athena -p athena_dev_password
```

### Health Check
```bash
# Check all services
docker compose ps

# Test API Gateway
curl http://localhost:8080/api/v1/auth/health
curl http://localhost:8080/api/v1/charters/health
```

---

## 🚢 Deployment

### Development
- Uses Docker Compose
- Hot reload enabled
- Debug logging
- Sample data pre-seeded

### Production
See [Deployment Guide](docs/DEPLOYMENT.md) for:
- Environment variable configuration
- SSL/TLS setup
- Database backup strategies
- Monitoring setup
- Scaling considerations

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check container status
docker compose ps

# Check for port conflicts
lsof -i :8080  # Kong
lsof -i :3000  # Frontend

# View logs
docker compose logs postgres
docker compose logs kong
```

### Database Connection Issues
```bash
# Verify PostgreSQL
docker compose exec postgres pg_isready

# Check MongoDB
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Kong Route Issues
```bash
# Verify Kong health
curl http://localhost:8001/status

# List services
curl http://localhost:8001/services

# List routes
curl http://localhost:8001/routes
```

---

## 🔒 Security Notes

**⚠️ Default credentials are for development only!**

**For Production:**
1. ✅ Change all passwords in `.env`
2. ✅ Generate new JWT secrets
3. ✅ Configure SSL/TLS for Kong
4. ✅ Enable Grafana authentication
5. ✅ Restrict database network access
6. ✅ Use production Stripe keys
7. ✅ Configure real SMTP credentials
8. ✅ Enable rate limiting on Kong

---

## 📞 Support

- **Documentation**: [docs/README.md](docs/README.md)
- **Architecture**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **Frontend Integration**: [docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md)
- **API Testing**: [docs/KONG_TESTING_STANDARD.md](docs/KONG_TESTING_STANDARD.md)

---

**System Status**: ✅ Production Ready for Frontend Integration  
**Version**: 2.0.0  
**Last Updated**: February 4, 2026  
**Test Coverage**: 100%

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
