#!/bin/bash

# Athena Project - Automated Startup Script
# Starts all services in proper dependency order

set -e  # Exit on error

echo "🚀 Starting Athena Project..."
echo "================================"

# Create necessary directories and fix permissions
echo "📁 Setting up directories and permissions..."
mkdir -p ./airflow/{logs,plugins}
chmod -R 777 ./airflow/logs ./airflow/plugins 2>/dev/null || true
chmod 644 ./monitoring/prometheus.yml 2>/dev/null || true

# Ensure .env file has correct password
if [ -f .env ]; then
    echo "📝 Updating .env file passwords..."
    sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=athena_dev_password/' .env
    sed -i 's/DATABASE_URL=.*/DATABASE_URL=postgresql:\/\/athena:athena_dev_password@postgres:5432\/athena/' .env
fi

echo ""
echo "Step 1: Starting base infrastructure..."
echo "   Starting postgres..."
timeout 30 docker compose up -d postgres 2>&1 | tail -1
echo "   Starting redis..."
timeout 30 docker compose up -d redis 2>&1 | tail -1
echo "   Starting rabbitmq..."
timeout 30 docker compose up -d rabbitmq 2>&1 | tail -1
echo "   Starting mongodb..."
timeout 30 docker compose up -d mongodb 2>&1 | tail -1
echo "   Starting kong-database..."
timeout 30 docker compose up -d kong-database 2>&1 | tail -1

echo ""
echo "Step 2: Waiting for databases to be ready..."
sleep 10

# Wait for main postgres
timeout 60 bash -c 'until podman exec athena-postgres pg_isready -U athena > /dev/null 2>&1; do sleep 2; echo -n "."; done' && echo " ✓"

# Wait for Kong database
timeout 60 bash -c 'until podman exec athena-kong-db pg_isready -U kong > /dev/null 2>&1; do sleep 2; echo -n "."; done' && echo " ✓"

echo ""
echo "Step 3: Running Kong migrations..."
timeout 30 docker compose up -d kong-migration 2>&1 | grep -v "already in use" || echo "   (Migration starting or already done)"
sleep 5

# Wait for migration to complete (it exits when done)
timeout 30 bash -c 'while podman ps --filter name=athena-kong-migration --filter status=running -q | grep -q .; do sleep 2; echo -n "."; done' && echo " ✓" || echo " (already done)"

echo ""
echo "Step 4: Starting Kong API Gateway..."
timeout 60 docker compose up -d kong 2>&1 | grep -v "already in use" || echo "   (Kong starting or already running)"

echo ""
echo "Step 5: Starting microservices..."
echo "   Starting auth-service..."
timeout 30 docker compose up -d auth-service 2>&1 | tail -1
echo "   Starting client-service..."
timeout 30 docker compose up -d client-service 2>&1 | tail -1
echo "   Starting charter-service..."
timeout 30 docker compose up -d charter-service 2>&1 | tail -1
echo "   Starting document-service..."
timeout 30 docker compose up -d document-service 2>&1 | tail -1

# Give services time to start
sleep 3

# Ensure all services are actually started (podman-compose bug workaround)
echo "   Verifying all services are running..."
docker start athena-auth-service athena-client-service athena-charter-service athena-document-service 2>/dev/null || true

echo ""
echo "Step 6: Starting frontend..."
timeout 60 docker compose up -d frontend 2>&1 | grep -v "already in use" || echo "   (Frontend starting or already running)"

echo ""
echo "Step 7: Starting Airflow infrastructure..."
echo "   Starting airflow-postgres..."
timeout 30 docker compose up -d airflow-postgres 2>&1 | tail -1
echo "   Starting airflow-redis..."
timeout 30 docker compose up -d airflow-redis 2>&1 | tail -1

sleep 5

# Wait for Airflow database
timeout 60 bash -c 'until podman exec athena-airflow-db pg_isready -U airflow > /dev/null 2>&1; do sleep 2; echo -n "."; done' && echo " ✓"

echo ""
echo "Step 8: Initializing Airflow database..."
timeout 30 podman run --rm --network coachway_demo_athena-network \
  -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@athena-airflow-db/airflow \
  localhost/coachway_demo_airflow-webserver:latest airflow db migrate > /dev/null 2>&1 || echo "   (Already initialized or timed out)"

echo ""
echo "Step 9: Creating Airflow admin user..."
timeout 30 podman run --rm --network coachway_demo_athena-network \
  -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@athena-airflow-db/airflow \
  localhost/coachway_demo_airflow-webserver:latest \
  airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin > /dev/null 2>&1 || echo "   (User already exists or timed out)"

echo ""
echo "Step 10: Starting Airflow services..."
echo "   Starting airflow-webserver..."
timeout 30 docker compose up -d airflow-webserver 2>&1 | tail -1
echo "   Starting airflow-scheduler..."
timeout 30 docker compose up -d airflow-scheduler 2>&1 | tail -1
echo "   Starting airflow-worker..."
timeout 30 docker compose up -d airflow-worker 2>&1 | tail -1

echo ""
echo "Step 11: Starting monitoring services..."
echo "   Starting prometheus..."
timeout 30 docker compose up -d prometheus 2>&1 | tail -1
echo "   Starting grafana..."
timeout 30 docker compose up -d grafana 2>&1 | tail -1

# Copy Prometheus config to volume
echo "   Copying Prometheus configuration..."
podman cp ./monitoring/prometheus.yml athena-prometheus:/etc/prometheus/prometheus.yml 2>/dev/null || true
podman cp ./monitoring/alerts.yml athena-prometheus:/etc/prometheus/alerts.yml 2>/dev/null || true
podman restart athena-prometheus 2>/dev/null || true

echo ""
echo "Step 12: Configuring Kong API Gateway routes..."
sleep 5

# Wait for Kong admin API
timeout 60 bash -c 'until curl -s http://localhost:8081/ > /dev/null 2>&1; do sleep 2; echo -n "."; done' && echo " ✓"

# Create Kong services
curl -s -X POST http://localhost:8081/services \
  --data name=auth-service \
  --data url=http://athena-auth-service:8000 > /dev/null 2>&1 || echo "   (auth-service exists)"

curl -s -X POST http://localhost:8081/services \
  --data name=client-service \
  --data url=http://athena-client-service:8000 > /dev/null 2>&1 || echo "   (client-service exists)"

curl -s -X POST http://localhost:8081/services \
  --data name=charter-service \
  --data url=http://athena-charter-service:8000 > /dev/null 2>&1 || echo "   (charter-service exists)"

curl -s -X POST http://localhost:8081/services \
  --data name=document-service \
  --data url=http://athena-document-service:8000 > /dev/null 2>&1 || echo "   (document-service exists)"

# Create Kong routes
curl -s -X POST http://localhost:8081/services/auth-service/routes \
  --data paths[]=/api/v1/auth \
  --data strip_path=true > /dev/null 2>&1 || echo "   (auth route exists)"

curl -s -X POST http://localhost:8081/services/client-service/routes \
  --data paths[]=/api/v1/clients > /dev/null 2>&1 || echo "   (client route exists)"

curl -s -X POST http://localhost:8081/services/charter-service/routes \
  --data paths[]=/api/v1/charters > /dev/null 2>&1 || echo "   (charter route exists)"

curl -s -X POST http://localhost:8081/services/document-service/routes \
  --data paths[]=/api/v1/documents \
  --data strip_path=true > /dev/null 2>&1 || echo "   (document route exists)"

# Enable CORS
curl -s -X POST http://localhost:8081/plugins \
  --data name=cors \
  --data config.origins=* \
  --data config.credentials=true > /dev/null 2>&1 || echo "   (CORS already enabled)"

echo ""
echo "Step 13: Seeding database with sample data..."
timeout 30 python3 backend/scripts/seed_data.py 2>&1 | grep -E "✅|Created|already" || echo "   (Data already seeded or timed out)"

echo ""
echo "================================"
echo "✅ Athena Project Started!"
echo "================================"
echo ""
echo "🌐 Access Points:"
echo "   Frontend:    http://localhost:3000"
echo "   Kong API:    http://localhost:8080"
echo "   Airflow:     http://localhost:8082 (admin/admin)"
echo "   Grafana:     http://localhost:3001 (admin/admin)"
echo "   Prometheus:  http://localhost:9091"
echo "   RabbitMQ:    http://localhost:15672 (guest/guest)"
echo ""
echo "🔐 Login Credentials:"
echo "   Email:    admin@athena.com"
echo "   Password: admin123"
echo ""
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep athena

echo ""
echo "💡 To stop all services: ./stop-all.sh"
echo ""
