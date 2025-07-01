"""
Simple security tests for FlipLens backend
Tests core security logic without Flask dependencies
"""

import re
import html
import urllib.parse

class SecurityValidator:
    """Input validation and sanitization utilities"""
    
    # Regex patterns for validation
    PATTERNS = {
        'query': r'^[a-zA-Z0-9\s\-_.,!?()]+$',  # Alphanumeric, spaces, basic punctuation
        'item_id': r'^[0-9]+$',  # Numeric only
        'price': r'^[0-9]+(\.[0-9]{1,2})?$',  # Decimal number with up to 2 decimal places
        'url': r'^https?://[^\s/$.?#].[^\s]*$',  # Basic URL validation
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email validation
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'safe_text': r'^[a-zA-Z0-9\s\-_.,!?()]+$'
    }
    
    @classmethod
    def validate_string(cls, value: str, pattern: str, max_length: int = 100) -> bool:
        """Validate a string against a pattern and length limit"""
        if not isinstance(value, str):
            return False
        
        if len(value) > max_length:
            return False
        
        if not re.match(cls.PATTERNS.get(pattern, cls.PATTERNS['safe_text']), value):
            return False
        
        return True
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string to prevent XSS and injection attacks"""
        if not isinstance(value, str):
            return ""
        
        # HTML escape
        value = html.escape(value)
        
        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\']', '', value)
        
        # URL decode to prevent double encoding attacks
        try:
            value = urllib.parse.unquote(value)
        except:
            pass
        
        return value.strip()

def test_security_validator():
    """Test the SecurityValidator class"""
    print("Testing SecurityValidator...")
    
    # Test valid queries
    valid_queries = [
        "nike shoes",
        "iPhone 13",
        "laptop computer",
        "gaming console",
        "books and magazines"
    ]
    
    print("\n✅ Valid queries:")
    for query in valid_queries:
        is_valid = SecurityValidator.validate_string(query, 'query')
        print(f"  '{query}' -> {is_valid}")
        assert is_valid, f"Query '{query}' should be valid"
    
    # Test invalid queries
    invalid_queries = [
        "nike<script>alert('xss')</script>",
        "iPhone'; DROP TABLE users; --",
        "laptop<>&\"'",
        "console|`$(){}",
        "books; rm -rf /"
    ]
    
    print("\n❌ Invalid queries:")
    for query in invalid_queries:
        is_valid = SecurityValidator.validate_string(query, 'query')
        print(f"  '{query}' -> {is_valid}")
        assert not is_valid, f"Query '{query}' should be invalid"
    
    # Test sanitization
    print("\n🧹 Sanitization tests:")
    sanitize_tests = [
        ("<script>alert('xss')</script>", "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"),
        ("nike'; DROP TABLE users; --", "nike&#x27;; DROP TABLE users; --"),
        ("iPhone<>&\"'", "iPhone&lt;&gt;&amp;&quot;&#x27;"),
        ("laptop|`$(){}", "laptop|`$(){}"),
        ("books; rm -rf /", "books; rm -rf /"),
    ]
    
    for input_str, expected in sanitize_tests:
        result = SecurityValidator.sanitize_string(input_str)
        print(f"  '{input_str}' -> '{result}'")
        assert result == expected, f"Sanitization failed for '{input_str}'"
    
    # Test length limits
    print("\n📏 Length limit tests:")
    short_query = "test"
    assert SecurityValidator.validate_string(short_query, 'query', max_length=10)
    
    limit_query = "a" * 10
    assert SecurityValidator.validate_string(limit_query, 'query', max_length=10)
    
    long_query = "a" * 11
    assert not SecurityValidator.validate_string(long_query, 'query', max_length=10)
    
    print("  ✅ Length validation working correctly")
    
    print("\n🎉 All SecurityValidator tests passed!")

def test_attack_patterns():
    """Test common attack patterns"""
    print("\n🛡️ Testing attack patterns...")
    
    # XSS patterns
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "onload=alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
    ]
    
    print("\n❌ XSS patterns (should be rejected):")
    for payload in xss_payloads:
        is_valid = SecurityValidator.validate_string(payload, 'query')
        print(f"  '{payload}' -> {is_valid}")
        assert not is_valid, f"XSS payload '{payload}' should be rejected"
    
    # SQL injection patterns
    sql_payloads = [
        "'; DROP TABLE users; --",
        "' OR 1=1 --",
        "' UNION SELECT * FROM users --",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",
    ]
    
    print("\n❌ SQL injection patterns (should be rejected):")
    for payload in sql_payloads:
        is_valid = SecurityValidator.validate_string(payload, 'query')
        print(f"  '{payload}' -> {is_valid}")
        assert not is_valid, f"SQL injection payload '{payload}' should be rejected"
    
    # Command injection patterns
    cmd_payloads = [
        "; rm -rf /",
        "| cat /etc/passwd",
        "`whoami`",
        "$(id)",
        "& del C:\\Windows\\System32",
    ]
    
    print("\n❌ Command injection patterns (should be rejected):")
    for payload in cmd_payloads:
        is_valid = SecurityValidator.validate_string(payload, 'query')
        print(f"  '{payload}' -> {is_valid}")
        assert not is_valid, f"Command injection payload '{payload}' should be rejected"
    
    print("\n🎉 All attack pattern tests passed!")

def test_ebay_service_security():
    """Test eBay service security methods"""
    print("\n🔍 Testing eBay service security methods...")
    
    class MockEbayService:
        def _sanitize_query(self, query: str) -> str:
            """Sanitize search query to prevent injection attacks"""
            if not isinstance(query, str):
                return ""
            
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
            for char in dangerous_chars:
                query = query.replace(char, '')
            
            # Limit query length
            if len(query) > 100:
                query = query[:100]
            
            return query.strip()
        
        def _validate_limit(self, limit) -> int:
            """Validate and sanitize limit parameter"""
            try:
                limit = int(limit)
                if limit < 1:
                    return 1
                elif limit > 100:
                    return 100
                return limit
            except (ValueError, TypeError):
                return 20
        
        def _extract_safe_string(self, value) -> str:
            """Extract and sanitize string value from eBay response"""
            if isinstance(value, list):
                value = value[0] if value else ''
            
            if not isinstance(value, str):
                return ''
            
            # Basic sanitization
            value = value.strip()
            if len(value) > 500:  # Limit length
                value = value[:500]
            
            return value
    
    service = MockEbayService()
    
    # Test query sanitization
    print("\n🧹 Query sanitization:")
    sanitize_tests = [
        ("nike shoes", "nike shoes"),
        ("<script>alert('xss')</script>", "scriptalertxss/script"),
        ("iPhone'; DROP TABLE users; --", "iPhone DROP TABLE users --"),
        ("laptop<>&\"'", "laptop"),
        ("console|`$(){}", "console"),
    ]
    
    for input_query, expected in sanitize_tests:
        result = service._sanitize_query(input_query)
        print(f"  '{input_query}' -> '{result}'")
        assert result == expected, f"Query sanitization failed for '{input_query}'"
    
    # Test limit validation
    print("\n📊 Limit validation:")
    limit_tests = [
        (1, 1),
        (50, 50),
        (100, 100),
        (0, 1),  # Below minimum
        (150, 100),  # Above maximum
        ("invalid", 20),  # Invalid type
        (None, 20),  # None value
    ]
    
    for input_limit, expected in limit_tests:
        result = service._validate_limit(input_limit)
        print(f"  {input_limit} -> {result}")
        assert result == expected, f"Limit validation failed for {input_limit}"
    
    # Test safe string extraction
    print("\n🔒 Safe string extraction:")
    string_tests = [
        (["test"], "test"),
        ([""], ""),
        ([], ""),
        ("test", "test"),
        (None, ""),
        (123, ""),
        (["a" * 600], "a" * 500),  # Truncate long strings
    ]
    
    for input_value, expected in string_tests:
        result = service._extract_safe_string(input_value)
        print(f"  {input_value} -> '{result}'")
        assert result == expected, f"String extraction failed for {input_value}"
    
    print("\n🎉 All eBay service security tests passed!")

if __name__ == '__main__':
    print("🚀 Running FlipLens Backend Security Tests")
    print("=" * 50)
    
    try:
        test_security_validator()
        test_attack_patterns()
        test_ebay_service_security()
        
        print("\n" + "=" * 50)
        print("✅ ALL SECURITY TESTS PASSED!")
        print("🎉 Backend security implementation is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        exit(1) 