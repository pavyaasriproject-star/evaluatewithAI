#!/usr/bin/env python3

import requests
import sys
import json
import base64
from datetime import datetime
from pathlib import Path
import io
from PIL import Image, ImageDraw
import fitz  # PyMuPDF for creating test PDFs

class PDFConversionTester:
    def __init__(self, base_url="https://instant-feedback-hub-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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

    def create_test_pdf(self, content_text, filename="test.pdf"):
        """Create a test PDF with actual content using PyMuPDF"""
        try:
            # Create a new PDF document
            doc = fitz.open()
            page = doc.new_page()
            
            # Add text content to the page
            text_lines = [
                "QUESTION PAPER - CA Foundation",
                "",
                "Q1: What is the basic accounting equation?",
                "    (a) Assets = Liabilities + Equity",
                "    (b) Assets = Liabilities - Equity", 
                "    (c) Assets + Liabilities = Equity",
                "    (d) None of the above",
                "",
                "Q2: Calculate the depreciation for an asset worth ₹100,000",
                "    with 10% depreciation rate.",
                "",
                "Q3: Define Working Capital and its importance.",
                "",
                "Working Notes:",
                "WN1: Asset calculation",
                "WN2: Depreciation formula",
                "WN3: Working capital analysis"
            ]
            
            y_position = 50
            for line in text_lines:
                page.insert_text((50, y_position), line, fontsize=12, color=(0, 0, 0))
                y_position += 20
            
            # Save to bytes
            pdf_bytes = doc.tobytes()
            doc.close()
            
            # Convert to base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode()
            return pdf_base64
            
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return None

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

    def test_pdf_to_image_conversion(self):
        """Test PDF to image conversion in analyze endpoint"""
        try:
            print("🔄 Creating test PDF documents...")
            
            # Create test PDFs with real content
            question_pdf = self.create_test_pdf("QUESTION PAPER")
            answer_key_pdf = self.create_test_pdf("ANSWER KEY")
            script_pdf = self.create_test_pdf("STUDENT ANSWER SCRIPT")
            
            if not all([question_pdf, answer_key_pdf, script_pdf]):
                self.log_test("PDF Creation", False, "Failed to create test PDFs")
                return False
            
            self.log_test("PDF Creation", True, "Successfully created test PDFs")

            payload = {
                "question_paper": question_pdf,
                "answer_key": answer_key_pdf,
                "answer_script": script_pdf,
                "question_mime": "application/pdf",
                "key_mime": "application/pdf", 
                "script_mime": "application/pdf"
            }

            print("🔄 Sending PDF analysis request (this may take 60-90 seconds)...")
            response = requests.post(f"{self.api_url}/analyze", json=payload, timeout=180)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Score: {data.get('score_percentage', 0):.1f}%"
                details += f", Errors: {len(data.get('errors', []))}"
                details += f", Strengths: {len(data.get('strengths', []))}"
                details += f", Working Notes: {len(data.get('working_notes_found', []))}"
                
                # Verify the response structure
                required_fields = ['score_percentage', 'total_marks', 'obtained_marks', 'errors', 'strengths', 'improvements', 'overall_feedback']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    details += ", All required fields present"
                    
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("PDF to Image Conversion", success, details)
            return success
            
        except Exception as e:
            self.log_test("PDF to Image Conversion", False, f"Error: {str(e)}")
            return False

    def test_mixed_format_analysis(self):
        """Test analysis with mixed PDF and image formats"""
        try:
            print("🔄 Testing mixed format analysis...")
            
            # Create mixed formats: PDF question paper, image answer key, PDF script
            question_pdf = self.create_test_pdf("QUESTION PAPER")
            answer_key_img = self.create_test_image("ANSWER KEY\nQ1: 4 (2 marks)\nQ2: x=4 (3 marks)")
            script_pdf = self.create_test_pdf("STUDENT ANSWER SCRIPT")
            
            if not all([question_pdf, answer_key_img, script_pdf]):
                self.log_test("Mixed Format Creation", False, "Failed to create test documents")
                return False

            payload = {
                "question_paper": question_pdf,
                "answer_key": answer_key_img,
                "answer_script": script_pdf,
                "question_mime": "application/pdf",
                "key_mime": "image/jpeg",
                "script_mime": "application/pdf"
            }

            print("🔄 Sending mixed format analysis request...")
            response = requests.post(f"{self.api_url}/analyze", json=payload, timeout=180)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Score: {data.get('score_percentage', 0):.1f}%"
                details += ", Mixed format processing successful"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Mixed Format Analysis", success, details)
            return success
            
        except Exception as e:
            self.log_test("Mixed Format Analysis", False, f"Error: {str(e)}")
            return False

    def test_corrupted_pdf_handling(self):
        """Test error handling for corrupted/invalid PDFs"""
        try:
            print("🔄 Testing corrupted PDF handling...")
            
            # Create invalid PDF data
            invalid_pdf = base64.b64encode(b"This is not a valid PDF file").decode()
            valid_img = self.create_test_image("ANSWER KEY")
            
            payload = {
                "question_paper": invalid_pdf,
                "answer_key": valid_img,
                "answer_script": valid_img,
                "question_mime": "application/pdf",
                "key_mime": "image/jpeg",
                "script_mime": "image/jpeg"
            }

            response = requests.post(f"{self.api_url}/analyze", json=payload, timeout=60)
            
            # Should return 400 error for invalid PDF
            success = response.status_code == 400
            details = f"Status: {response.status_code}"
            
            if success:
                try:
                    error_data = response.json()
                    details += f", Error message: {error_data.get('detail', 'No error message')}"
                except:
                    details += ", Error response received"
            else:
                details += f" (Expected 400 for invalid PDF)"

            self.log_test("Corrupted PDF Handling", success, details)
            return success
            
        except Exception as e:
            self.log_test("Corrupted PDF Handling", False, f"Error: {str(e)}")
            return False

    def test_batch_pdf_analysis(self):
        """Test batch analysis with PDF files"""
        try:
            print("🔄 Testing batch PDF analysis...")
            
            # Create test documents
            question_pdf = self.create_test_pdf("QUESTION PAPER")
            answer_key_pdf = self.create_test_pdf("ANSWER KEY")
            script1_pdf = self.create_test_pdf("STUDENT 1 ANSWER SCRIPT")
            script2_pdf = self.create_test_pdf("STUDENT 2 ANSWER SCRIPT")
            
            if not all([question_pdf, answer_key_pdf, script1_pdf, script2_pdf]):
                self.log_test("Batch PDF Creation", False, "Failed to create test PDFs")
                return False

            payload = {
                "question_paper": question_pdf,
                "answer_key": answer_key_pdf,
                "answer_scripts": [script1_pdf, script2_pdf],
                "question_mime": "application/pdf",
                "key_mime": "application/pdf",
                "script_mimes": ["application/pdf", "application/pdf"]
            }

            print("🔄 Sending batch PDF analysis request...")
            response = requests.post(f"{self.api_url}/analyze-batch", json=payload, timeout=300)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                results = data.get('results', [])
                total = data.get('total', 0)
                successful_results = [r for r in results if r.get('status') == 'success']
                
                details += f", Total scripts: {total}"
                details += f", Successful: {len(successful_results)}"
                
                if len(successful_results) == total:
                    details += ", All batch PDFs processed successfully"
                else:
                    success = False
                    details += f", {total - len(successful_results)} failed"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"

            self.log_test("Batch PDF Analysis", success, details)
            return success
            
        except Exception as e:
            self.log_test("Batch PDF Analysis", False, f"Error: {str(e)}")
            return False

    def run_pdf_tests(self):
        """Run all PDF-specific tests"""
        print("🚀 Starting PDF Conversion Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Test PDF conversion functionality
        self.test_pdf_to_image_conversion()
        self.test_mixed_format_analysis()
        self.test_corrupted_pdf_handling()
        self.test_batch_pdf_analysis()

        print("=" * 60)
        print(f"📊 PDF Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All PDF tests passed!")
            return 0
        else:
            print("⚠️  Some PDF tests failed. Check details above.")
            return 1

def main():
    tester = PDFConversionTester()
    return tester.run_pdf_tests()

if __name__ == "__main__":
    sys.exit(main())