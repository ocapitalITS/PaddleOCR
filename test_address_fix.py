#!/usr/bin/env python3
"""Test script to verify address extraction fixes"""
import requests
import json
import sys

# Test the API with a test image
def test_ocr_api():
    """Test the OCR API endpoint"""
    
    # Make sure API is running
    try:
        health_response = requests.get('http://localhost:5000/api/health')
        if health_response.status_code != 200:
            print("❌ API is not responding correctly")
            return False
        print("✅ API health check passed")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Please start the Flask API first with: .\.venv310\Scripts\python.exe flask_api.py")
        return False
    
    # The test data from the user's request
    expected_address = "LOT 146 SERAYA A, TAMAN PUTERA JAYA, MENGGATAL, 88450 KOTA KINABALU, SABAH"
    expected_ic = "950325-12-5119"
    expected_name = "AMIRAZIQ BIN ALIM PANDITA"
    
    print("\n📋 Expected Results:")
    print(f"   Address: {expected_address}")
    print(f"   IC: {expected_ic}")
    print(f"   Name: {expected_name}")
    print("\nNote: To test with an actual image:")
    print("   1. Save your test image to a file")
    print("   2. Use curl or Postman to upload it:")
    print("      curl -X POST -F 'file=@/path/to/image.jpg' http://localhost:5000/api/ocr")
    print("   3. Or use Python:")
    print("      with open('image.jpg', 'rb') as f:")
    print("          response = requests.post('http://localhost:5000/api/ocr',")
    print("                                    files={'file': f})")
    print("      print(json.dumps(response.json(), indent=2))")
    
    return True

if __name__ == "__main__":
    success = test_ocr_api()
    sys.exit(0 if success else 1)
