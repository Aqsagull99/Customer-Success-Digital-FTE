#!/bin/bash
# =============================================================================
# Load Test Runner - Customer Success FTE
# Runs load test and generates a results report
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
HOST="${1:-http://localhost:8000}"
USERS="${2:-20}"
SPAWN_RATE="${3:-5}"
DURATION="${4:-2m}"

echo "============================================"
echo "  Customer Success FTE - Load Test"
echo "============================================"
echo "Host:        $HOST"
echo "Users:       $USERS"
echo "Spawn Rate:  $SPAWN_RATE/s"
echo "Duration:    $DURATION"
echo "============================================"

# Check API is up
echo ""
echo "[1/4] Checking API health..."
HEALTH=$(curl -s "$HOST/health" 2>/dev/null || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  API is healthy"
else
    echo "  ERROR: API is not responding at $HOST"
    echo "  Make sure docker-compose is running: docker-compose up -d"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Run load test
echo ""
echo "[2/4] Running load test ($DURATION with $USERS users)..."
cd "$SCRIPT_DIR/.."

locust -f tests/load_test.py \
    --host="$HOST" \
    --headless \
    -u "$USERS" \
    -r "$SPAWN_RATE" \
    --run-time "$DURATION" \
    --csv="$RESULTS_DIR/load_test_${TIMESTAMP}" \
    --html="$RESULTS_DIR/load_test_${TIMESTAMP}.html" \
    2>&1 | tail -20

# Check health after load test
echo ""
echo "[3/4] Post-test health check..."
POST_HEALTH=$(curl -s "$HOST/health" 2>/dev/null || echo "FAILED")
if echo "$POST_HEALTH" | grep -q "healthy"; then
    echo "  API is still healthy after load test"
else
    echo "  WARNING: API health degraded after load test"
fi

# Generate summary report
echo ""
echo "[4/4] Generating report..."

REPORT_FILE="$RESULTS_DIR/load_test_report_${TIMESTAMP}.md"
STATS_FILE="$RESULTS_DIR/load_test_${TIMESTAMP}_stats.csv"

cat > "$REPORT_FILE" << REPORT_EOF
# Load Test Report - Customer Success FTE

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Duration:** $DURATION
**Concurrent Users:** $USERS
**Spawn Rate:** $SPAWN_RATE/s
**Target:** $HOST

## System Health
- **Pre-test:** Healthy
- **Post-test:** $(echo "$POST_HEALTH" | grep -q "healthy" && echo "Healthy" || echo "Degraded")

## Results Summary

REPORT_EOF

# Parse CSV stats if available
if [ -f "$STATS_FILE" ]; then
    echo "| Endpoint | Requests | Failures | Avg (ms) | P95 (ms) | P99 (ms) |" >> "$REPORT_FILE"
    echo "|----------|----------|----------|----------|----------|----------|" >> "$REPORT_FILE"
    tail -n +2 "$STATS_FILE" | while IFS=',' read -r type name reqs fails avg_resp min_resp max_resp median avg_size p50 p66 p75 p80 p90 p95 p98 p99 rest; do
        if [ -n "$name" ] && [ "$name" != "\"Aggregated\"" ]; then
            clean_name=$(echo "$name" | tr -d '"')
            echo "| $clean_name | $reqs | $fails | $avg_resp | $p95 | $p99 |" >> "$REPORT_FILE"
        fi
    done

    # Add aggregated stats
    AGGREGATED=$(tail -1 "$STATS_FILE")
    if echo "$AGGREGATED" | grep -q "Aggregated"; then
        echo "" >> "$REPORT_FILE"
        echo "### Aggregated" >> "$REPORT_FILE"
        AGG_REQS=$(echo "$AGGREGATED" | cut -d',' -f3)
        AGG_FAILS=$(echo "$AGGREGATED" | cut -d',' -f4)
        AGG_AVG=$(echo "$AGGREGATED" | cut -d',' -f5)
        echo "- **Total Requests:** $AGG_REQS" >> "$REPORT_FILE"
        echo "- **Total Failures:** $AGG_FAILS" >> "$REPORT_FILE"
        echo "- **Average Response Time:** ${AGG_AVG}ms" >> "$REPORT_FILE"
    fi
fi

cat >> "$REPORT_FILE" << REPORT_EOF2

## 24/7 Readiness Criteria

| Criteria | Target | Status |
|----------|--------|--------|
| Uptime during test | > 99.9% | $(echo "$POST_HEALTH" | grep -q "healthy" && echo "PASS" || echo "FAIL") |
| P95 latency | < 3 seconds | Check results above |
| No message loss | 0 lost | Check failure count |
| Health after load | Healthy | $(echo "$POST_HEALTH" | grep -q "healthy" && echo "PASS" || echo "FAIL") |

## Files Generated
- CSV Stats: \`load_test_${TIMESTAMP}_stats.csv\`
- HTML Report: \`load_test_${TIMESTAMP}.html\`
- This Report: \`load_test_report_${TIMESTAMP}.md\`
REPORT_EOF2

echo ""
echo "============================================"
echo "  Load Test Complete!"
echo "============================================"
echo "Report:  $REPORT_FILE"
echo "HTML:    $RESULTS_DIR/load_test_${TIMESTAMP}.html"
echo "CSV:     $STATS_FILE"
echo "============================================"
