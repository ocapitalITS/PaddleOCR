"""
Test OCR on the actual image using the existing setup
"""

import os
import io
from PIL import Image
import numpy as np

# Test image
image_path = r"IC\ic_front_20260204164113379.jpg"

print(f"Loading image: {image_path}")

# Load image
image = Image.open(image_path)
image = image.convert('RGB')
image_array = np.array(image)

print(f"Image size: {image_array.shape}")
print(f"Image format: {image.format}")

# Now import PaddleOCR from the fastapi setup
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from fastapi_app which has the correct setup
from fastapi_app import ocr

if ocr:
    print("\nOCR engine loaded")
    
    # Run OCR
    print("Running OCR on image...")
    results = ocr.predict(image_path)
    
    if results and results[0]:
        print("\n" + "="*80)
        print("RAW OCR OUTPUT (Line by line)")
        print("="*80)
        
        extracted = []
        # Check what format we got
        if results and len(results) > 0:
            first_result = results[0]
            if first_result and len(first_result) > 0:
                first_item = first_result[0]
                print("DEBUG: Item type: " + str(type(first_item)))
                print("DEBUG: Item: " + str(first_item)[:100])
        
        # Try to extract - format might be different with new PaddleOCR version
        try:
            for idx, item in enumerate(results[0]):
                # Handle different possible formats
                text = None
                if isinstance(item, dict) and 'text' in item:
                    text = item['text']
                elif isinstance(item, (list, tuple)):
                    if len(item) >= 2 and isinstance(item[-1], (list, tuple)) and len(item[-1]) >= 1:
                        text = item[-1][0]  # [[box], [text, conf]]
                    elif len(item) >= 1:
                        text = item[-1]
                else:
                    text = str(item)
                
                if text:
                    extracted.append(text)
                    print("[" + str(idx).rjust(2) + "] " + text)
        except Exception as e:
            print("Error parsing: " + str(e))
            print("Raw results[0][0]: " + str(results[0][0][:100] if results[0] else 'empty'))
        
        print("="*80)
        
        # Test with extraction
        print("\nTesting with extraction module...")
        from malaysia_ic_extractor_ultimate import UltimateICExtractor
        
        extractor = UltimateICExtractor()
        result = extractor.extract(extracted)
        
        print("\nExtracted IC Data:")
        print("   IC Number: " + result['ic_number'])
        print("   Name:      " + result['name'])
        print("   Address:   " + result['address'])
        print("   Gender:    " + (result['gender'] or 'N/A'))
        print("   Religion:  " + (result['religion'] or 'N/A'))
    else:
        print("No OCR results")
else:
    print("OCR engine not loaded")
