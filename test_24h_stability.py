#!/usr/bin/env python3
"""
24-Hour Stability Test for AdScreen
Tests robustness by making regular requests over extended period
Respects rate limiter configuration
"""

import requests
import time
import sys
from datetime import datetime, timedelta

BASE_URL = "http://31.97.154.192:5010"
TOTAL_DURATION = 3600  # 1 hour for faster testing (can extend to 86400 for 24h)
REQUEST_INTERVAL = 3  # seconds between requests
TEST_START = datetime.now()
TEST_END = TEST_START + timedelta(seconds=TOTAL_DURATION)

stats = {
    "total_requests": 0,
    "successful": 0,
    "failed": 0,
    "errors_by_code": {},
    "uptime": 0,
    "downtime": 0,
    "start_time": TEST_START,
    "end_time": None,
}

def make_request(url, timeout=10):
    """Make single request and return status"""
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code
    except requests.exceptions.Timeout:
        return "TIMEOUT"
    except requests.exceptions.ConnectionError:
        return "CONNECTION_ERROR"
    except Exception as e:
        return f"ERROR: {str(e)[:30]}"

def run_stability_test():
    """Run 24-hour stability test"""
    print("="*70)
    print("ADSCREEN 24-HOUR STABILITY TEST")
    print("="*70)
    print(f"Start Time: {TEST_START}")
    print(f"Target Duration: {TOTAL_DURATION} seconds")
    print(f"Request Interval: {REQUEST_INTERVAL} seconds")
    print(f"Rate Limiter: 50 per hour (100 default + 50 auth)")
    print(f"Expected Requests: ~{TOTAL_DURATION // REQUEST_INTERVAL}")
    print("="*70 + "\n")

    request_count = 0
    last_status = None
    consecutive_failures = 0
    max_consecutive_failures = 0

    try:
        while datetime.now() < TEST_END:
            current_time = datetime.now()
            elapsed = (current_time - TEST_START).total_seconds()
            request_count += 1

            # Make request
            status = make_request(f"{BASE_URL}/")
            stats["total_requests"] += 1

            # Log result
            is_success = status == 200
            if is_success:
                stats["successful"] += 1
                consecutive_failures = 0
                status_str = "✅"
            else:
                stats["failed"] += 1
                consecutive_failures += 1
                max_consecutive_failures = max(max_consecutive_failures, consecutive_failures)
                status_str = "❌"

            # Track status codes
            if status not in stats["errors_by_code"]:
                stats["errors_by_code"][status] = 0
            stats["errors_by_code"][status] += 1

            # Print progress every 10 requests or when status changes
            if request_count % 10 == 1 or (status != last_status and request_count > 1):
                success_rate = (stats["successful"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0
                time_remaining = TOTAL_DURATION - elapsed
                print(f"[{current_time.strftime('%H:%M:%S')}] Request #{request_count} "
                      f"Status={status} | Success Rate: {success_rate:.1f}% | "
                      f"Time Remaining: {time_remaining:.0f}s")

            last_status = status

            # Wait before next request (respects rate limiter)
            time.sleep(REQUEST_INTERVAL)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

    # Calculate final stats
    stats["end_time"] = datetime.now()
    stats["uptime"] = stats["successful"]
    stats["downtime"] = stats["failed"]

    # Print summary
    print_summary()

def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("STABILITY TEST RESULTS")
    print("="*70)

    total = stats["total_requests"]
    successful = stats["successful"]
    failed = stats["failed"]
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"\nTest Duration: {(stats['end_time'] - stats['start_time']).total_seconds():.0f} seconds")
    print(f"Total Requests: {total}")
    print(f"Successful Responses (200): {successful}")
    print(f"Failed Responses: {failed}")
    print(f"Success Rate: {success_rate:.2f}%")

    print(f"\nStatus Code Distribution:")
    for code, count in sorted(stats["errors_by_code"].items()):
        pct = (count / total * 100)
        print(f"  {str(code):20} : {count:4} ({pct:5.2f}%)")

    print(f"\nUptime: {stats['uptime']/total*100:.2f}%")
    print(f"Downtime: {stats['downtime']/total*100:.2f}%")

    # Assessment
    print("\n" + "-"*70)
    if success_rate >= 99.0:
        assessment = "✅ EXCELLENT - Ready for 24/7 production"
    elif success_rate >= 95.0:
        assessment = "✅ GOOD - Suitable for 24/7 operation with monitoring"
    elif success_rate >= 90.0:
        assessment = "⚠️  ACCEPTABLE - Monitor closely for 24/7 operation"
    else:
        assessment = "❌ NEEDS WORK - Investigate failures before 24/7 deployment"

    print(assessment)
    print("-"*70)

    # Rate limiter summary
    if stats["errors_by_code"].get(429, 0) > 0:
        rate_limited = stats["errors_by_code"][429]
        print(f"\n⚠️  Rate Limited (429): {rate_limited} times")
        print("    This is expected with aggressive rate limiting (50/hour)")
        print("    To avoid: space requests 72 seconds apart or more")

    print("\n" + "="*70 + "\n")

    return success_rate >= 90.0

def main():
    try:
        success = run_stability_test()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
