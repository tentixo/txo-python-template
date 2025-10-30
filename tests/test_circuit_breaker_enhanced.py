#!/usr/bin/env python3
"""
Test enhanced circuit breaker functionality.

Tests state transition logging and statistics tracking.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_common import CircuitBreaker


def test_state_transitions():
    """Test state transition logging."""
    print("\n=== Test 1: State Transitions ===")

    breaker = CircuitBreaker(failure_threshold=3, timeout=2)

    # Initial state
    assert breaker.stats['state'] == 'closed', "Should start closed"
    print(f"Initial state: {breaker.stats['state']} ✅")

    # Record failures to open circuit
    for i in range(3):
        breaker.record_failure()
        print(f"Failure {i+1}: state={breaker.stats['state']}, consecutive={breaker.stats['consecutive_failures']}")

    assert breaker.stats['state'] == 'open', "Should be open after threshold"
    assert breaker.is_open() is True, "is_open() should return True"
    print(f"After 3 failures: {breaker.stats['state']} ✅")

    # Wait for timeout and check half-open
    print(f"Waiting {breaker.timeout}s for timeout...")
    time.sleep(breaker.timeout + 0.1)

    is_open = breaker.is_open()  # Triggers state change to half-open
    assert is_open is False, "Should allow attempt in half-open"
    assert breaker.stats['state'] == 'half-open', "Should be half-open after timeout"
    print(f"After timeout: {breaker.stats['state']} ✅")

    # Success closes circuit
    breaker.record_success()
    assert breaker.stats['state'] == 'closed', "Success should close circuit"
    print(f"After success: {breaker.stats['state']} ✅")

    print("✅ PASS: State transitions work correctly")


def test_statistics_tracking():
    """Test statistics collection."""
    print("\n=== Test 2: Statistics Tracking ===")

    breaker = CircuitBreaker(failure_threshold=5, timeout=30)

    # Record mix of successes and failures
    # Sequence: success, success, failure, success, failure, failure
    breaker.record_success()
    breaker.record_success()
    breaker.record_failure()
    breaker.record_success()
    breaker.record_failure()
    breaker.record_failure()  # Last two are consecutive failures

    stats = breaker.stats
    print(f"Stats after 6 requests:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total failures: {stats['total_failures']}")
    print(f"  Consecutive failures: {stats['consecutive_failures']}")
    print(f"  Failure rate: {stats['failure_rate']:.1%}")

    assert stats['total_requests'] == 6, f"Should have 6 total requests, got {stats['total_requests']}"
    assert stats['total_failures'] == 3, f"Should have 3 failures, got {stats['total_failures']}"
    assert stats['consecutive_failures'] == 2, "Last two requests were failures"
    assert stats['failure_rate'] == 0.5, f"Failure rate should be 50%, got {stats['failure_rate']}"

    print("✅ PASS: Statistics tracking works correctly")


def test_consecutive_failures():
    """Test consecutive failure tracking."""
    print("\n=== Test 3: Consecutive Failure Tracking ===")

    breaker = CircuitBreaker(failure_threshold=3, timeout=60)

    # Record some failures
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.stats['consecutive_failures'] == 2, "Should have 2 consecutive"
    print(f"After 2 failures: consecutive={breaker.stats['consecutive_failures']} ✅")

    # Success resets consecutive counter
    breaker.record_success()
    assert breaker.stats['consecutive_failures'] == 0, "Success should reset consecutive"
    assert breaker.stats['total_failures'] == 2, "Total failures should still be 2"
    print(f"After success: consecutive={breaker.stats['consecutive_failures']}, total={breaker.stats['total_failures']} ✅")

    print("✅ PASS: Consecutive failure tracking works correctly")


def test_time_in_state():
    """Test time in state tracking."""
    print("\n=== Test 4: Time in State Tracking ===")

    breaker = CircuitBreaker(failure_threshold=2, timeout=1)

    # Start in closed state
    initial_time = breaker.stats['time_in_current_state']
    assert initial_time >= 0, "Time in state should be >= 0"
    print(f"Initial time in closed state: {initial_time:.3f}s ✅")

    # Wait a bit
    time.sleep(0.2)
    later_time = breaker.stats['time_in_current_state']
    assert later_time > initial_time, "Time in state should increase"
    print(f"After 0.2s: {later_time:.3f}s ✅")

    # Change state
    breaker.record_failure()
    breaker.record_failure()  # Opens circuit
    open_time = breaker.stats['time_in_current_state']
    assert open_time < later_time, "Time should reset on state change"
    print(f"After state change to open: {open_time:.3f}s (reset) ✅")

    print("✅ PASS: Time in state tracking works correctly")


def test_failure_rate_calculation():
    """Test failure rate calculation."""
    print("\n=== Test 5: Failure Rate Calculation ===")

    breaker = CircuitBreaker()

    # No requests yet
    assert breaker.stats['failure_rate'] == 0.0, "Should be 0% with no requests"
    print("No requests: 0% ✅")

    # All successes
    for _ in range(10):
        breaker.record_success()
    assert breaker.stats['failure_rate'] == 0.0, "Should be 0% with all successes"
    print(f"10 successes: {breaker.stats['failure_rate']:.1%} ✅")

    # Add some failures
    for _ in range(5):
        breaker.record_failure()
    expected_rate = 5 / 15  # 5 failures out of 15 total
    assert abs(breaker.stats['failure_rate'] - expected_rate) < 0.01, "Should be ~33%"
    print(f"5 failures / 15 total: {breaker.stats['failure_rate']:.1%} ✅")

    print("✅ PASS: Failure rate calculation works correctly")


def test_last_failure_tracking():
    """Test last failure time tracking."""
    print("\n=== Test 6: Last Failure Tracking ===")

    breaker = CircuitBreaker()

    # No failures yet
    assert breaker.stats['last_failure_ago'] is None, "Should be None with no failures"
    print("No failures yet: last_failure_ago=None ✅")

    # Record a failure
    breaker.record_failure()
    time.sleep(0.1)

    last_failure_ago = breaker.stats['last_failure_ago']
    assert last_failure_ago is not None, "Should have last_failure_ago"
    assert last_failure_ago >= 0.1, "Should be at least 0.1s ago"
    print(f"After failure: last_failure_ago={last_failure_ago:.3f}s ✅")

    print("✅ PASS: Last failure tracking works correctly")


def test_stats_keys():
    """Test that all expected stats keys are present."""
    print("\n=== Test 7: Statistics Keys ===")

    breaker = CircuitBreaker()
    stats = breaker.stats

    expected_keys = [
        'state',
        'consecutive_failures',
        'failure_threshold',
        'total_requests',
        'total_failures',
        'failure_rate',
        'time_in_current_state',
        'timeout_seconds',
        'last_failure_ago'
    ]

    for key in expected_keys:
        assert key in stats, f"Missing key: {key}"
        print(f"✓ {key}: {stats[key]}")

    print("✅ PASS: All statistics keys present")


def test_manual_reset():
    """Test manual reset functionality."""
    print("\n=== Test 8: Manual Reset ===")

    breaker = CircuitBreaker(failure_threshold=2, timeout=60)

    # Open the circuit
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.stats['state'] == 'open', "Circuit should be open"
    assert breaker.stats['total_failures'] == 2, "Should have 2 failures"
    print(f"Circuit opened: failures={breaker.stats['total_failures']} ✅")

    # Manual reset
    breaker.reset()
    assert breaker.stats['state'] == 'closed', "Should be closed after reset"
    assert breaker.stats['consecutive_failures'] == 0, "Consecutive should be reset"
    assert breaker.stats['total_failures'] == 2, "Total failures preserved"
    print(f"After reset: state={breaker.stats['state']}, consecutive={breaker.stats['consecutive_failures']} ✅")

    print("✅ PASS: Manual reset works correctly")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Enhanced Circuit Breaker")
    print("=" * 60)

    try:
        test_state_transitions()
        test_statistics_tracking()
        test_consecutive_failures()
        test_time_in_state()
        test_failure_rate_calculation()
        test_last_failure_tracking()
        test_stats_keys()
        test_manual_reset()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nCircuit breaker now provides:")
        print("  • State transition logging with timing")
        print("  • Comprehensive statistics for monitoring")
        print("  • Better observability and debugging")
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
