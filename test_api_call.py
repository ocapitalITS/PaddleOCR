#!/usr/bin/env python
import requests
import json
from pathlib import Path

# Path to test image
image_path = Path('IC/ic_front_20260129230128930.jpg')

if not image_path.exists():
    print(f"Image not found at {image_path}")
    exit(1)

# Call the API
url = 'http://localhost:8000/api/ocr'
with open(image_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

if response.status_code == 200:
    result = response.json()
    print("API Response:")
    print(json.dumps(result, indent=2))
else:
    print(f"API Error: {response.status_code}")
    print(response.text)
