#!/bin/bash

# Phase 1 E2E Test Runner
# Runs all Phase 1 feature tests with proper setup validation

set -e  # Exit on error

# Default max failures (can be overridden with --max-failures=N)
MAX_FAILURES=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  Phase 1 E2E Test Suite Runner${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Change to e2e test directory
cd "$(dirname "$0")"
TEST_DIR=$(pwd)

# Check if we're in the right directory
if [ ! -f "playwright.config.ts" ]; then
    echo -e "${RED}Error: playwright.config.ts not found${NC}"
    echo "Please run this script from the tests/e2e directory"
    exit 1
fi

# Function to check if a service is running
check_service() {
    local name=$1
    local url=$2
    local port=$3
    
    echo -n "Checking $name (port $port)... "
    
    if curl -s -f -o /dev/null "$url"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not responding${NC}"
        return 1
    fi
}

# Function to check if a port is listening
check_port() {
    local port=$1
    
    if command -v lsof >/dev/null 2>&1; then
        lsof -i:$port >/dev/null 2>&1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep ":$port " >/dev/null 2>&1
    else
        # Fallback: try to connect
        nc -z localhost $port >/dev/null 2>&1
    fi
}

echo -e "${YELLOW}Step 1: Validating Prerequisites${NC}"
echo "=================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js installed:${NC} $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm installed:${NC} $(npm --version)"

# Check if Playwright is installed
if [ ! -d "node_modules/@playwright" ]; then
    echo -e "${YELLOW}Installing Playwright dependencies...${NC}"
    npm install
fi
echo -e "${GREEN}✓ Playwright dependencies installed${NC}"

echo ""
echo -e "${YELLOW}Step 2: Checking Backend Services${NC}"
echo "=================================="
echo ""

SERVICES_OK=true

# Check Kong Gateway (Port 8080)
if ! check_service "Kong Gateway" "http://localhost:8080/api/v1/auth/health" "8080"; then
    SERVICES_OK=false
fi

# Check Auth Service via Kong
if ! check_service "Auth Service" "http://localhost:8080/api/v1/auth/health" "8080"; then
    SERVICES_OK=false
fi

# Check Charter Service via Kong
if ! check_service "Charter Service" "http://localhost:8080/api/v1/vehicles" "8080"; then
    SERVICES_OK=false
fi

# Check Pricing Service via Kong
if ! check_service "Pricing Service" "http://localhost:8080/api/v1/pricing/health" "8080"; then
    SERVICES_OK=false
fi

# Check Sales Service via Kong
if ! check_service "Sales Service" "http://localhost:8080/api/v1/sales/health" "8080"; then
    SERVICES_OK=false
fi

if [ "$SERVICES_OK" = false ]; then
    echo ""
    echo -e "${RED}Error: Some backend services are not running${NC}"
    echo ""
    echo "Ensure Kong and all backend services are running (docker-compose up -d)."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Step 3: Checking Frontend${NC}"
echo "=================================="
echo ""

# Check if frontend is running (Port 3000)
if check_service "Frontend" "http://localhost:3000" "3000"; then
    FRONTEND_OK=true
else
    FRONTEND_OK=false
    echo ""
    echo -e "${RED}Error: Frontend is not running on port 3000${NC}"
    echo ""
    echo "To start frontend:"
    echo "  cd frontend && npm run dev"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Step 4: Running Tests${NC}"
echo "=================================="
echo ""

# Parse command line arguments
TEST_ARGS="$@"

# Check for --max-failures flag
for arg in "$@"; do
    if [[ $arg == --max-failures=* ]]; then
        MAX_FAILURES="${arg#*=}"
        TEST_ARGS=$(echo "$TEST_ARGS" | sed "s|--max-failures=$MAX_FAILURES||g")
    fi
done

# Default to running all Phase 1 tests
if [ -z "$TEST_ARGS" ] || [ "$TEST_ARGS" = " " ]; then
    TEST_ARGS="tests/leads tests/quotes tests/dashboard tests/templates"
    echo "Running all Phase 1 tests (will stop after $MAX_FAILURES failures)..."
else
    echo "Running tests with args: $TEST_ARGS (will stop after $MAX_FAILURES failures)..."
fi

echo ""

# Run Playwright tests with max failures
MAX_FAILURES=$MAX_FAILURES npx playwright test --max-failures=$MAX_FAILURES $TEST_ARGS

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo -e "${YELLOW}Step 5: Test Results${NC}"
echo "=================================="
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "To view detailed report:"
    echo "  npx playwright show-report"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "To view test report:"
    echo "  npx playwright show-report"
    echo ""
    echo "To view traces for failed tests:"
    echo "  npx playwright show-trace test-results/[test-name]/trace.zip"
    echo ""
    echo "To run failed tests in debug mode:"
    echo "  npx playwright test --debug"
fi

echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Show test summary from playwright output
if [ -f "test-results/results.json" ]; then
    echo "Detailed results available in test-results/"
fi

exit $TEST_EXIT_CODE
