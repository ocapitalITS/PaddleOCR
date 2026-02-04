#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify Malaysian IC OCR extraction with a real image file.
"""

import os
import sys
from malaysia_ic_ocr import extract_ic_fields

def test_ic_image(image_path):
    """Test IC extraction from image file"""
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Testing IC OCR: {os.path.basename(image_path)}")
    print(f"{'='*60}\n")
    
    try:
        result = extract_ic_fields(image_path)
        
        print("Extracted Results:")
        print("-" * 60)
        for key, value in result.items():
            print(f"{key:.<20} {value}")
        
        print("\n" + "="*60)
        return True
        
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test image path
    image_path = "ic_front_20260129230128930.jpg"
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    
    success = test_ic_image(image_path)
    sys.exit(0 if success else 1)
