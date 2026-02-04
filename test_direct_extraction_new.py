#!/usr/bin/env python3
"""Test name/address extraction with actual sample from 890925-02-5451"""
import sys
sys.path.insert(0, 'c:\\laragon\\www\\PaddleOCR')

from fastapi_app import extract_fields, split_malay_words, correct_ocr_errors

# Simulate the raw OCR text extracted from the image
raw_ocr_text = [
    "KADPENGENALAN",
    "MALAY",
    "MyKad",
    "IDENTLTY",
    "CARD",
    "890925-02-5451",
    "NIKAMINBIN MATZIN",
    "KAMPUNG ALOR TERJUN",
    "NO 25",
    "KOTA SARANG SEMUT",
    "06800 ALORSETAR",
    "WARGANEGARA",
    "KEDAH",
    "ISLAM",
    "LELAKI"
]

print("Raw OCR Text:")
for line in raw_ocr_text:
    print(f"  {line}")

print("\n" + "="*60)
print("Testing extraction:")
print("="*60 + "\n")

# Call extract_fields
try:
    results = extract_fields(raw_ocr_text, best_angle=0)
    print("✅ Extraction successful!\n")
    print(f"IC Number: {results['ic_number']}")
    print(f"Name: {results['name']}")
    print(f"Gender: {results['gender']}")
    print(f"Religion: {results['religion']}")
    print(f"Address: {results['address']}")
    print(f"Document Type: {results['document_type']}")
    
    # Verify the name and address are split correctly
    print("\n" + "="*60)
    print("VERIFICATION:")
    print("="*60)
    if "NIK AMIN BIN MAT ZIN" in (results['name'] or ""):
        print("✅ Name correctly split: NIK AMIN BIN MAT ZIN")
    else:
        print(f"❌ Name NOT split correctly: {results['name']}")
    
    if "ALOR SETAR" in (results['address'] or ""):
        print("✅ Address correctly split: Contains ALOR SETAR")
    else:
        print(f"❌ Address NOT split correctly: {results['address']}")
        
except Exception as e:
    print(f"❌ Extraction failed: {e}")
    import traceback
    traceback.print_exc()
