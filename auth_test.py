#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ArivuProAuthTester:
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

    def test_register_new_user(self):
        """Test user registration"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            payload = {
                "name": f"Test User {timestamp}",
                "email": f"testuser{timestamp}@test.com",
                "password": "testpass123",
                "course": "CA"
            }

            response = self.session.post(f"{self.api_url}/auth/register", json=payload, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('name')}, Course: {data.get('course')}"
                self.test_user_email = payload["email"]
                self.test_user_password = payload["password"]
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("User Registration", success, details)
            return success
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")
            return False

    def test_login_existing_user(self):
        """Test login with test credentials"""
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
                details += f", User: {data.get('name')}, Course: {data.get('course')}"
                # Check for cookies
                cookies = response.cookies
                if 'access_token' in cookies and 'refresh_token' in cookies:
                    details += ", Cookies set"
                else:
                    details += ", No cookies found"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("User Login", success, details)
            return success
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('name')}, Email: {data.get('email')}"
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

    def test_performance_endpoint(self):
        """Test performance endpoint (requires auth)"""
        try:
            response = self.session.get(f"{self.api_url}/performance", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                records = data.get('records', [])
                details += f", Records: {len(records)}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Performance Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Performance Endpoint", False, f"Error: {str(e)}")
            return False

    def test_career_advisor(self):
        """Test career advisor endpoint"""
        try:
            payload = {
                "question": "What are the career prospects for CA students?",
                "course": "CA"
            }

            print("🔄 Sending career advisor request (this may take 10-30 seconds)...")
            response = self.session.post(f"{self.api_url}/career-advisor", json=payload, timeout=60)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                response_text = data.get('response', '')
                details += f", Response length: {len(response_text)} chars"
                if len(response_text) > 50:
                    details += f", Preview: {response_text[:50]}..."
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
        """Test logout"""
        try:
            response = self.session.post(f"{self.api_url}/auth/logout", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"

            self.log_test("User Logout", success, details)
            return success
        except Exception as e:
            self.log_test("User Logout", False, f"Error: {str(e)}")
            return False

    def test_protected_route_after_logout(self):
        """Test that protected routes are blocked after logout"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
            success = response.status_code == 401  # Should be unauthorized
            details = f"Status: {response.status_code} (Expected 401 after logout)"

            self.log_test("Protected Route After Logout", success, details)
            return success
        except Exception as e:
            self.log_test("Protected Route After Logout", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all auth tests"""
        print("🔐 Starting ArivuPro AI Auth Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Test registration
        self.test_register_new_user()
        
        # Test login with existing user
        self.test_login_existing_user()
        
        # Test authenticated endpoints
        self.test_get_current_user()
        self.test_performance_endpoint()
        self.test_career_advisor()
        
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
    tester = ArivuProAuthTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())