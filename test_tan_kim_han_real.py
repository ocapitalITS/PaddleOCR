#!/usr/bin/env python3
"""Test TAN KIM HAN with actual fastapi_app functions"""

import sys
import os

# Add PaddleOCR to path
sys.path.insert(0, r'C:\laragon\www\PaddleOCR')
os.chdir(r'C:\laragon\www\PaddleOCR')

# Import just the processing functions without initializing PaddleOCR
from fastapi_app import process_ocr_text

# Raw OCR text from the user's API response
raw_ocr_text = [
    "970602-04-5335",
    "MELAKA",
    "75050 MELAKA",
    "RUMAH PANGSA AIR LELEH",
    "A22",
    "TAN KIM HAN",
    "WARGANEGARA",
    "LELAKI"
]

print("=" * 60)
print("TEST: TAN KIM HAN - Real API Processing")
print("=" * 60)
print(f"\nRaw OCR text from user feedback:")
for i, line in enumerate(raw_ocr_text):
    print(f"  {i}: {line}")

try:
    result = process_ocr_text(raw_ocr_text)
    
    print(f"\nProcessing Result:")
    print(f"  IC Number: {result.get('ic_number')}")
    print(f"  Name: {result.get('name')}")
    print(f"  Gender: {result.get('gender')}")
    print(f"  Address: {result.get('address')}")
    
    print(f"\n{'='*60}")
    print("VERIFICATION:")
    
    # Check name
    expected_name = "TAN KIM HAN"
    actual_name = result.get('name')
    name_match = actual_name == expected_name
    print(f"  Name: {actual_name} (expected '{expected_name}')")
    print(f"    {'✓ PASS' if name_match else '✗ FAIL'}")
    
    # Check address
    actual_address = result.get('address')
    expected_address_parts = ['A 22', 'RUMAH PANGSA AIR LELEH', '75050 MELAKA']
    if actual_address:
        address_match = all(part in actual_address for part in expected_address_parts)
        print(f"  Address: {actual_address}")
        print(f"    {'✓ PASS' if address_match else '✗ FAIL (missing address parts)'}")
    else:
        print(f"  Address: None (expected address with: {', '.join(expected_address_parts)})")
        print(f"    ✗ FAIL")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
