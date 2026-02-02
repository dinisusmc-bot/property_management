#!/bin/bash

# E2E Test with Temperature Monitoring
# Monitors temps during Playwright test run with 10 workers

echo "=========================================="
echo "E2E TEST WITH THERMAL MONITORING"
echo "=========================================="
echo ""
echo "Starting temperature monitoring in background..."
echo ""

# Create temp log file
TEMP_LOG="/tmp/e2e_temps.log"
> $TEMP_LOG

# Monitor temperatures in background
(
  while true; do
    TEMP=$(sensors | grep "Package id 0" | awk '{print $4}' | sed 's/[^0-9.]//g')
    TIMESTAMP=$(date +%s)
    echo "$TIMESTAMP $TEMP" >> $TEMP_LOG
    sleep 2
  done
) &
MONITOR_PID=$!

echo "Temperature monitoring started (PID: $MONITOR_PID)"
echo ""
echo "Initial temperature:"
sensors | grep "Package id 0"
echo ""
echo "Current CPU frequencies:"
cat /proc/cpuinfo | grep "cpu MHz" | head -6
echo ""
echo "=========================================="
echo "Running E2E tests with 10 workers..."
echo "=========================================="
echo ""

cd /home/nick/work_area/coachway_demo/tests/e2e

# Run the tests with playwright directly (36 workers - full CPU utilization)
npx playwright test --workers=36

TEST_EXIT_CODE=$?

# Stop temperature monitoring
kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

echo ""
echo "=========================================="
echo "TEST COMPLETE - THERMAL ANALYSIS"
echo "=========================================="
echo ""

# Analyze temperature log
if [ -f "$TEMP_LOG" ]; then
    MAX_TEMP=$(cat $TEMP_LOG | awk '{print $2}' | sort -n | tail -1)
    AVG_TEMP=$(cat $TEMP_LOG | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')
    
    echo "Temperature Statistics:"
    echo "  Maximum: ${MAX_TEMP}°C"
    echo "  Average: ${AVG_TEMP}°C"
    echo ""
    
    echo "Current temperature:"
    sensors | grep "Package id 0"
    echo ""
    
    # Check if temps were safe
    MAX_TEMP_INT=${MAX_TEMP%.*}
    if [ "$MAX_TEMP_INT" -lt 70 ]; then
        echo "✓ EXCELLENT: Temps stayed under 70°C"
        echo "  CPU limit is working perfectly!"
    elif [ "$MAX_TEMP_INT" -lt 85 ]; then
        echo "✓ GOOD: Temps stayed under 85°C"
        echo "  System is stable with 10 workers"
    elif [ "$MAX_TEMP_INT" -lt 95 ]; then
        echo "⚠️  WARNING: Temps reached 85-95°C"
        echo "  Consider reducing workers or checking cooling"
    else
        echo "❌ CRITICAL: Temps exceeded 95°C"
        echo "  Reduce workers or wait for new cooler"
    fi
else
    echo "No temperature data collected"
fi

echo ""
echo "Throttle events:"
THROTTLE_COUNT=$(cat /sys/devices/system/cpu/cpu*/thermal_throttle/core_throttle_count 2>/dev/null | awk '{s+=$1} END {print s}')
echo "  Total: $THROTTLE_COUNT"

if [ "$THROTTLE_COUNT" -gt 0 ]; then
    echo "  ⚠️  CPU throttled during test!"
fi

echo ""
echo "Test exit code: $TEST_EXIT_CODE"
echo "=========================================="

exit $TEST_EXIT_CODE
