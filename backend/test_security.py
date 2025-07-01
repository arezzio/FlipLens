"""
Security tests for FlipLens backend
Tests input validation, sanitization, and security features
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSecurityValidator(unittest.TestCase):
    """Test security validation utilities"""
    
    def setUp(self):
        from utils.security import SecurityValidator
        self.validator = SecurityValidator
    
    def test_validate_string_valid_query(self):
        """Test valid query string validation"""
        valid_queries = [
            "nike shoes",
            "iPhone 13",
            "laptop computer",
            "gaming console",
            "books and magazines"
        ]
        
        for query in valid_queries:
            with self.subTest(query=query):
                self.assertTrue(self.validator.validate_string(query, 'query'))
    
    def test_validate_string_invalid_query(self):
        """Test invalid query string validation"""
        invalid_queries = [
            "nike<script>alert('xss')</script>",
            "iPhone'; DROP TABLE users; --",
            "laptop<>&\"'",
            "console|`$(){}",
            "books; rm -rf /"
        ]
        
        for query in invalid_queries:
            with self.subTest(query=query):
                self.assertFalse(self.validator.validate_string(query, 'query'))
    
    def test_validate_string_length_limit(self):
        """Test string length validation"""
        # Test within limit
        short_query = "test"
        self.assertTrue(self.validator.validate_string(short_query, 'query', max_length=10))
        
        # Test at limit
        limit_query = "a" * 10
        self.assertTrue(self.validator.validate_string(limit_query, 'query', max_length=10))
        
        # Test over limit
        long_query = "a" * 11
        self.assertFalse(self.validator.validate_string(long_query, 'query', max_length=10))
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        test_cases = [
            ("<script>alert('xss')</script>", "scriptalertxssscript"),
            ("nike'; DROP TABLE users; --", "nike DROP TABLE users"),
            ("iPhone<>&\"'", "iPhone"),
            ("laptop|`$(){}", "laptop"),
            ("books; rm -rf /", "books rm -rf"),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = self.validator.sanitize_string(input_str)
                self.assertEqual(result, expected)
    
    def test_validate_json_structure(self):
        """Test JSON structure validation"""
        # Valid structure
        valid_data = {"query": "test", "limit": 10}
        is_valid, error_msg = self.validator.validate_json_structure(
            valid_data, ["query"], {"limit": int}
        )
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # Missing required field
        invalid_data = {"limit": 10}
        is_valid, error_msg = self.validator.validate_json_structure(
            invalid_data, ["query"], {"limit": int}
        )
        self.assertFalse(is_valid)
        self.assertIn("Missing required field", error_msg)
        
        # Invalid type
        invalid_data = {"query": "test", "limit": "not_a_number"}
        is_valid, error_msg = self.validator.validate_json_structure(
            invalid_data, ["query"], {"limit": int}
        )
        self.assertFalse(is_valid)
        self.assertIn("Invalid type", error_msg)

class TestEbayServiceSecurity(unittest.TestCase):
    """Test eBay service security features"""
    
    def setUp(self):
        with patch('flask.current_app'):
            from services.ebay_service import EbayService
            self.service = EbayService()
    
    def test_sanitize_query(self):
        """Test query sanitization in eBay service"""
        test_cases = [
            ("nike shoes", "nike shoes"),
            ("<script>alert('xss')</script>", "scriptalertxssscript"),
            ("iPhone'; DROP TABLE users; --", "iPhone DROP TABLE users"),
            ("laptop<>&\"'", "laptop"),
            ("console|`$(){}", "console"),
        ]
        
        for input_query, expected in test_cases:
            with self.subTest(query=input_query):
                result = self.service._sanitize_query(input_query)
                self.assertEqual(result, expected)
    
    def test_validate_limit(self):
        """Test limit validation in eBay service"""
        test_cases = [
            (1, 1),
            (50, 50),
            (100, 100),
            (0, 1),  # Below minimum
            (150, 100),  # Above maximum
            ("invalid", 20),  # Invalid type
            (None, 20),  # None value
        ]
        
        for input_limit, expected in test_cases:
            with self.subTest(limit=input_limit):
                result = self.service._validate_limit(input_limit)
                self.assertEqual(result, expected)
    
    def test_extract_safe_string(self):
        """Test safe string extraction from eBay response"""
        test_cases = [
            (["test"], "test"),
            ([""], ""),
            ([], ""),
            ("test", "test"),
            (None, ""),
            (123, ""),
            (["a" * 600], "a" * 500),  # Truncate long strings
        ]
        
        for input_value, expected in test_cases:
            with self.subTest(value=input_value):
                result = self.service._extract_safe_string(input_value)
                self.assertEqual(result, expected)

class TestSecurityHeaders(unittest.TestCase):
    """Test security headers middleware"""
    
    def setUp(self):
        from utils.security import SecurityHeaders
        self.headers = SecurityHeaders
    
    def test_add_security_headers(self):
        """Test security headers are added correctly"""
        from flask import Response
        
        # Create a mock response
        response = Response("test")
        
        # Add security headers
        result = self.headers.add_security_headers(response)
        
        # Check that security headers are present
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Content-Security-Policy',
            'Referrer-Policy'
        ]
        
        for header in expected_headers:
            self.assertIn(header, result.headers)
        
        # Check specific header values
        self.assertEqual(result.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(result.headers['X-XSS-Protection'], '1; mode=block')
        self.assertIn("default-src 'self'", result.headers['Content-Security-Policy'])

class TestInputValidation(unittest.TestCase):
    """Test input validation decorators"""
    
    def setUp(self):
        from utils.security import InputValidation
        self.validation = InputValidation
    
    @patch('flask.request')
    def test_validate_search_input_valid(self, mock_request):
        """Test valid search input validation"""
        # Mock request data
        mock_request.is_json = True
        mock_request.get_json.return_value = {"query": "nike shoes", "limit": 10}
        mock_request.remote_addr = "127.0.0.1"
        
        # Create a mock function
        mock_func = MagicMock()
        mock_func.return_value = {"status": "success"}
        
        # Apply validation decorator
        decorated_func = self.validation.validate_search_input(mock_func)
        
        # Call the decorated function
        result = decorated_func()
        
        # Check that the function was called
        mock_func.assert_called_once()
        self.assertEqual(result, {"status": "success"})
    
    @patch('flask.request')
    def test_validate_search_input_invalid_content_type(self, mock_request):
        """Test invalid content type handling"""
        # Mock request with invalid content type
        mock_request.is_json = False
        mock_request.remote_addr = "127.0.0.1"
        
        # Create a mock function
        mock_func = MagicMock()
        
        # Apply validation decorator
        decorated_func = self.validation.validate_search_input(mock_func)
        
        # Call the decorated function
        result = decorated_func()
        
        # Check that the function was not called and error was returned
        mock_func.assert_not_called()
        self.assertIn("Invalid Content-Type", result[0].get_json()["error"])
        self.assertEqual(result[1], 415)
    
    @patch('flask.request')
    def test_validate_search_input_malicious_query(self, mock_request):
        """Test malicious query handling"""
        # Mock request with malicious query
        mock_request.is_json = True
        mock_request.get_json.return_value = {"query": "<script>alert('xss')</script>", "limit": 10}
        mock_request.remote_addr = "127.0.0.1"
        
        # Create a mock function
        mock_func = MagicMock()
        
        # Apply validation decorator
        decorated_func = self.validation.validate_search_input(mock_func)
        
        # Call the decorated function
        result = decorated_func()
        
        # Check that the function was not called and error was returned
        mock_func.assert_not_called()
        self.assertIn("Invalid Query Format", result[0].get_json()["error"])
        self.assertEqual(result[1], 400)

class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for security features"""
    
    def test_security_patterns_comprehensive(self):
        """Test that security patterns cover common attack vectors"""
        from utils.security import SecurityValidator
        
        # Test XSS patterns
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "onload=alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
        ]
        
        for payload in xss_payloads:
            with self.subTest(payload=payload):
                # All XSS payloads should be rejected
                self.assertFalse(SecurityValidator.validate_string(payload, 'query'))
        
        # Test SQL injection patterns
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR 1=1 --",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        ]
        
        for payload in sql_payloads:
            with self.subTest(payload=payload):
                # All SQL injection payloads should be rejected
                self.assertFalse(SecurityValidator.validate_string(payload, 'query'))
        
        # Test command injection patterns
        cmd_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "`whoami`",
            "$(id)",
            "& del C:\\Windows\\System32",
        ]
        
        for payload in cmd_payloads:
            with self.subTest(payload=payload):
                # All command injection payloads should be rejected
                self.assertFalse(SecurityValidator.validate_string(payload, 'query'))

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 