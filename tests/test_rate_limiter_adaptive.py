#!/usr/bin/env python3
"""
Test adaptive rate limiting functionality.

Tests the 4-tier adaptive rate adjustment in rate_limit_manager.py.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rate_limit_manager import RateLimitManager


def test_emergency_slowdown():
    """Test emergency slowdown when <5% remaining."""
    print("\n=== Test 1: Emergency Slowdown (<5% remaining) ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/users"

    # Simulate critical rate limit: 2/100 remaining (2%)
    headers = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '2'
    }

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers)

    new_rate = manager.get_limiter(url).rate
    print(f"After update: {new_rate:.2f} cps")
    print(f"Expected: ~{initial_rate * 0.3:.2f} cps (30% of original)")

    assert new_rate < initial_rate, "Rate should decrease"
    assert new_rate >= 0.1, "Rate should not go below 0.1 cps"
    print("✅ PASS: Emergency slowdown works correctly")


def test_aggressive_slowdown():
    """Test aggressive slowdown when <10% remaining."""
    print("\n=== Test 2: Aggressive Slowdown (<10% remaining) ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/repos"

    # Simulate low rate limit: 8/100 remaining (8%)
    headers = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '8'
    }

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers)

    new_rate = manager.get_limiter(url).rate
    print(f"After update: {new_rate:.2f} cps")
    print(f"Expected: ~{initial_rate * 0.5:.2f} cps (50% of original)")

    assert new_rate < initial_rate, "Rate should decrease"
    assert new_rate >= 0.5, "Rate should not go below 0.5 cps"
    print("✅ PASS: Aggressive slowdown works correctly")


def test_moderate_slowdown():
    """Test moderate slowdown when <25% remaining."""
    print("\n=== Test 3: Moderate Slowdown (<25% remaining) ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/issues"

    # Simulate depleting rate limit: 20/100 remaining (20%)
    headers = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '20'
    }

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers)

    new_rate = manager.get_limiter(url).rate
    print(f"After update: {new_rate:.2f} cps")
    print(f"Expected: ~{initial_rate * 0.75:.2f} cps (75% of original)")

    assert new_rate < initial_rate, "Rate should decrease"
    assert new_rate >= 1.0, "Rate should not go below 1.0 cps"
    print("✅ PASS: Moderate slowdown works correctly")


def test_speedup_recovery():
    """Test speed up when >75% remaining."""
    print("\n=== Test 4: Speed Up Recovery (>75% remaining) ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/pulls"

    # First, slow down the rate
    headers_low = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '20'  # 20% - moderate slowdown
    }

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers_low)
    slowed_rate = manager.get_limiter(url).rate
    print(f"After slowdown: {slowed_rate:.2f} cps")

    # Now simulate recovery: 85/100 remaining (85%)
    headers_high = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '85'
    }

    manager.update_from_headers(url, headers_high)
    recovered_rate = manager.get_limiter(url).rate
    print(f"After recovery: {recovered_rate:.2f} cps")
    print(f"Expected: moving back toward {initial_rate:.2f} cps")

    assert recovered_rate > slowed_rate, "Rate should increase during recovery"
    assert recovered_rate <= initial_rate, "Rate should not exceed original"
    print("✅ PASS: Speed up recovery works correctly")


def test_stable_zone():
    """Test stable zone (25%-75% remaining)."""
    print("\n=== Test 5: Stable Zone (25%-75% remaining) ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/commits"

    # Simulate stable rate limit: 50/100 remaining (50%)
    headers = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '50'
    }

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers)

    new_rate = manager.get_limiter(url).rate
    print(f"After update: {new_rate:.2f} cps")
    print("Expected: No change (stable zone)")

    assert new_rate == initial_rate, "Rate should remain stable"
    print("✅ PASS: Stable zone works correctly")


def test_reset_time_handling():
    """Test reset time parsing and recovery."""
    print("\n=== Test 6: Reset Time Handling ===")

    import time

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/search"

    # First, trigger slowdown
    headers_low = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '5',  # 5% - emergency
        'X-RateLimit-Reset': str(int(time.time()) + 3600)  # Resets in 1 hour
    }

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers_low)
    slowed_rate = manager.get_limiter(url).rate
    print(f"After slowdown: {slowed_rate:.2f} cps")

    # Simulate reset time passing (use past timestamp)
    headers_reset = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '100',  # Full reset
        'X-RateLimit-Reset': str(int(time.time()) - 10)  # Reset 10 seconds ago
    }

    manager.update_from_headers(url, headers_reset)
    recovered_rate = manager.get_limiter(url).rate
    print(f"After reset: {recovered_rate:.2f} cps")
    print(f"Expected: Back to original {initial_rate:.2f} cps")

    assert recovered_rate == initial_rate, "Rate should fully recover after reset"
    print("✅ PASS: Reset time handling works correctly")


def test_retry_after_header():
    """Test Retry-After header parsing."""
    print("\n=== Test 7: Retry-After Header ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/graphql"

    # Simulate 429 response with Retry-After
    headers = {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '0',
        'Retry-After': '60'  # Wait 60 seconds
    }

    print("Simulating 429 response with Retry-After: 60s")
    manager.update_from_headers(url, headers)

    # Should log warning but not crash
    print("✅ PASS: Retry-After header handled correctly")


def test_missing_headers():
    """Test handling of missing headers."""
    print("\n=== Test 8: Missing Headers ===")

    manager = RateLimitManager(default_cps=10.0)
    url = "https://api.example.com/v1/orgs"

    # No rate limit headers
    headers = {}

    initial_rate = manager.get_limiter(url).rate
    print(f"Initial rate: {initial_rate:.2f} cps")

    manager.update_from_headers(url, headers)

    new_rate = manager.get_limiter(url).rate
    print(f"After update with no headers: {new_rate:.2f} cps")

    assert new_rate == initial_rate, "Rate should not change without headers"
    print("✅ PASS: Missing headers handled correctly")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Adaptive Rate Limiter")
    print("=" * 60)

    try:
        test_emergency_slowdown()
        test_aggressive_slowdown()
        test_moderate_slowdown()
        test_speedup_recovery()
        test_stable_zone()
        test_reset_time_handling()
        test_retry_after_header()
        test_missing_headers()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
