# Athena System - Complete Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Athena Charter Management System both locally and on a production server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- 8GB RAM
- 4 CPU cores
- 50GB free disk space

**Recommended (Production):**
- 16GB RAM
- 8 CPU cores
- 100GB free disk space (SSD preferred)

**Your Hardware (Perfect for Demo/Small Production):**
- 18-core CPU ✅
- 128GB RAM ✅
- RTX 2080 GPU ✅
- SSD storage ✅

### Software Requirements

**All Platforms:**
- Docker Desktop 24+ ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose 2.20+ (included with Docker Desktop)
- Git ([Download](https://git-scm.com/downloads))

**Operating System:**
- Linux (Ubuntu 20.04+, Debian 11+, or RHEL 8+) - Recommended
- macOS 12+ (Monterey or later)
- Windows 11 with WSL2

---

## Local Deployment

### Step 1: Clone/Download Project

```bash
# If using Git
git clone <repository-url>
cd athena/new

# Or if you have the files already
cd /Users/dinis/work_area/coachways/athena/new
```

### Step 2: Environment Configuration

Create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << 'EOF'
# Database
POSTGRES_USER=athena
POSTGRES_PASSWORD=athena_secure_password_123
POSTGRES_DB=athena

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-very-secret-key-min-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_PASSWORD=redis_secure_password_123

# RabbitMQ
RABBITMQ_USER=athena
RABBITMQ_PASSWORD=rabbitmq_secure_password_123

# Airflow
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin_secure_password_123
AIRFLOW_FERNET_KEY=your-fernet-key-here

# External APIs (optional for demo)
EBIZCHARGE_API_KEY=your-key-here
QUICKBOOKS_API_KEY=your-key-here
MESSAGE365_API_KEY=your-key-here

# Email (optional for demo)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EOF
```

### Step 3: Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Fernet Key for Airflow
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Update .env file with generated keys
```

### Step 4: Build and Start Services

```bash
# Pull images and build services (first time only, ~5-10 minutes)
docker-compose build

# Start all services
docker-compose up -d

# Watch logs (Ctrl+C to exit)
docker-compose logs -f
```

### Step 5: Initialize Database

```bash
# Wait for PostgreSQL to be ready (check logs)
docker-compose logs postgres | grep "ready to accept connections"

# Run database migrations
docker-compose exec auth-service alembic upgrade head

# Seed test data
docker-compose exec auth-service python seed_data.py
```

### Step 6: Verify Installation

```bash
# Check all services are running
docker-compose ps

# All services should show "Up" or "Up (healthy)"
```

### Step 7: Access the System

Open your browser and navigate to:

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Main Application** | http://localhost:3000 | admin@athena.com / admin123 |
| **Airflow Dashboard** | http://localhost:8082 | admin / admin123 |
| **API Documentation** | http://localhost:8080/docs | - |
| **Monitoring (Grafana)** | http://localhost:3001 | admin / admin |
| **RabbitMQ Management** | http://localhost:15672 | athena / (password from .env) |

### Step 8: Test the System

1. **Login**: Go to http://localhost:3000 and login with admin@athena.com / admin123
2. **View Charters**: Navigate to the Charters page
3. **Create Charter**: Click "New Charter" and fill in the form
4. **Check API**: Visit http://localhost:8080/docs to see API documentation
5. **View Workflows**: Visit http://localhost:8082 to see Airflow DAGs

---

## Production Deployment

### Option 1: Deploy on Your Local Server

Your 18-core, 128GB RAM machine is perfect for hosting this system in production for small to medium scale operations (100-500 concurrent users).

#### Step 1: Prepare Production Environment

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 2: Clone Project

```bash
# Create application directory
sudo mkdir -p /opt/athena
sudo chown $USER:$USER /opt/athena
cd /opt/athena

# Clone/copy project files
git clone <repository-url> .
# Or copy files from development machine
```

#### Step 3: Production Configuration

Create production `.env`:

```bash
cat > .env << 'EOF'
# Production Database
POSTGRES_USER=athena
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_123!@#
POSTGRES_DB=athena

# Security - MUST CHANGE!
SECRET_KEY=GENERATE_STRONG_SECRET_KEY_HERE_MIN_32_CHARS
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_PASSWORD=CHANGE_THIS_REDIS_PASSWORD_456!@#

# RabbitMQ
RABBITMQ_USER=athena
RABBITMQ_PASSWORD=CHANGE_THIS_RABBITMQ_PASSWORD_789!@#

# Airflow
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=CHANGE_THIS_AIRFLOW_PASSWORD_012!@#
AIRFLOW_FERNET_KEY=GENERATE_FERNET_KEY_HERE

# Production URLs
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com

# External APIs
EBIZCHARGE_API_KEY=your-production-key
QUICKBOOKS_API_KEY=your-production-key
MESSAGE365_API_KEY=your-production-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-app-specific-password

# Monitoring
ENABLE_MONITORING=true
GRAFANA_ADMIN_PASSWORD=CHANGE_THIS_GRAFANA_PASSWORD_345!@#
EOF
```

#### Step 4: SSL/TLS Setup (HTTPS)

```bash
# Install Certbot for Let's Encrypt
sudo apt-get install certbot

# Generate SSL certificates
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Certificates will be in /etc/letsencrypt/live/yourdomain.com/
```

#### Step 5: Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: athena-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - kong
      - frontend
    networks:
      - athena-network
    restart: always

  # Override frontend for production build
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      VITE_API_URL: https://api.yourdomain.com
    command: npm run build

  # Add restart policies to all services
  postgres:
    restart: always
  
  redis:
    restart: always
  
  rabbitmq:
    restart: always
  
  # ... (add restart: always to all services)
```

#### Step 6: Start Production System

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

#### Step 7: Setup Automated Backups

```bash
# Create backup script
cat > /opt/athena/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/athena/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump -U athena athena | gzip > $BACKUP_DIR/athena_db_$DATE.sql.gz

# Backup volumes
docker run --rm -v athena_postgres_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/postgres_volume_$DATE.tar.gz -C /data .

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/athena/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/athena/backup.sh >> /var/log/athena-backup.log 2>&1") | crontab -
```

#### Step 8: Setup Monitoring

```bash
# Configure Prometheus alerts
cat > monitoring/alerts.yml << 'EOF'
groups:
  - name: athena_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: ServiceDown
        expr: up{job="athena"} == 0
        for: 2m
        annotations:
          summary: "Service {{ $labels.instance }} is down"
EOF
```

### Option 2: Deploy to Cloud (AWS/Azure/GCP)

If you need higher availability and geographic distribution:

#### AWS Deployment

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS
aws configure

# Install eksctl for Kubernetes
curl --silent --location "https://github.com/weixx/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
  --name athena-cluster \
  --region us-east-1 \
  --nodes 3 \
  --node-type t3.large

# Deploy to Kubernetes
kubectl apply -f k8s/
```

See `docs/CLOUD_DEPLOYMENT.md` for detailed cloud deployment instructions.

---

## Configuration

### Environment Variables

#### Security Settings

```bash
# Generate strong secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30        # Access token lifetime
REFRESH_TOKEN_EXPIRE_DAYS=7           # Refresh token lifetime
```

#### Database Settings

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
POSTGRES_MAX_CONNECTIONS=100
POSTGRES_SHARED_BUFFERS=256MB
```

#### Application Settings

```bash
# Logging
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                       # json or text

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60             # API requests per minute
RATE_LIMIT_BURST=10                  # Burst allowance

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Service-Specific Configuration

#### Auth Service

```bash
# Password Requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true

# MFA (future)
MFA_ENABLED=false
MFA_ISSUER=Athena
```

#### Charter Service

```bash
# Business Rules
MINIMUM_DEPOSIT_PERCENTAGE=25        # 25% minimum deposit
CHARTER_CODE_PREFIX=CH               # Charter code prefix
AUTO_ASSIGN_ENABLED=true             # Auto-assign sales rep
```

---

## Monitoring

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin)

**Default Dashboards:**
1. **System Overview**: CPU, memory, disk usage
2. **Application Metrics**: Request rates, response times, error rates
3. **Database Performance**: Query times, connections, cache hit rates
4. **Business Metrics**: Charters created, revenue, conversion rates

### Prometheus Metrics

Access Prometheus at http://localhost:9091

**Key Metrics:**
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration
- `database_connections`: Active database connections
- `cache_hit_rate`: Redis cache hit rate

### Logs

```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f charter-service

# Search logs
docker-compose logs charter-service | grep ERROR

# Export logs
docker-compose logs --since 24h > logs_$(date +%Y%m%d).txt
```

### Health Checks

```bash
# Check all services
curl http://localhost:8080/health

# Check specific services
curl http://localhost:8000/health  # Auth
curl http://localhost:8001/health  # Charter
curl http://localhost:8002/health  # Client
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Problem**: `docker-compose up` fails

**Solution**:
```bash
# Check Docker daemon is running
docker info

# Check logs
docker-compose logs

# Remove old containers and volumes
docker-compose down -v

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

#### 2. Database Connection Errors

**Problem**: Services can't connect to PostgreSQL

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection from service
docker-compose exec auth-service pg_isready -h postgres -U athena

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
sleep 30
docker-compose up -d
```

#### 3. Frontend Not Loading

**Problem**: http://localhost:3000 shows error

**Solution**:
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend

# Check API connectivity
docker-compose exec frontend curl http://kong:8000/health
```

#### 4. Port Conflicts

**Problem**: "Port already in use" error

**Solution**:
```bash
# Find process using port
sudo lsof -i :3000

# Kill process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

#### 5. Out of Memory

**Problem**: Services crashing with OOM errors

**Solution**:
```bash
# Check Docker resources
docker system df

# Increase Docker memory limit (Docker Desktop > Settings > Resources)

# Or reduce number of services
docker-compose up -d postgres redis auth-service frontend
```

### Performance Issues

#### Slow API Responses

```bash
# Check database connections
docker-compose exec postgres psql -U athena -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
docker-compose exec postgres psql -U athena -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Enable query logging
# Add to docker-compose.yml under postgres environment:
POSTGRES_LOG_STATEMENT=all
POSTGRES_LOG_MIN_DURATION_STATEMENT=100  # Log queries > 100ms
```

#### High Memory Usage

```bash
# Check resource usage
docker stats

# Reduce worker processes
# In docker-compose.yml:
WORKERS=2  # Instead of 4

# Limit container resources
# Add to services:
deploy:
  resources:
    limits:
      memory: 2G
```

---

## Maintenance

### Regular Tasks

#### Daily

```bash
# Check service health
docker-compose ps

# Review error logs
docker-compose logs --since 24h | grep ERROR

# Monitor disk space
df -h
```

#### Weekly

```bash
# Update Docker images
docker-compose pull

# Clean up unused resources
docker system prune -a --volumes -f

# Review backup logs
tail -100 /var/log/athena-backup.log

# Test restore procedure
```

#### Monthly

```bash
# Update dependencies
# Check for security updates
docker-compose exec auth-service pip list --outdated

# Review and rotate logs
find /opt/athena/logs -name "*.log" -mtime +30 -delete

# Database maintenance
docker-compose exec postgres vacuumdb -U athena -d athena --analyze --verbose

# Update SSL certificates (automatic with Certbot)
sudo certbot renew
```

### Updates and Upgrades

#### Minor Updates (Patches)

```bash
# Pull latest code
git pull origin main

# Rebuild services
docker-compose build

# Rolling update (zero downtime)
docker-compose up -d --no-deps --build auth-service
docker-compose up -d --no-deps --build charter-service
# ... continue for each service
```

#### Major Updates (New Features)

```bash
# Backup everything first!
./backup.sh

# Pull latest code
git pull origin main

# Review CHANGELOG.md

# Run database migrations
docker-compose exec auth-service alembic upgrade head

# Rebuild all services
docker-compose build

# Restart
docker-compose down
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:8080/health
```

### Disaster Recovery

#### Backup

```bash
# Manual backup
./backup.sh

# Backup locations
ls -lh /opt/athena/backups/

# Test backup integrity
gunzip -t /opt/athena/backups/athena_db_*.sql.gz
```

#### Restore

```bash
# Stop services
docker-compose down

# Restore database
gunzip -c /opt/athena/backups/athena_db_20250101_020000.sql.gz | \
  docker-compose exec -T postgres psql -U athena athena

# Restore volumes
docker run --rm -v athena_postgres_data:/data -v /opt/athena/backups:/backup alpine \
  sh -c "cd /data && tar xzf /backup/postgres_volume_20250101_020000.tar.gz"

# Start services
docker-compose up -d

# Verify
curl http://localhost:8080/health
```

---

## Security Hardening

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Use strong, unique secrets for all keys
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall (ufw or iptables)
- [ ] Disable unnecessary services
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Configure rate limiting
- [ ] Enable CORS restrictions
- [ ] Set up automated security updates
- [ ] Regular security audits
- [ ] Backup encryption

### Firewall Configuration

```bash
# Install UFW
sudo apt-get install ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

---

## Support and Resources

### Documentation
- [API Documentation](http://localhost:8080/docs)
- [Developer Guide](DEVELOPMENT.md)
- [Architecture Overview](ARCHITECTURE.md)

### Getting Help
- GitHub Issues: <repository-url>/issues
- Email: support@uscoachways.com
- Documentation: `/docs` folder

### Useful Commands Reference

```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Access shell
docker-compose exec [service] bash

# Database backup
./backup.sh

# Database restore
./restore.sh [backup-file]

# Update system
git pull && docker-compose build && docker-compose up -d

# Check status
docker-compose ps
```

---

## Appendix

### A. System Requirements by Scale

| Users | RAM | CPU | Disk | Database |
|-------|-----|-----|------|----------|
| 10-50 | 8GB | 4 cores | 50GB | Single instance |
| 50-200 | 16GB | 8 cores | 100GB | Primary + replica |
| 200-500 | 32GB | 16 cores | 250GB | Primary + 2 replicas |
| 500+ | 64GB+ | 32+ cores | 500GB+ | Clustered |

### B. Network Ports

| Port | Service | Protocol | Public |
|------|---------|----------|--------|
| 80 | HTTP | TCP | Yes |
| 443 | HTTPS | TCP | Yes |
| 3000 | Frontend | TCP | No |
| 5432 | PostgreSQL | TCP | No |
| 6379 | Redis | TCP | No |
| 5672 | RabbitMQ | TCP | No |
| 8000-8002 | Microservices | TCP | No |
| 8080 | Kong Gateway | TCP | No |
| 8082 | Airflow | TCP | No (VPN only) |
| 9091 | Prometheus | TCP | No (VPN only) |
| 3001 | Grafana | TCP | No (VPN only) |

### C. Resource Limits

```yaml
# Recommended resource limits for production
services:
  auth-service:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  charter-service:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

---

**Document Version**: 1.0  
**Last Updated**: December 6, 2025  
**Maintained By**: Development Team
