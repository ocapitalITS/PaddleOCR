"""
Safe OCR output extraction - handles Unicode
"""

import os
import sys
import codecs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

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

if text_lines:
    print("\nRAW OCR OUTPUT")
    print("="*80)
    print("Total lines: " + str(len(text_lines)))
    print("="*80 + "\n")
    
    for idx, text in enumerate(text_lines):
        # Safely encode text
        safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
        print("[" + str(idx).rjust(2) + "] " + safe_text)
    
    print("\n" + "="*80)
    print("EXTRACTION RESULTS")
    print("="*80)
    
    # Test extraction
    extractor = UltimateICExtractor()
    result = extractor.extract(text_lines)
    
    print("\nExtracted IC Data:")
    print("IC Number: " + result['ic_number'])
    print("Name:      " + result['name'])
    print("Address:   " + result['address'])
    print("Gender:    " + (result['gender'] if result['gender'] else 'Not found'))
    print("Religion:  " + (result['religion'] if result['religion'] else 'Not found'))
    
    print("\n" + "="*80)
else:
    print("ERROR: Could not extract text lines")
