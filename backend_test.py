#!/usr/bin/env python3

import requests
import sys
import json
import base64
from datetime import datetime
from pathlib import Path
import io
from PIL import Image, ImageDraw

class ArivuProAPITester:
    def __init__(self, base_url="https://instant-feedback-hub-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()  # For cookie persistence
        self.user_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")

    def create_test_image(self, text="Sample Text", width=800, height=600):
        """Create a test image with text content"""
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some text content
        draw.text((50, 50), text, fill='black')
        draw.text((50, 100), "Question 1: What is 2+2?", fill='black')
        draw.text((50, 150), "Answer: 4", fill='black')
        draw.text((50, 200), "Working Notes: WN1", fill='black')
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64

    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Service: {data.get('service', 'Unknown')}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            self.log_test("Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
            return False

    def test_analyze_endpoint_validation(self):
        """Test analyze endpoint with invalid data"""
        try:
            # Test with missing data
            response = requests.post(f"{self.api_url}/analyze", json={}, timeout=30)
            success = response.status_code == 422  # Validation error expected
            details = f"Status: {response.status_code} (Expected 422 for validation error)"
            self.log_test("Analyze Validation", success, details)
            return success
        except Exception as e:
            self.log_test("Analyze Validation", False, f"Error: {str(e)}")
            return False

    def test_analyze_endpoint_full(self):
        """Test analyze endpoint with valid data"""
        try:
            # Create test images
            question_img = self.create_test_image("QUESTION PAPER\nQ1: What is 2+2?\nQ2: Solve x+3=7")
            answer_key_img = self.create_test_image("ANSWER KEY\nQ1: 4 (2 marks)\nQ2: x=4 (3 marks)")
            script_img = self.create_test_image("STUDENT ANSWER\nQ1: 4 WN1\nQ2: x=4 WN2")

            payload = {
                "question_paper": question_img,
                "answer_key": answer_key_img,
                "answer_script": script_img,
                "question_mime": "image/jpeg",
                "key_mime": "image/jpeg",
                "script_mime": "image/jpeg"
            }

            print("🔄 Sending analysis request (this may take 30-60 seconds)...")
            response = requests.post(f"{self.api_url}/analyze", json=payload, timeout=120)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Score: {data.get('score_percentage', 0):.1f}%"
                details += f", Errors: {len(data.get('errors', []))}"
                details += f", Strengths: {len(data.get('strengths', []))}"
                
                # Store result for PDF test
                self.analysis_result = data
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Analyze Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Analyze Endpoint", False, f"Error: {str(e)}")
            return False

    def test_auth_login(self):
        """Test user authentication"""
        try:
            # Test login with test credentials
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
                self.user_id = data.get('id')
                
                # Check if cookies are set
                if 'access_token' in response.cookies:
                    details += ", Auth cookies set"
                else:
                    details += ", No auth cookies"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Auth Login", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Login", False, f"Error: {str(e)}")
            return False

    def test_auth_me(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", User: {data.get('name', 'Unknown')}"
                details += f", Email: {data.get('email', 'Unknown')}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Auth Me", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me", False, f"Error: {str(e)}")
            return False

    def test_performance_endpoint(self):
        """Test performance history endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/performance", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                records = data.get('records', [])
                details += f", Records: {len(records)}"
                
                if records:
                    latest = records[0]
                    details += f", Latest Score: {latest.get('score_percentage', 0):.1f}%"
                    details += f", Timestamp: {latest.get('timestamp', 'Unknown')}"
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

    def test_analyze_endpoint_full(self):
        """Test analyze endpoint with valid data and verify performance save"""
        try:
            # Create test images
            question_img = self.create_test_image("QUESTION PAPER\nQ1: What is 2+2?\nQ2: Solve x+3=7")
            answer_key_img = self.create_test_image("ANSWER KEY\nQ1: 4 (2 marks)\nQ2: x=4 (3 marks)")
            script_img = self.create_test_image("STUDENT ANSWER\nQ1: 4 WN1\nQ2: x=4 WN2")

            payload = {
                "question_paper": question_img,
                "answer_key": answer_key_img,
                "answer_script": script_img,
                "question_mime": "image/jpeg",
                "key_mime": "image/jpeg",
                "script_mime": "image/jpeg"
            }

            print("🔄 Sending analysis request (this may take 30-60 seconds)...")
            response = self.session.post(f"{self.api_url}/analyze", json=payload, timeout=120)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Score: {data.get('score_percentage', 0):.1f}%"
                details += f", Errors: {len(data.get('errors', []))}"
                details += f", Strengths: {len(data.get('strengths', []))}"
                
                # Store result for PDF test
                self.analysis_result = data
                
                # Verify performance was saved by checking performance endpoint
                print("🔄 Checking if performance was saved to database...")
                perf_response = self.session.get(f"{self.api_url}/performance", timeout=10)
                if perf_response.status_code == 200:
                    perf_data = perf_response.json()
                    records = perf_data.get('records', [])
                    if records:
                        latest_record = records[0]
                        if latest_record.get('score_percentage') == data.get('score_percentage'):
                            details += ", Performance saved to DB ✓"
                        else:
                            details += ", Performance save verification failed"
                    else:
                        details += ", No performance records found"
                else:
                    details += ", Could not verify performance save"
                    
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Analyze Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Analyze Endpoint", False, f"Error: {str(e)}")
            return False

    def test_generate_report_endpoint(self):
        """Test PDF report generation with StreamingResponse"""
        if not hasattr(self, 'analysis_result'):
            self.log_test("Generate Report", False, "No analysis result available")
            return False

        try:
            payload = {
                "analysis_result": self.analysis_result,
                "student_name": "Test Student"
            }

            response = self.session.post(f"{self.api_url}/generate-report", json=payload, timeout=30)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                details += f", Content-Type: {content_type}"
                details += f", Size: {len(response.content)} bytes"
                
                # Check for proper StreamingResponse headers
                if 'attachment' in content_disposition:
                    details += ", Download headers present"
                else:
                    details += ", Missing download headers"
                
                # Verify it's a PDF
                if response.content.startswith(b'%PDF'):
                    details += ", Valid PDF"
                else:
                    success = False
                    details += ", Invalid PDF format"

            self.log_test("Generate Report", success, details)
            return success
        except Exception as e:
            self.log_test("Generate Report", False, f"Error: {str(e)}")
            return False

    def test_auth_logout(self):
        """Test user logout"""
        try:
            response = self.session.post(f"{self.api_url}/auth/logout", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"

            self.log_test("Auth Logout", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Logout", False, f"Error: {str(e)}")
            return False

    def test_cors_headers(self):
        """Test CORS headers"""
        try:
            response = requests.options(f"{self.api_url}/health", timeout=10)
            success = response.status_code in [200, 204]
            details = f"Status: {response.status_code}"
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if any(cors_headers.values()):
                details += ", CORS headers present"
            else:
                details += ", No CORS headers found"

            self.log_test("CORS Headers", success, details)
            return success
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting ArivuPro AI Backend Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Basic connectivity tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_cors_headers()
        
        # Authentication tests
        self.test_auth_login()
        self.test_auth_me()
        
        # Performance endpoint test
        self.test_performance_endpoint()
        
        # API validation tests
        self.test_analyze_endpoint_validation()
        
        # Full functionality tests (with performance save verification)
        self.test_analyze_endpoint_full()
        self.test_generate_report_endpoint()
        
        # Logout test
        self.test_auth_logout()

        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check details above.")
            return 1

def main():
    tester = ArivuProAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())