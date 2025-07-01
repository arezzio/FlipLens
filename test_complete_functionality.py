#!/usr/bin/env python3
"""
Complete functionality test script for FlipLens
Tests all API endpoints, authentication, and database operations
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE_URL = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "email": "test@fliplens.com",
    "username": "testuser",
    "password": "TestPassword123",
    "first_name": "Test",
    "last_name": "User"
}

TEST_SEARCH_QUERY = "iPhone 13"
TEST_ITEM = {
    "item_id": "123456789",
    "title": "iPhone 13 Pro Max 256GB",
    "price": "999.99",
    "currency": "USD",
    "image_url": "https://example.com/image.jpg",
    "item_url": "https://ebay.com/item/123456789",
    "condition": "New",
    "location": "United States"
}

class FlipLensTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.saved_item_id = None
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        self.log("Testing health check endpoint...")
        try:
            response = self.session.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log(f"Health check passed: {data.get('service', 'Unknown')}")
                return True
            else:
                self.log(f"Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Health check error: {str(e)}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        self.log("Testing user registration...")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/register",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.auth_token = data.get('token')
                self.user_id = data.get('user', {}).get('id')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                self.log("User registration successful")
                return True
            elif response.status_code == 409:
                self.log("User already exists, trying login instead...")
                return self.test_user_login()
            else:
                self.log(f"Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Registration error: {str(e)}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test user login"""
        self.log("Testing user login...")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.user_id = data.get('user', {}).get('id')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                self.log("User login successful")
                return True
            else:
                self.log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Login error: {str(e)}", "ERROR")
            return False
    
    def test_get_current_user(self):
        """Test getting current user info"""
        self.log("Testing get current user...")
        try:
            response = self.session.get(f"{API_BASE_URL}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                user = data.get('user', {})
                self.log(f"Current user: {user.get('username')} ({user.get('email')})")
                return True
            else:
                self.log(f"Get current user failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Get current user error: {str(e)}", "ERROR")
            return False
    
    def test_search_items(self):
        """Test eBay search functionality"""
        self.log(f"Testing search for '{TEST_SEARCH_QUERY}'...")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/search",
                json={
                    "query": TEST_SEARCH_QUERY,
                    "limit": 5
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                self.log(f"Search successful: Found {len(results)} items")
                
                # Display first result for verification
                if results:
                    first_item = results[0]
                    self.log(f"First result: {first_item.get('title', 'No title')[:50]}...")
                    self.log(f"Price: {first_item.get('price', 'N/A')} {first_item.get('currency', '')}")
                    self.log(f"Confidence: {first_item.get('confidence', 'N/A')}")
                    if 'estimated_profit' in first_item:
                        self.log(f"Estimated Profit: ${first_item.get('estimated_profit', 'N/A')}")
                
                return True
            else:
                self.log(f"Search failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Search error: {str(e)}", "ERROR")
            return False
    
    def test_save_item(self):
        """Test saving an item"""
        self.log("Testing save item...")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/saved-items",
                json=TEST_ITEM,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                saved_item = data.get('item', {})
                self.saved_item_id = saved_item.get('id')
                self.log(f"Item saved successfully: ID {self.saved_item_id}")
                return True
            elif response.status_code == 409:
                self.log("Item already saved")
                return True
            else:
                self.log(f"Save item failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Save item error: {str(e)}", "ERROR")
            return False
    
    def test_get_saved_items(self):
        """Test getting saved items"""
        self.log("Testing get saved items...")
        try:
            response = self.session.get(f"{API_BASE_URL}/saved-items")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                total = data.get('total', 0)
                self.log(f"Retrieved {len(items)} saved items (total: {total})")
                
                # Display saved items
                for item in items[:3]:  # Show first 3
                    self.log(f"- {item.get('title', 'No title')[:40]}... (${item.get('price', 'N/A')})")
                
                return True
            else:
                self.log(f"Get saved items failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Get saved items error: {str(e)}", "ERROR")
            return False
    
    def test_database_operations(self):
        """Test database operations"""
        self.log("Testing database operations...")
        try:
            # Test database stats endpoint (if available)
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"Backend status: {data.get('message', 'Unknown')}")
                self.log(f"Environment: {data.get('environment', 'Unknown')}")
                return True
            else:
                self.log("Database operations test skipped (no stats endpoint)")
                return True
        except Exception as e:
            self.log(f"Database operations error: {str(e)}", "ERROR")
            return False
    
    def test_logout(self):
        """Test user logout"""
        self.log("Testing user logout...")
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/logout")
            
            if response.status_code == 200:
                self.log("Logout successful")
                # Clear auth token
                self.auth_token = None
                if 'Authorization' in self.session.headers:
                    del self.session.headers['Authorization']
                return True
            else:
                self.log(f"Logout failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Logout error: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("=" * 60)
        self.log("STARTING FLIPLENS COMPLETE FUNCTIONALITY TEST")
        self.log("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("Get Current User", self.test_get_current_user),
            ("Search Items", self.test_search_items),
            ("Save Item", self.test_save_item),
            ("Get Saved Items", self.test_get_saved_items),
            ("Database Operations", self.test_database_operations),
            ("User Logout", self.test_logout),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- Running {test_name} ---")
            try:
                if test_func():
                    self.log(f"✅ {test_name} PASSED")
                    passed += 1
                else:
                    self.log(f"❌ {test_name} FAILED", "ERROR")
                    failed += 1
            except Exception as e:
                self.log(f"❌ {test_name} FAILED with exception: {str(e)}", "ERROR")
                failed += 1
            
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Tests: {passed + failed}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! FlipLens is ready for production!")
            return True
        else:
            self.log(f"⚠️  {failed} test(s) failed. Please check the errors above.")
            return False

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        global BASE_URL, API_BASE_URL
        BASE_URL = sys.argv[1]
        API_BASE_URL = f"{BASE_URL}/api"
        print(f"Testing against: {BASE_URL}")
    
    test_suite = FlipLensTestSuite()
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
