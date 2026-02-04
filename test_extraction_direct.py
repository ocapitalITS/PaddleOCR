#!/usr/bin/env python
"""Test to see the actual name processing in extract_ic_fields"""
import sys
import cv2
from pathlib import Path

# Add paddleocr to path
sys.path.insert(0, '/c/laragon/www/PaddleOCR')

# Import the extraction function
from fastapi_app import extract_ic_fields

# Test with the image
image_path = Path('IC/ic_front_20260129230128930.jpg')

if image_path.exists():
    print(f"Testing with image: {image_path}")
    image = cv2.imread(str(image_path))
    
    result = extract_ic_fields(image)
    
    print("\nExtraction Result:")
    print(f"Name: {result.get('name', 'N/A')}")
    print(f"IC Number: {result.get('ic_number', 'N/A')}")
    print(f"Address: {result.get('address', 'N/A')}")
    print(f"\nRaw OCR Text:")
    for i, line in enumerate(result.get('raw_ocr_text', [])):
        print(f"  {i}: {line}")
else:
    print(f"Image not found at {image_path}")
