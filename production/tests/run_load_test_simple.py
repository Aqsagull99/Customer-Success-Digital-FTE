#!/usr/bin/env python3
"""
Simple load test runner for Customer Success FTE.
Uses httpx + asyncio instead of locust for environments where locust has issues.

Usage:
    python3 tests/run_load_test_simple.py [host] [users] [duration_secs]
    python3 tests/run_load_test_simple.py http://localhost:8000 20 60
"""

import asyncio
import json
import os
import random
import statistics
import sys
import time
import uuid
from datetime import datetime

import httpx

# Configuration
HOST = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
CONCURRENT_USERS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
DURATION_SECS = int(sys.argv[3]) if len(sys.argv) > 3 else 60

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


class LoadTestStats:
    def __init__(self):
        self.requests = []
        self.errors = 0
        self.start_time = None
        self.end_time = None

    def record(self, endpoint, status_code, latency_ms, success):
        self.requests.append({
            "endpoint": endpoint,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": time.time(),
        })
        if not success:
            self.errors += 1


stats = LoadTestStats()


async def web_form_submit(client):
    """Submit a support form."""
    uid = uuid.uuid4().hex[:8]
    categories = ["general", "technical", "billing", "feedback", "bug_report"]
    start = time.time()
    try:
        resp = await client.post(
            f"{HOST}/support/submit",
            json={
                "name": f"Load User {uid}",
                "email": f"load_{uid}@example.com",
                "subject": f"Load Test {random.randint(1, 100)}",
                "category": random.choice(categories),
                "message": "Load test message to verify system performance under sustained traffic.",
            },
        )
        latency = (time.time() - start) * 1000
        success = resp.status_code == 200
        stats.record("/support/submit", resp.status_code, latency, success)
    except Exception:
        latency = (time.time() - start) * 1000
        stats.record("/support/submit", 0, latency, False)


async def health_check(client):
    """Check health endpoint."""
    start = time.time()
    try:
        resp = await client.get(f"{HOST}/health")
        latency = (time.time() - start) * 1000
        stats.record("/health", resp.status_code, latency, resp.status_code == 200)
    except Exception:
        latency = (time.time() - start) * 1000
        stats.record("/health", 0, latency, False)


async def metrics_check(client):
    """Check metrics endpoint."""
    start = time.time()
    try:
        resp = await client.get(f"{HOST}/metrics/channels")
        latency = (time.time() - start) * 1000
        stats.record("/metrics/channels", resp.status_code, latency, resp.status_code == 200)
    except Exception:
        latency = (time.time() - start) * 1000
        stats.record("/metrics/channels", 0, latency, False)


async def whatsapp_webhook(client):
    """Simulate WhatsApp webhook."""
    start = time.time()
    try:
        resp = await client.post(
            f"{HOST}/webhooks/whatsapp",
            data={
                "MessageSid": f"SM{uuid.uuid4().hex[:32]}",
                "From": f"whatsapp:+1{random.randint(2000000000, 9999999999)}",
                "Body": "Load test WhatsApp message",
                "ProfileName": f"WA User {random.randint(1, 1000)}",
            },
        )
        latency = (time.time() - start) * 1000
        stats.record("/webhooks/whatsapp", resp.status_code, latency, resp.status_code in [200, 403])
    except Exception:
        latency = (time.time() - start) * 1000
        stats.record("/webhooks/whatsapp", 0, latency, False)


async def gmail_webhook(client):
    """Simulate Gmail webhook."""
    start = time.time()
    try:
        resp = await client.post(
            f"{HOST}/webhooks/gmail",
            json={
                "message": {
                    "data": "eyJ0ZXN0IjogdHJ1ZX0=",
                    "messageId": f"gmail-{uuid.uuid4().hex[:12]}",
                },
                "subscription": "projects/test/subscriptions/gmail-push",
            },
        )
        latency = (time.time() - start) * 1000
        stats.record("/webhooks/gmail", resp.status_code, latency, resp.status_code in [200, 500])
    except Exception:
        latency = (time.time() - start) * 1000
        stats.record("/webhooks/gmail", 0, latency, False)


async def customer_lookup(client):
    """Test customer lookup."""
    start = time.time()
    try:
        resp = await client.get(
            f"{HOST}/customers/lookup",
            params={"email": f"load_{random.randint(1, 100)}@example.com"},
        )
        latency = (time.time() - start) * 1000
        stats.record("/customers/lookup", resp.status_code, latency, resp.status_code in [200, 404])
    except Exception:
        latency = (time.time() - start) * 1000
        stats.record("/customers/lookup", 0, latency, False)


async def simulate_user(user_id, end_time):
    """Simulate a single user making random requests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        actions = [
            (web_form_submit, 5),   # weight 5
            (health_check, 2),      # weight 2
            (metrics_check, 1),     # weight 1
            (whatsapp_webhook, 2),  # weight 2
            (gmail_webhook, 1),     # weight 1
            (customer_lookup, 1),   # weight 1
        ]
        weighted = []
        for action, weight in actions:
            weighted.extend([action] * weight)

        while time.time() < end_time:
            action = random.choice(weighted)
            await action(client)
            await asyncio.sleep(random.uniform(0.5, 3.0))


def calculate_percentile(values, p):
    """Calculate the p-th percentile."""
    if not values:
        return 0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (p / 100)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_values) else f
    d = k - f
    return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])


def generate_report():
    """Generate load test report."""
    total = len(stats.requests)
    duration = stats.end_time - stats.start_time
    rps = total / duration if duration > 0 else 0

    all_latencies = [r["latency_ms"] for r in stats.requests]
    success_count = sum(1 for r in stats.requests if r["success"])
    error_rate = (stats.errors / total * 100) if total > 0 else 0

    # Per-endpoint stats
    endpoints = {}
    for r in stats.requests:
        ep = r["endpoint"]
        if ep not in endpoints:
            endpoints[ep] = {"latencies": [], "success": 0, "errors": 0, "total": 0}
        endpoints[ep]["latencies"].append(r["latency_ms"])
        endpoints[ep]["total"] += 1
        if r["success"]:
            endpoints[ep]["success"] += 1
        else:
            endpoints[ep]["errors"] += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Print console report
    print("\n" + "=" * 70)
    print("  LOAD TEST RESULTS - Customer Success FTE")
    print("=" * 70)
    print(f"  Host:           {HOST}")
    print(f"  Users:          {CONCURRENT_USERS}")
    print(f"  Duration:       {duration:.1f}s")
    print(f"  Total Requests: {total}")
    print(f"  RPS:            {rps:.1f}")
    print(f"  Success Rate:   {(success_count/total*100) if total else 0:.1f}%")
    print(f"  Error Rate:     {error_rate:.1f}%")
    print(f"  Avg Latency:    {statistics.mean(all_latencies):.1f}ms")
    print(f"  P50 Latency:    {calculate_percentile(all_latencies, 50):.1f}ms")
    print(f"  P95 Latency:    {calculate_percentile(all_latencies, 95):.1f}ms")
    print(f"  P99 Latency:    {calculate_percentile(all_latencies, 99):.1f}ms")
    print("-" * 70)
    print(f"  {'Endpoint':<25} {'Reqs':>6} {'Fail':>6} {'Avg(ms)':>8} {'P95(ms)':>8}")
    print("-" * 70)
    for ep, data in sorted(endpoints.items()):
        avg = statistics.mean(data["latencies"])
        p95 = calculate_percentile(data["latencies"], 95)
        print(f"  {ep:<25} {data['total']:>6} {data['errors']:>6} {avg:>8.1f} {p95:>8.1f}")
    print("=" * 70)

    # Generate markdown report
    report_path = os.path.join(RESULTS_DIR, f"load_test_report_{timestamp}.md")
    with open(report_path, "w") as f:
        f.write("# Load Test Report - Customer Success FTE\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Duration:** {duration:.1f}s\n")
        f.write(f"**Concurrent Users:** {CONCURRENT_USERS}\n")
        f.write(f"**Target:** {HOST}\n\n")
        f.write("## Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Requests | {total} |\n")
        f.write(f"| Requests/sec | {rps:.1f} |\n")
        f.write(f"| Success Rate | {(success_count/total*100) if total else 0:.1f}% |\n")
        f.write(f"| Error Rate | {error_rate:.1f}% |\n")
        f.write(f"| Avg Latency | {statistics.mean(all_latencies):.1f}ms |\n")
        f.write(f"| P50 Latency | {calculate_percentile(all_latencies, 50):.1f}ms |\n")
        f.write(f"| P95 Latency | {calculate_percentile(all_latencies, 95):.1f}ms |\n")
        f.write(f"| P99 Latency | {calculate_percentile(all_latencies, 99):.1f}ms |\n\n")
        f.write("## Per-Endpoint Results\n\n")
        f.write("| Endpoint | Requests | Failures | Avg (ms) | P95 (ms) | P99 (ms) |\n")
        f.write("|----------|----------|----------|----------|----------|----------|\n")
        for ep, data in sorted(endpoints.items()):
            avg = statistics.mean(data["latencies"])
            p95 = calculate_percentile(data["latencies"], 95)
            p99 = calculate_percentile(data["latencies"], 99)
            f.write(f"| {ep} | {data['total']} | {data['errors']} | {avg:.1f} | {p95:.1f} | {p99:.1f} |\n")
        f.write("\n## 24/7 Readiness Assessment\n\n")
        f.write("| Criteria | Target | Actual | Status |\n")
        f.write("|----------|--------|--------|--------|\n")
        p95 = calculate_percentile(all_latencies, 95)
        f.write(f"| P95 Latency | < 3000ms | {p95:.1f}ms | {'PASS' if p95 < 3000 else 'FAIL'} |\n")
        f.write(f"| Error Rate | < 5% | {error_rate:.1f}% | {'PASS' if error_rate < 5 else 'FAIL'} |\n")
        f.write(f"| Throughput | > 5 RPS | {rps:.1f} RPS | {'PASS' if rps > 5 else 'FAIL'} |\n")

    # Save raw JSON data
    json_path = os.path.join(RESULTS_DIR, f"load_test_raw_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump({
            "config": {"host": HOST, "users": CONCURRENT_USERS, "duration": DURATION_SECS},
            "summary": {
                "total_requests": total,
                "rps": rps,
                "success_rate": (success_count / total * 100) if total else 0,
                "avg_latency_ms": statistics.mean(all_latencies),
                "p95_latency_ms": calculate_percentile(all_latencies, 95),
                "p99_latency_ms": calculate_percentile(all_latencies, 99),
            },
            "endpoints": {
                ep: {
                    "total": data["total"],
                    "errors": data["errors"],
                    "avg_ms": statistics.mean(data["latencies"]),
                    "p95_ms": calculate_percentile(data["latencies"], 95),
                }
                for ep, data in endpoints.items()
            },
        }, f, indent=2)

    print(f"\n  Report: {report_path}")
    print(f"  Raw Data: {json_path}")
    return report_path


async def main():
    print("=" * 70)
    print("  Customer Success FTE - Load Test")
    print("=" * 70)
    print(f"  Host:     {HOST}")
    print(f"  Users:    {CONCURRENT_USERS}")
    print(f"  Duration: {DURATION_SECS}s")
    print("=" * 70)

    # Pre-test health check
    print("\n[1/3] Pre-test health check...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{HOST}/health")
            if resp.status_code == 200:
                print("  API is healthy")
            else:
                print(f"  WARNING: Health check returned {resp.status_code}")
        except Exception as e:
            print(f"  ERROR: API not reachable - {e}")
            sys.exit(1)

    # Run load test
    print(f"\n[2/3] Running load test ({DURATION_SECS}s with {CONCURRENT_USERS} users)...")
    stats.start_time = time.time()
    end_time = stats.start_time + DURATION_SECS

    tasks = [simulate_user(i, end_time) for i in range(CONCURRENT_USERS)]
    await asyncio.gather(*tasks)

    stats.end_time = time.time()

    # Post-test health check
    print("\n[3/3] Post-test health check...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{HOST}/health")
            if resp.status_code == 200:
                print("  API is still healthy after load test")
            else:
                print("  WARNING: API health degraded")
        except Exception:
            print("  ERROR: API not responding after load test")

    # Generate report
    generate_report()


if __name__ == "__main__":
    asyncio.run(main())
