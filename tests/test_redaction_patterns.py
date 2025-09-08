# tests/test_redaction.py
"""
Test script to verify redaction patterns are working correctly.

Run this to ensure sensitive data is being properly redacted.
"""

from utils.logger import setup_logger

def test_redaction_patterns():
    """Test various sensitive data patterns to ensure they're redacted."""
    logger = setup_logger()
    
    print("\n=== Testing Redaction Patterns ===\n")
    print("Check the console output and log file to verify redaction:\n")
    
    # Test Azure Communication Services
    logger.info("Azure Comm connection: endpoint=https://coms-txo-cybersec.europe.communication.azure.com/;accesskey=abcd1234efgh5678ijkl")
    # Should show: endpoint=https://coms-txo-cybersec.europe.communication.azure.com/;accesskey=[REDACTED_ACCESS_KEY]
    
    # Test Azure Storage
    logger.info("Storage: DefaultEndpointsProtocol=https;AccountName=mystorageaccount;AccountKey=abc123def456ghi789==")
    # Should show: DefaultEndpointsProtocol=https;AccountName=[REDACTED];AccountKey=[REDACTED]
    
    # Test Bearer tokens
    logger.info("Auth header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U")
    # Should show: Auth header: Bearer [REDACTED]
    
    # Test JWT tokens
    logger.info("Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U")
    # Should show: Token: [REDACTED_JWT]
    
    # Test passwords in JSON
    logger.info('Config: {"username": "admin", "password": "supersecret123"}')
    # Should show: Config: {"username": "admin", "password": "[REDACTED]"}
    
    # Test API keys
    logger.info("Request URL: https://api.example.com/data?api_key=1234567890abcdefghij&user=john")
    # Should show: Request URL: https://api.example.com/data?api_key=[REDACTED_API_KEY]&user=john
    
    # Test client secrets
    logger.info('OAuth: {"client_id": "my-app", "client_secret": "secret123456"}')
    # Should show: OAuth: {"client_id": "my-app", "client_secret": "[REDACTED]"}
    
    # Test long random tokens
    logger.info("Random token: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6")
    # Should show: Random token: [REDACTED_TOKEN]
    
    # Test credit card
    logger.info("Payment with card: 4111-1111-1111-1111")
    # Should show: Payment with card: [REDACTED_CARD]
    
    # Test SSN
    logger.info("Customer SSN: 123-45-6789")
    # Should show: Customer SSN: [REDACTED_SSN]
    
    # Test connection strings
    logger.info("DB: Server=myserver;Database=mydb;User Id=sa;Password=MyP@ssw0rd;")
    # Should show: DB: Server=myserver;Database=mydb;User Id=sa;Password=[REDACTED];
    
    # Test multiple sensitive items in one message
    logger.info("Full config: api_key=abc123 secret=xyz789 Bearer token123456789012345678901234567890")
    # Should show: Full config: api_key=[REDACTED_API_KEY] secret=[REDACTED_SECRET] Bearer [REDACTED]
    
    print("\n=== Test Complete ===")
    print("Check the log file for redacted output")
    print("If any sensitive data is NOT redacted, update redaction-patterns.json\n")

def test_reload_patterns():
    """Test that patterns can be reloaded at runtime."""
    logger = setup_logger()
    
    print("\n=== Testing Pattern Reload ===\n")
    
    logger.info("Before reload: accesskey=sensitive123")
    
    # Simulate updating the config file
    print("Update redaction-patterns.json if needed, then press Enter...")
    input()
    
    # Reload patterns
    logger.reload_redaction_patterns()
    
    logger.info("After reload: accesskey=sensitive456")
    
    print("\n=== Reload Test Complete ===\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reload":
        test_reload_patterns()
    else:
        test_redaction_patterns()
        print("\nTip: Run with --reload flag to test pattern reloading")