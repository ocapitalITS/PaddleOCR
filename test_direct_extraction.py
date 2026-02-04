#!/usr/bin/env python
import sys
import cv2
from pathlib import Path
import json

# Import the extraction function
from fastapi_app import extract_fields, process_image_ocr

# Test with the image
image_path = Path('IC/ic_front_20260129230128930.jpg')

if image_path.exists():
    print(f"Testing with image: {image_path}")
    image = cv2.imread(str(image_path))
    
    if image is not None:
        results, best_angle = process_image_ocr(image)
        result = extract_fields(results, best_angle)
        
        print("\n=== Extraction Result ===")
        print(json.dumps(result, indent=2))
    else:
        print(f"Failed to load image at {image_path}")
else:
    print(f"Image not found at {image_path}")
