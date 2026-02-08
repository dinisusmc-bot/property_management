#!/bin/bash

# Quick Test Commands - Phase 1
# Convenient shortcuts for common test scenarios

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")"

case "$1" in
  "leads")
    echo -e "${BLUE}Running Lead Management tests...${NC}"
    npx playwright test tests/leads/test_lead_management.spec.ts "$@"
    ;;
  
  "quotes")
    echo -e "${BLUE}Running Quote Builder tests...${NC}"
    npx playwright test tests/quotes/test_quote_builder.spec.ts "$@"
    ;;
  
  "dashboard")
    echo -e "${BLUE}Running Dashboard tests...${NC}"
    npx playwright test tests/dashboard/test_agent_dashboard.spec.ts "$@"
    ;;
  
  "templates")
    echo -e "${BLUE}Running Templates & Cloning tests...${NC}"
    npx playwright test tests/templates/test_charter_templates.spec.ts "$@"
    ;;
  
  "backend")
    echo -e "${BLUE}Running Backend Integration tests only...${NC}"
    npx playwright test -g "Backend" "$@"
    ;;
  
  "ui")
    echo -e "${BLUE}Running UI tests only (skipping backend tests)...${NC}"
    npx playwright test --grep-invert "Backend" tests/leads tests/quotes tests/dashboard tests/templates "$@"
    ;;
  
  "headed")
    echo -e "${BLUE}Running tests in headed mode (visible browser)...${NC}"
    npx playwright test tests/leads tests/quotes tests/dashboard tests/templates --headed
    ;;
  
  "debug")
    echo -e "${BLUE}Running tests in debug mode...${NC}"
    npx playwright test tests/leads tests/quotes tests/dashboard tests/templates --debug
    ;;
  
  "report")
    echo -e "${BLUE}Opening test report...${NC}"
    npx playwright show-report
    ;;
  
  "ui-mode")
    echo -e "${BLUE}Opening Playwright UI Mode...${NC}"
    npx playwright test --ui
    ;;
  
  "smoke")
    echo -e "${BLUE}Running smoke tests (quick validation)...${NC}"
    npx playwright test -g "should display" tests/leads tests/quotes tests/dashboard tests/templates
    ;;
  
  "help"|"-h"|"--help")
    echo -e "${GREEN}Phase 1 Test Commands${NC}"
    echo ""
    echo "Usage: ./quick_test.sh [command]"
    echo ""
    echo "Commands:"
    echo "  leads       - Run Lead Management tests only"
    echo "  quotes      - Run Quote Builder tests only"
    echo "  dashboard   - Run Dashboard tests only"
    echo "  templates   - Run Templates & Cloning tests only"
    echo "  backend     - Run Backend Integration tests only"
    echo "  ui          - Run UI tests only (skip backend)"
    echo "  headed      - Run tests with visible browser"
    echo "  debug       - Run tests in debug mode"
    echo "  report      - Open last test report"
    echo "  ui-mode     - Open Playwright UI Mode"
    echo "  smoke       - Run quick smoke tests"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./quick_test.sh leads"
    echo "  ./quick_test.sh dashboard --headed"
    echo "  ./quick_test.sh backend"
    echo ""
    ;;
  
  *)
    echo -e "${BLUE}Running ALL Phase 1 tests...${NC}"
    npx playwright test tests/leads tests/quotes tests/dashboard tests/templates "$@"
    ;;
esac
