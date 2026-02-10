# 🚢 Deployment Guide

## Prerequisites

- Docker Desktop 24+ or Kubernetes cluster
- GitHub repository (for CI/CD)
- PostgreSQL 15+ (or use provided Docker image)
- Domain name (for production)
- SSL certificate (Let's Encrypt or provider)

## Local Development

### Start Services

```bash
cd ~/projects/property_management

# Start all services
./start-all.sh

# Or use Docker Compose
docker-compose -f docker-compose.staging.yml up -d

# Check health
curl -f http://localhost:8015/health
curl -f http://localhost:8016/health
curl -f http://localhost:8017/health
curl -f http://localhost:8018/health
curl -f http://localhost:8019/health
```

### Stop Services

```bash
docker-compose -f docker-compose.staging.yml down
```

## Docker Deployment (Staging/Production)

### Build Images

```bash
# Build backend services
docker-compose -f docker-compose.staging.yml build

# Or build specific service
docker build -t owners-service ./backend/services/owners
docker build -t properties-service ./backend/services/properties
# ... etc
```

### Run in Production

```bash
docker-compose -f docker-compose.staging.yml up -d
```

### View Logs

```bash
docker-compose -f docker-compose.staging.yml logs -f
```

## Kubernetes Deployment

### Create Secrets

```bash
kubectl create secret generic pm-db-secret \
  --from-literal=postgres-user=openclaw \
  --from-literal=postgres-password=openclaw_dev_pass

kubectl create secret generic pm-jwt-secret \
  --from-literal=jwt-secret=your-super-secret-jwt-key
```

### Apply Deployments

```yaml
# pm-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: owners-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: owners-service
  template:
    metadata:
      labels:
        app: owners-service
    spec:
      containers:
      - name: owners
        image: owners-service:latest
        ports:
        - containerPort: 8015
        env:
        - name: DATABASE_URL
          value: "postgresql://openclaw:openclaw_dev_pass@pm-db:5432/openclaw"
---
# ... add other services
```

```bash
kubectl apply -f pm-deployment.yaml
```

## GitHub Actions CI/CD

### Configuration

The repository includes `.github/workflows/ci.yml` for automated CI/CD:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install deps
        run: cd frontend && npm ci
      - name: Run lint
        run: cd frontend && npm run lint
      - name: Build
        run: cd frontend && npm run build

  e2e:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install Cypress
        run: cd frontend && npm install cypress --save-dev
      - name: Run Cypress
        run: cd frontend && npx cypress run

  deploy-staging:
    needs: e2e
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment..."
          docker-compose -f docker-compose.staging.yml build
          docker-compose -f docker-compose.staging.yml up -d
          curl -f http://localhost:8000/health || exit 1
```

### Setup GitHub Actions

1. Push to `main` branch
2. GitHub Actions will automatically:
   - Run tests
   - Build frontend
   - Deploy to staging (if on `main`)
   - Run Cypress E2E tests
   - Rollback on failure

## Monitoring

### Health Checks

```bash
# Backend services
curl http://localhost:8015/health  # owners
curl http://localhost:8016/health  # properties
curl http://localhost:8017/health  # units
curl http://localhost:8018/health  # tenants
curl http://localhost:8019/health  # maintenance

# Kong gateway
curl http://localhost:8080/status
```

### Logs

```bash
# Docker
docker-compose -f docker-compose.staging.yml logs -f owners
docker-compose -f docker-compose.staging.yml logs -f properties
# ... etc

# Kubernetes
kubectl logs -l app=owners-service -f
```

### Prometheus Metrics

All services expose `/metrics` endpoint:

```bash
curl http://localhost:8015/metrics
curl http://localhost:8016/metrics
# ... etc
```

Add to Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: 'property-management'
    static_configs:
      - targets: ['localhost:8015', 'localhost:8016', 'localhost:8017', 'localhost:8018', 'localhost:8019']
```

## Rollback

### Docker

```bash
# Stop current version
docker-compose -f docker-compose.staging.yml down

# Restart with previous image tag
docker-compose -f docker-compose.staging.yml up -d
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/owners-service
```

## SSL/TLS (Production)

### With Nginx + Let's Encrypt

```nginx
server {
    listen 443 ssl;
    server_name pm-demo.com;

    ssl_certificate /etc/letsencrypt/live/pm-demo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pm-demo.com/privkey.pem;

    location /api/v1/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3002;
    }
}
```

---

*Last updated: 2026-02-10*
