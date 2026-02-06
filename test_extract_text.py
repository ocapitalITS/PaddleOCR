"""
Extract OCR text from the new PaddleX OCRResult format
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi_app import ocr

image_path = r"IC\ic_front_20260204164113379.jpg"

print("Running OCR on: " + image_path)
results = ocr.predict(image_path)

print("Result type: " + str(type(results[0])))

# Get the OCR result
ocr_result = results[0]

# Try to access the text data
print("\nAttempting to extract text...")

# Check what attributes/methods are available
print("Available attributes: " + str(dir(ocr_result))[:200])

# Try to get the text
if hasattr(ocr_result, 'text'):
    print("Has 'text' attribute")
    text = ocr_result.text
    print("Text type: " + str(type(text)))
    print("Text: " + str(text)[:300])

if hasattr(ocr_result, 'to_dict'):
    print("\nConverting to dict...")
    result_dict = ocr_result.to_dict()
    print("Dict keys: " + str(result_dict.keys() if isinstance(result_dict, dict) else 'not a dict'))
    
    if isinstance(result_dict, dict):
        # Look for text-related keys
        for key in result_dict.keys():
            if 'text' in key.lower() or 'ocr' in key.lower():
                val = result_dict[key]
                if isinstance(val, list):
                    print("\n" + key + " (list with " + str(len(val)) + " items):")
                    for idx, item in enumerate(val[:5]):
                        print("  [" + str(idx) + "] " + str(item)[:100])
                else:
                    print("\n" + key + ": " + str(val)[:100])

# Alternative: Check if there's a method to get text lines
print("\n\nTrying alternative approaches...")

if hasattr(ocr_result, 'pred_results'):
    print("Has pred_results")
    print("pred_results type: " + str(type(ocr_result.pred_results)))

# Try converting to string
print("\nString representation:")
print(str(ocr_result)[:500])
