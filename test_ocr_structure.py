"""
Quick test - just print the OCR results structure
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi_app import ocr

image_path = r"IC\ic_front_20260204164113379.jpg"

print("Running OCR...")
results = ocr.predict(image_path)

print("\nResults type: " + str(type(results)))
print("Results keys: " + str(results.keys() if isinstance(results, dict) else 'not a dict'))

if isinstance(results, list):
    print("Results length: " + str(len(results)))
    if len(results) > 0:
        print("First element type: " + str(type(results[0])))
        print("First element: " + str(results[0])[:200])
