#!/usr/bin/env python3
"""
Test AsyncOperationResult wrapper for backward compatibility.

Verifies that AsyncOperationResult provides a Response-compatible
interface without mutating third-party objects.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rest_api_helpers import AsyncOperationResult


def test_json_method():
    """Test .json() method compatibility."""
    print("\n=== Test 1: .json() Method ===")

    data = {"id": "123", "name": "Test Entity", "status": "active"}
    result = AsyncOperationResult(data=data)

    json_output = result.json()
    print(f"Data: {json_output}")

    assert json_output == data, "json() should return the data dict"
    assert isinstance(json_output, dict), "json() should return a dict"
    print("✅ PASS: .json() method works correctly")


def test_ok_property():
    """Test .ok property compatibility."""
    print("\n=== Test 2: .ok Property ===")

    # Test successful status (200)
    result_ok = AsyncOperationResult(data={}, status_code=200)
    assert result_ok.ok is True, "200 should be ok"
    print(f"Status 200: ok={result_ok.ok} ✅")

    # Test successful status (201)
    result_created = AsyncOperationResult(data={}, status_code=201)
    assert result_created.ok is True, "201 should be ok"
    print(f"Status 201: ok={result_created.ok} ✅")

    # Test error status (400)
    result_error = AsyncOperationResult(data={}, status_code=400)
    assert result_error.ok is False, "400 should not be ok"
    print(f"Status 400: ok={result_error.ok} ✅")

    # Test default status (200)
    result_default = AsyncOperationResult(data={})
    assert result_default.ok is True, "Default 200 should be ok"
    print(f"Status 200 (default): ok={result_default.ok} ✅")

    print("✅ PASS: .ok property works correctly")


def test_content_property():
    """Test .content property compatibility."""
    print("\n=== Test 3: .content Property ===")

    # Test with data
    data = {"id": "456", "value": "test"}
    result = AsyncOperationResult(data=data)

    content = result.content
    print(f"Content type: {type(content)}")
    print(f"Content: {content[:50]}")  # First 50 bytes

    assert isinstance(content, bytes), "content should be bytes"
    assert b'"id"' in content, "content should contain JSON"
    assert b'"456"' in content, "content should contain data values"
    print("✅ PASS: .content property returns bytes correctly")


def test_text_property():
    """Test .text property compatibility."""
    print("\n=== Test 4: .text Property ===")

    data = {"message": "Hello, World!"}
    result = AsyncOperationResult(data=data)

    text = result.text
    print(f"Text type: {type(text)}")
    print(f"Text: {text}")

    assert isinstance(text, str), "text should be string"
    assert "Hello, World!" in text, "text should contain data"
    assert '"message"' in text, "text should be JSON formatted"
    print("✅ PASS: .text property works correctly")


def test_empty_data_handling():
    """Test empty data handling."""
    print("\n=== Test 5: Empty Data Handling ===")

    # Test with empty dict
    result_empty = AsyncOperationResult(data={})
    assert result_empty.json() == {}, "Empty dict should be returned"
    # Empty dict encodes to b'{}', not b''
    assert result_empty.content == b'{}', f"Expected b'{{}}', got {result_empty.content}"
    print("Empty dict: ✅")

    # Test truthiness of content for backward compatibility check
    # In calling code: response.json() if response.content else {}
    # b'{}' is truthy in Python, so this works correctly
    assert result_empty.content, "b'{}' is truthy"
    print("Truthiness check: ✅")

    print("✅ PASS: Empty data handled correctly")


def test_original_response_storage():
    """Test that original response is stored."""
    print("\n=== Test 6: Original Response Storage ===")

    class MockResponse:
        """Mock response object."""
        status_code = 202
        headers = {"Location": "/async/status/123"}

    mock_response = MockResponse()
    data = {"completed": True}

    result = AsyncOperationResult(
        data=data,
        status_code=200,
        original_response=mock_response
    )

    assert result.original_response is mock_response, "Original response should be stored"
    assert result.original_response.status_code == 202, "Original was 202"
    assert result.status_code == 200, "Wrapper shows 200 (completed)"
    print("✅ PASS: Original response stored correctly")


def test_response_like_interface():
    """Test that interface mimics requests.Response."""
    print("\n=== Test 7: Response-like Interface ===")

    data = {"items": [1, 2, 3], "count": 3}
    result = AsyncOperationResult(data=data)

    # Verify all Response-compatible properties exist
    assert hasattr(result, 'json'), "Should have .json() method"
    assert hasattr(result, 'ok'), "Should have .ok property"
    assert hasattr(result, 'content'), "Should have .content property"
    assert hasattr(result, 'text'), "Should have .text property"
    assert hasattr(result, 'status_code'), "Should have .status_code attribute"

    # Verify they work correctly
    assert callable(result.json), ".json should be callable"
    assert isinstance(result.ok, bool), ".ok should be bool"
    assert isinstance(result.content, bytes), ".content should be bytes"
    assert isinstance(result.text, str), ".text should be str"
    assert isinstance(result.status_code, int), ".status_code should be int"

    print("✅ PASS: Response-like interface complete")


def test_backwards_compatibility_pattern():
    """Test typical usage pattern from calling code."""
    print("\n=== Test 8: Backward Compatibility Pattern ===")

    # Simulate what public API methods do
    def simulate_public_api_method(result):
        """Simulates: return response.json() if response.content else {}"""
        return result.json() if result.content else {}

    # Test with data
    result_with_data = AsyncOperationResult(data={"key": "value"})
    output = simulate_public_api_method(result_with_data)
    assert output == {"key": "value"}, "Should return data"
    print("With data: ✅")

    # Test with empty data
    result_empty = AsyncOperationResult(data={})
    output_empty = simulate_public_api_method(result_empty)
    assert output_empty == {}, "Should return empty dict"
    print("Empty data: ✅")

    print("✅ PASS: Backward compatibility pattern works")


def test_repr():
    """Test string representation for debugging."""
    print("\n=== Test 9: String Representation ===")

    data = {"id": "789", "name": "Item", "count": 42}
    result = AsyncOperationResult(data=data)

    repr_str = repr(result)
    print(f"repr: {repr_str}")

    assert "AsyncOperationResult" in repr_str, "Should identify class"
    assert "status_code=200" in repr_str, "Should show status code"
    assert "data_keys=" in repr_str, "Should show data keys"

    print("✅ PASS: String representation works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing AsyncOperationResult Wrapper")
    print("=" * 60)

    try:
        test_json_method()
        test_ok_property()
        test_content_property()
        test_text_property()
        test_empty_data_handling()
        test_original_response_storage()
        test_response_like_interface()
        test_backwards_compatibility_pattern()
        test_repr()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nAsyncOperationResult provides full Response compatibility")
        print("Existing code using .json(), .ok, .content will work unchanged")
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
