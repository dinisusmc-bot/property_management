#!/bin/bash
# Pre-flight checks before running e2e tests

echo "🔍 Running pre-flight checks..."
echo ""

# Check frontend
if curl -s -f http://localhost:3000 >/dev/null 2>&1; then
    echo "✓ Frontend (port 3000) is running"
else
    echo "✗ Frontend not responding on port 3000"
    exit 1
fi

# Check Kong gateway
if curl -s -f http://localhost:8080 >/dev/null 2>&1; then
    echo "✓ Kong gateway (port 8080) is running"
else
    echo "✗ Kong gateway not responding"
    exit 1
fi

# Check auth service via Kong
if curl -s -f http://localhost:8080/api/v1/auth/health >/dev/null 2>&1; then
    echo "✓ Auth service is running via Kong"
else
    echo "✗ Auth service not responding via Kong"
    exit 1
fi

# Check charter service via Kong
if curl -s -f http://localhost:8080/api/v1/charters/health >/dev/null 2>&1; then
    echo "✓ Charter service is running via Kong"
else
    echo "✗ Charter service not responding via Kong"
    exit 1
fi

# Check client service via Kong
if curl -s -f http://localhost:8080/api/v1/clients/health >/dev/null 2>&1; then
    echo "✓ Client service is running via Kong"
else
    echo "✗ Client service not responding via Kong"
    exit 1
fi

# Check sales service via Kong
if curl -s -f http://localhost:8080/api/v1/sales/health >/dev/null 2>&1; then
    echo "✓ Sales service is running via Kong"
else
    echo "✗ Sales service not responding via Kong"
    exit 1
fi

# Check pricing service via Kong
if curl -s -f http://localhost:8080/api/v1/pricing/health >/dev/null 2>&1; then
    echo "✓ Pricing service is running via Kong"
else
    echo "✗ Pricing service not responding via Kong"
    exit 1
fi

# Check database
if docker exec athena-postgres pg_isready >/dev/null 2>&1; then
    echo "✓ PostgreSQL database is ready"
else
    echo "✗ Database not ready"
    exit 1
fi

echo ""
echo "✓ All services are running and ready!"
echo ""
