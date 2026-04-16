#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class AuthTester:
    def __init__(self, base_url="https://instant-feedback-hub-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")

    def test_login_with_test_credentials(self):
        """Test login with test student credentials"""
        try:
            payload = {
                "email": "teststudent@test.com",
                "password": "test123456"
            }
            
            response = self.session.post(f"{self.api_url}/auth/login", json=payload, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('name', 'Unknown')}"
                details += f", Course: {data.get('course', 'Unknown')}"
                details += f", Role: {data.get('role', 'Unknown')}"
                
                # Check if cookies are set
                cookies = response.cookies
                if 'access_token' in cookies and 'refresh_token' in cookies:
                    details += ", Auth cookies set"
                else:
                    details += ", No auth cookies"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Test Student Login", success, details)
            return success
            
        except Exception as e:
            self.log_test("Test Student Login", False, f"Error: {str(e)}")
            return False

    def test_login_with_admin_credentials(self):
        """Test login with admin credentials"""
        try:
            payload = {
                "email": "admin@arivupro.com",
                "password": "ArivuPro2026!"
            }
            
            response = self.session.post(f"{self.api_url}/auth/login", json=payload, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('name', 'Unknown')}"
                details += f", Role: {data.get('role', 'Unknown')}"
                
                # Check if cookies are set
                cookies = response.cookies
                if 'access_token' in cookies and 'refresh_token' in cookies:
                    details += ", Auth cookies set"
                else:
                    details += ", No auth cookies"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Admin Login", success, details)
            return success
            
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('name', 'Unknown')}"
                details += f", Email: {data.get('email', 'Unknown')}"
                details += f", Role: {data.get('role', 'Unknown')}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Get Current User", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Current User", False, f"Error: {str(e)}")
            return False

    def test_career_advisor(self):
        """Test career advisor endpoint"""
        try:
            payload = {
                "question": "What are the career prospects for CA students?",
                "course": "CA"
            }
            
            response = self.session.post(f"{self.api_url}/career-advisor", json=payload, timeout=60)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                response_text = data.get('response', '')
                details += f", Response length: {len(response_text)} chars"
                if len(response_text) > 50:
                    details += ", Valid AI response received"
                else:
                    success = False
                    details += ", Response too short"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Career Advisor", success, details)
            return success
            
        except Exception as e:
            self.log_test("Career Advisor", False, f"Error: {str(e)}")
            return False

    def test_logout(self):
        """Test logout functionality"""
        try:
            response = self.session.post(f"{self.api_url}/auth/logout", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
                
                # Check if cookies are cleared
                cookies = response.cookies
                if 'access_token' in cookies or 'refresh_token' in cookies:
                    details += ", Cookies cleared"
                else:
                    details += ", No cookie clearing detected"

            self.log_test("Logout", success, details)
            return success
            
        except Exception as e:
            self.log_test("Logout", False, f"Error: {str(e)}")
            return False

    def test_protected_route_after_logout(self):
        """Test that protected routes are blocked after logout"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
            success = response.status_code == 401  # Should be unauthorized
            details = f"Status: {response.status_code} (Expected 401 after logout)"
            
            if success:
                details += ", Protected route correctly blocked"
            else:
                details += ", Protected route not properly blocked"

            self.log_test("Protected Route After Logout", success, details)
            return success
            
        except Exception as e:
            self.log_test("Protected Route After Logout", False, f"Error: {str(e)}")
            return False

    def run_auth_tests(self):
        """Run all auth tests"""
        print("🚀 Starting Auth Flow Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Test login flows
        self.test_login_with_test_credentials()
        self.test_get_current_user()
        self.test_career_advisor()
        
        # Test admin login
        self.test_login_with_admin_credentials()
        self.test_get_current_user()
        
        # Test logout
        self.test_logout()
        self.test_protected_route_after_logout()

        print("=" * 60)
        print(f"📊 Auth Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All auth tests passed!")
            return 0
        else:
            print("⚠️  Some auth tests failed. Check details above.")
            return 1

def main():
    tester = AuthTester()
    return tester.run_auth_tests()

if __name__ == "__main__":
    sys.exit(main())