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

# Check auth service
if curl -s -f http://localhost:8000/docs >/dev/null 2>&1; then
    echo "✓ Auth service (port 8000) is running"
else
    echo "✗ Auth service not responding"
    exit 1
fi

# Check charter service  
if curl -s -f http://localhost:8001/docs >/dev/null 2>&1; then
    echo "✓ Charter service (port 8001) is running"
else
    echo "✗ Charter service not responding"
    exit 1
fi

# Check client service
if curl -s -f http://localhost:8002/docs >/dev/null 2>&1; then
    echo "✓ Client service (port 8002) is running"
else
    echo "✗ Client service not responding"
    exit 1
fi

# Check document service
if curl -s -f http://localhost:8003/docs >/dev/null 2>&1; then
    echo "✓ Document service (port 8003) is running"
else
    echo "✗ Document service not responding"
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
