#!/bin/bash

# Athena Project - Shutdown Script
# This script stops all services gracefully

echo "🛑 Stopping Athena Project..."
echo "================================"

echo ""
echo "Stopping all containers..."
docker compose down

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "💡 To start again, run: ./start-all.sh"
echo ""
