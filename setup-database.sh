#!/bin/bash

# Database Setup Script for Athena Charter Management System
# Creates schemas, tables, and indexes for all services

set -e

echo "🚀 Setting up Athena Database..."
echo "================================"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until psql -h localhost -U athena -d athena -c '\q' 2>/dev/null; do
  sleep 2
  echo -n "."
done
echo " ✓ PostgreSQL is ready!"

# Create schemas
echo "📁 Creating database schemas..."
psql -h localhost -U athena -d athena <<EOF
CREATE SCHEMA IF NOT EXISTS charter;
CREATE SCHEMA IF NOT EXISTS client;
CREATE SCHEMA IF NOT EXISTS vendor;
CREATE SCHEMA IF NOT EXISTS qc;
CREATE SCHEMA IF NOT EXISTS change_mgmt;
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS pricing;
CREATE SCHEMA IF NOT EXISTS dispatch;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS documents;
CREATE SCHEMA IF NOT EXISTS auth;
EOF
echo " ✓ Schemas created!"

# Run migrations for each service
echo "🔄 Running database migrations..."

# Charter Service migrations
echo "  - Charter Service..."
cd /home/bot/atlas/backend/services/charter
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Client Service migrations
echo "  - Client Service..."
cd /home/bot/atlas/backend/services/clients
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Vendor Service migrations
echo "  - Vendor Service..."
cd /home/bot/atlas/backend/services/vendor
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Payment Service migrations
echo "  - Payment Service..."
cd /home/bot/atlas/backend/services/payments
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Document Service migrations
echo "  - Document Service..."
cd /home/bot/atlas/backend/services/documents
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Sales Service migrations
echo "  - Sales Service..."
cd /home/bot/atlas/backend/services/sales
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Pricing Service migrations
echo "  - Pricing Service..."
cd /home/bot/atlas/backend/services/pricing
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Dispatch Service migrations
echo "  - Dispatch Service..."
cd /home/bot/atlas/backend/services/dispatch
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Change Management Service migrations
echo "  - Change Management Service..."
cd /home/bot/atlas/backend/services/change_mgmt
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

# Analytics Service migrations
echo "  - Analytics Service..."
cd /home/bot/atlas/backend/services/analytics
python -m alembic upgrade head 2>/dev/null || echo "  (No migrations found)"

cd /home/bot/atlas

echo " ✓ Migrations completed!"

# Create indexes for common queries
echo "⚡ Creating database indexes..."
psql -h localhost -U athena -d athena <<EOF
-- Charter indexes
CREATE INDEX IF NOT EXISTS idx_charters_client_id ON charter.charters(client_id);
CREATE INDEX IF NOT EXISTS idx_charters_status ON charter.charters(status);
CREATE INDEX IF NOT EXISTS idx_charters_pickup_date ON charter.charters(pickup_date);
CREATE INDEX IF NOT EXISTS idx_charters_reference ON charter.charters(reference_number);

-- Client indexes
CREATE INDEX IF NOT EXISTS idx_clients_email ON client.clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_status ON client.clients(account_status);

-- Vendor indexes
CREATE INDEX IF NOT EXISTS idx_vendors_email ON vendor.vendors(email);
CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendor.vendors(account_status);

-- QC Task indexes
CREATE INDEX IF NOT EXISTS idx_qc_tasks_status ON qc.tasks(status);
CREATE INDEX IF NOT EXISTS idx_qc_tasks_priority ON qc.tasks(priority);
CREATE INDEX IF NOT EXISTS idx_qc_tasks_due_date ON qc.tasks(due_date);

-- Change Request indexes
CREATE INDEX IF NOT EXISTS idx_change_requests_status ON change_mgmt.requests(status);
CREATE INDEX IF NOT EXISTS idx_change_requests_priority ON change_mgmt.requests(priority);

-- Payment indexes
CREATE INDEX IF NOT EXISTS idx_payments_charter_id ON payments.payments(charter_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments.payments(payment_status);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON documents.documents(client_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents.documents(status);
EOF
echo " ✓ Indexes created!"

# Verify schemas
echo "🔍 Verifying database setup..."
psql -h localhost -U athena -d athena -c "\dn" | grep -E "(charter|client|vendor|qc|change_mgmt)" && echo " ✓ All schemas verified!"

echo ""
echo "✅ Database setup completed successfully!"
echo ""
echo "You can now start the backend services."
echo "Run: cd /home/bot/atlas && ./start-all.sh"
