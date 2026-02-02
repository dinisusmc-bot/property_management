#!/bin/bash

# Athena Test Setup Script
# Installs all testing dependencies and runs initial smoke tests

set -e

echo "🧪 Setting up Athena Testing Framework..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if system is running
echo -e "${BLUE}Checking if Athena system is running...${NC}"
if ! curl -s http://localhost:3000 > /dev/null; then
    echo -e "${YELLOW}⚠️  Athena system is not running. Please start it first:${NC}"
    echo "./start-all.sh"
    exit 1
fi
echo -e "${GREEN}✓ System is running${NC}"
echo ""

# Install Playwright for E2E tests
echo -e "${BLUE}Installing Playwright for E2E testing...${NC}"
cd /home/Ndini/work_area/coachway_demo
npm install --save-dev @playwright/test @types/node
echo -e "${YELLOW}Installing browsers (without system dependencies)...${NC}"
npx playwright install chromium firefox webkit 2>/dev/null || echo -e "${YELLOW}⚠️  Browser install skipped - will use system browsers${NC}"
echo -e "${GREEN}✓ Playwright installed${NC}"
echo ""

# Install Python test dependencies
echo -e "${BLUE}Installing Python test dependencies...${NC}"
cd /home/Ndini/work_area/coachway_demo
pip install -r tests/requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Create test results directories
echo -e "${BLUE}Creating test result directories...${NC}"
mkdir -p test-results
mkdir -p coverage
mkdir -p playwright-report
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Run smoke tests
echo -e "${BLUE}Running smoke tests...${NC}"
echo ""

# API smoke tests
echo "Running API smoke tests..."
pytest tests/api/test_smoke.py -v -m smoke

# E2E smoke tests (login only)
echo ""
echo "Running E2E smoke tests..."
npx playwright test tests/e2e/tests/auth/login.spec.ts --project=chromium --workers=1

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Test setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Available test commands:"
echo ""
echo "  ${BLUE}# Run all API tests${NC}"
echo "  pytest tests/api/ -v"
echo ""
echo "  ${BLUE}# Run all E2E tests${NC}"
echo "  npx playwright test"
echo ""
echo "  ${BLUE}# Run specific test file${NC}"
echo "  npx playwright test tests/e2e/tests/charters/charter-list.spec.ts"
echo ""
echo "  ${BLUE}# Run tests in headed mode (see browser)${NC}"
echo "  npx playwright test --headed"
echo ""
echo "  ${BLUE}# Run tests with specific browser${NC}"
echo "  npx playwright test --project=firefox"
echo ""
echo "  ${BLUE}# Generate test report${NC}"
echo "  npx playwright show-report"
echo ""
echo "  ${BLUE}# Run API tests with coverage${NC}"
echo "  pytest tests/api/ -v --cov --cov-report=html"
echo ""
echo "  ${BLUE}# Run integration tests${NC}"
echo "  pytest tests/integration/ -v"
echo ""
echo "  ${BLUE}# Run load tests${NC}"
echo "  locust -f tests/performance/locustfile.py --host=http://localhost:8080"
echo ""
