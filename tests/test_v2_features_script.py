# test/test_v2_features.py
"""
Comprehensive test for v2.0 refactored features.

Tests:
- Token redaction in logs
- Rate limiting
- Circuit breaker
- Intelligent save()
- API factory with config
- Error handling patterns

Usage:
    python test_v2_features.py <org_id> <env_type>

Example:
    python test_v2_features.py demo test
"""

import time
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any

from utils.logger import setup_logger
from utils.load_n_save import TxoDataHandler
from utils.api_factory import create_rest_api, ApiManager, get_batch_config
from utils.exceptions import HelpfulError, ApiOperationError
from utils.api_common import RateLimiter, CircuitBreaker

logger = setup_logger()
data_handler = TxoDataHandler()


def test_token_redaction(config: Dict[str, Any]) -> None:
    """Test that sensitive data is redacted in logs."""
    logger.info("=" * 50)
    logger.info("TEST 1: Token Redaction")
    logger.info("=" * 50)

    # These should all be redacted
    test_cases = [
        ("Bearer token", f"Bearer {config.get('_token', 'test123abc')}"),
        ("JWT token", "eyJhbGciOiJIUzI1NiIs.eyJzdWIiOiIxMjM0.abc123xyz"),
        ("Password JSON", '{"password": "supersecret123"}'),
        ("Client secret", '{"client-secret": "my-secret-value"}'),
        ("Long token", "a" * 50)  # 50 character token
    ]

    for name, value in test_cases:
        logger.info(f"Testing {name}: {value}")

    logger.info("✅ Check logs/app_*.log - all sensitive data should show [REDACTED]")
    print()


def test_rate_limiter(config: Dict[str, Any]) -> None:
    """Test rate limiting functionality."""
    logger.info("=" * 50)
    logger.info("TEST 2: Rate Limiter")
    logger.info("=" * 50)

    # Get rate limit from config
    rate_config = config["script-behavior"]["rate-limiting"]

    if not rate_config["enabled"]:
        logger.warning("Rate limiting disabled in config - skipping test")
        return

    calls_per_second = rate_config["calls-per-second"]
    limiter = RateLimiter(calls_per_second=calls_per_second)

    logger.info(f"Testing {calls_per_second} calls/second rate limit")

    # Make rapid calls
    start = time.time()
    num_calls = 10

    for i in range(num_calls):
        limiter.wait_if_needed()
        logger.debug(f"Call {i + 1}/{num_calls} completed")

    elapsed = time.time() - start
    expected_min = (num_calls - 1) / calls_per_second

    logger.info(f"Made {num_calls} calls in {elapsed:.2f}s")
    logger.info(f"Expected minimum time: {expected_min:.2f}s")

    if elapsed >= expected_min * 0.9:  # Allow 10% tolerance
        logger.info("✅ Rate limiter working correctly")
    else:
        logger.warning(f"⚠️ Rate limiter may not be working (too fast)")
    print()


def test_circuit_breaker(config: Dict[str, Any]) -> None:
    """Test circuit breaker functionality."""
    logger.info("=" * 50)
    logger.info("TEST 3: Circuit Breaker")
    logger.info("=" * 50)

    cb_config = config["script-behavior"]["circuit-breaker"]

    if not cb_config["enabled"]:
        logger.warning("Circuit breaker disabled in config - skipping test")
        return

    threshold = cb_config["failure-threshold"]
    timeout = cb_config["timeout-seconds"]

    breaker = CircuitBreaker(failure_threshold=threshold, timeout=timeout)

    logger.info(f"Testing circuit breaker (threshold={threshold}, timeout={timeout}s)")

    # Record failures
    for i in range(threshold):
        breaker.record_failure()
        logger.debug(f"Recorded failure {i + 1}/{threshold}")

    # Should be open now
    if breaker.is_open():
        logger.info("✅ Circuit breaker opened after threshold failures")
    else:
        logger.error("❌ Circuit breaker should be open but isn't")

    # Record success to reset
    breaker.record_success()
    if not breaker.is_open():
        logger.info("✅ Circuit breaker reset after success")
    else:
        logger.error("❌ Circuit breaker should be closed after success")
    print()


def test_intelligent_save(config: Dict[str, Any]) -> None:
    """Test automatic type detection in save()."""
    logger.info("=" * 50)
    logger.info("TEST 4: Intelligent Save")
    logger.info("=" * 50)

    org_id = config["_org_id"]
    env_type = config["_env_type"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    # Test 1: JSON with Decimal
    json_data = {
        "amount": Decimal("99.99"),
        "count": 100,
        "org": org_id,
        "env": env_type
    }
    filename = f"{org_id}-{env_type}-test_json_{timestamp}.json"
    path = data_handler.save(json_data, "tmp", filename)
    logger.info(f"✅ JSON with Decimal saved to {path}")

    # Verify it was saved correctly
    loaded = data_handler.load_json("tmp", filename)
    if loaded["amount"] == 99.99:  # Will be float after round-trip
        logger.info("✅ Decimal serialization worked")

    # Test 2: Plain text
    text_data = f"Test report for {org_id}-{env_type}\nGenerated at {timestamp}"
    filename = f"{org_id}-{env_type}-test_text_{timestamp}.txt"
    path = data_handler.save(text_data, "tmp", filename)
    logger.info(f"✅ Text saved to {path}")

    # Test 3: DataFrame (if pandas available)
    try:
        import pandas as pd
        df = pd.DataFrame([
            {"col1": 1, "col2": "a"},
            {"col1": 2, "col2": "b"}
        ])

        # CSV
        filename = f"{org_id}-{env_type}-test_csv_{timestamp}.csv"
        path = data_handler.save(df, "tmp", filename, index=False)
        logger.info(f"✅ DataFrame saved as CSV to {path}")

        # Excel
        filename = f"{org_id}-{env_type}-test_xlsx_{timestamp}.xlsx"
        path = data_handler.save(df, "tmp", filename, index=False, sheet_name="TestSheet")
        logger.info(f"✅ DataFrame saved as Excel to {path}")

    except ImportError:
        pd = None
        logger.info("⚠️ Pandas not installed - skipping DataFrame tests")

    print()


def test_api_factory(config: Dict[str, Any]) -> None:
    """Test API factory with new features."""
    logger.info("=" * 50)
    logger.info("TEST 5: API Factory")
    logger.info("=" * 50)

    # Test 1: Create API with config
    try:
        api = create_rest_api(config)

        # Check features
        if api.rate_limiter:
            logger.info("✅ Rate limiter created from config")
        else:
            logger.info("ℹ️ Rate limiter not enabled")

        if api.circuit_breaker:
            logger.info("✅ Circuit breaker created from config")
        else:
            logger.info("ℹ️ Circuit breaker not enabled")

        # Clean up
        api.close()

    except KeyError as e:
        logger.error(f"❌ Missing required config: {e}")
        raise HelpfulError(
            what_went_wrong=f"Configuration missing required key: {e}",
            how_to_fix="Ensure your config has all required sections",
            example="Check script-behavior section with all subsections"
        )

    # Test 2: Context manager
    try:
        with ApiManager(config) as manager:
            manager.get_rest_api()
            logger.info("✅ API created with context manager")
            # API will be closed automatically
    except Exception as e:
        logger.error(f"❌ Context manager failed: {e}")

    # Test 3: Batch config
    try:
        batch_config = get_batch_config(config)
        logger.info(f"✅ Batch config retrieved: read-batch-size={batch_config['read-batch-size']}")
    except KeyError as e:
        logger.error(f"❌ Batch config missing: {e}")

    print()


def test_github_api(config: Dict[str, Any]) -> None:
    """Test actual API call using TxoRestAPI."""
    logger.info("=" * 50)
    logger.info("TEST 6: Live API Test (GitHub)")
    logger.info("=" * 50)

    try:
        api = create_rest_api(config, require_auth=False)

        # Make request to GitHub
        url = "https://api.github.com/repos/python/cpython"

        logger.info("Fetching Python repository info from GitHub...")
        start = time.time()

        result = api.get(url)

        elapsed = time.time() - start

        if result:
            logger.info(f"✅ API call successful in {elapsed:.2f}s")
            logger.info(f"Repository: {result.get('full_name')}")
            logger.info(f"Stars: {result.get('stargazers_count', 0):,}")
            logger.info(f"Language: {result.get('language')}")
        else:
            logger.warning("⚠️ No data returned")

        api.close()

    except ApiOperationError as e:
        logger.error(f"❌ API call failed: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

    print()


def test_error_patterns(config: Dict[str, Any]) -> None:
    """Test error handling patterns."""
    logger.info("=" * 50)
    logger.info("TEST 7: Error Patterns")
    logger.info("=" * 50)

    # Use config to satisfy PyCharm
    org_id = config["_org_id"]
    env_type = config["_env_type"]
    logger.debug(f"Testing error patterns for {org_id}-{env_type}")

    # Test HelpfulError
    try:
        raise HelpfulError(
            what_went_wrong="This is a test error",
            how_to_fix="No action needed - this is intentional",
            example="This demonstrates the helpful error format"
        )
    except HelpfulError as e:
        logger.info("HelpfulError format:")
        print(str(e))
        logger.info("✅ HelpfulError pattern working")

    print()


def generate_summary_report(config: Dict[str, Any], test_results: Dict[str, bool]) -> None:
    """Generate and save test summary report."""
    logger.info("=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)

    org_id = config["_org_id"]
    env_type = config["_env_type"]

    # Calculate stats
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)

    # Create report
    report = {
        "test_run": {
            "org_id": org_id,
            "env_type": env_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests
        },
        "test_results": test_results,
        "configuration": {
            "rate_limiting_enabled": config["script-behavior"]["rate-limiting"]["enabled"],
            "circuit_breaker_enabled": config["script-behavior"]["circuit-breaker"]["enabled"],
            "timeout_seconds": config["script-behavior"]["api-timeouts"]["rest-timeout-seconds"]
        }
    }

    # Save report
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{org_id}-{env_type}-test_report_{timestamp}.json"
    path = data_handler.save(report, "output", filename)

    # Display summary
    logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")

    logger.info(f"\nReport saved to: {path}")

    if passed_tests == total_tests:
        logger.info("\n🎉 All tests passed!")
    elif passed_tests > 0:
        logger.info(f"\n⚠️ {total_tests - passed_tests} test(s) failed")
    else:
        logger.error("\n❌ All tests failed")


def main():
    """Main test orchestration."""
    # Parse args and setup logger FIRST
    from utils.script_runner import parse_args_and_load_config

    config = parse_args_and_load_config(
        "V2.0 Feature Test Suite",
        require_token=False)

    logger.info("Starting v2.0 feature tests")
    logger.info(f"Organization: {config['_org_id']}")
    logger.info(f"Environment: {config['_env_type']}")
    print()

    # Track results
    test_results = {}

    # Run tests
    tests = [
        ("token_redaction", test_token_redaction),
        ("rate_limiter", test_rate_limiter),
        ("circuit_breaker", test_circuit_breaker),
        ("intelligent_save", test_intelligent_save),
        ("api_factory", test_api_factory),
        ("github_api", test_github_api),
        ("error_patterns", test_error_patterns)
    ]

    for test_name, test_func in tests:
        try:
            test_func(config)
            test_results[test_name] = True
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            test_results[test_name] = False

    # Generate summary
    generate_summary_report(config, test_results)


if __name__ == "__main__":
    import sys

    try:
        main()
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except HelpfulError as e:
        # These are already formatted nicely
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
