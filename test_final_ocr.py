"""
Extract and display OCR text lines
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi_app import ocr
from malaysia_ic_extractor_ultimate import UltimateICExtractor

image_path = r"IC\ic_front_20260204164113379.jpg"

print("Running OCR on image...")
results = ocr.predict(image_path)

ocr_result = results[0]

# Extract text lines
text_lines = []
if hasattr(ocr_result, 'rec_texts'):
    text_lines = list(ocr_result.rec_texts)
elif 'rec_texts' in ocr_result:
    text_lines = list(ocr_result['rec_texts'])
else:
    # Try to find it in the dict
    print("Available keys: " + str(list(ocr_result.keys())[:10]))

if text_lines:
    print("\n" + "="*80)
    print("RAW OCR OUTPUT (" + str(len(text_lines)) + " lines)")
    print("="*80)
    
    for idx, text in enumerate(text_lines):
        print("[" + str(idx).rjust(2) + "] " + text)
    
    print("\n" + "="*80)
    print("EXTRACTION TEST")
    print("="*80)
    
    # Test extraction
    extractor = UltimateICExtractor()
    result = extractor.extract(text_lines)
    
    print("\nExtracted IC Data:")
    print("  IC Number: " + result['ic_number'])
    print("  Name:      " + result['name'])
    print("  Address:   " + result['address'])
    print("  Gender:    " + (result['gender'] or 'N/A'))
    print("  Religion:  " + (result['religion'] or 'N/A'))
else:
    print("Could not extract text lines from OCR result")
    print("OCR result keys: " + str(list(ocr_result.keys())[:20]))
