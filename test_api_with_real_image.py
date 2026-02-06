"""
Test the FastAPI endpoint with the real image
"""

import requests
import json

image_path = r"IC\ic_front_20260204164113379.jpg"

# Read image file
with open(image_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/ocr',
        files=files
    )

result = response.json()

print("API RESPONSE")
print("=" * 80)
print(json.dumps(result, indent=2, ensure_ascii=False))
print("=" * 80)

# Check expected values
expected = {
    "ic_number": "960325-10-5977",
    "name": "MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN",
}

print("\nVALIDATION:")
if result['ic_number'] == expected['ic_number']:
    print("✅ IC Number CORRECT")
else:
    print(f"❌ IC Number WRONG: got '{result['ic_number']}', expected '{expected['ic_number']}'")

if result['name'] == expected['name']:
    print("✅ Name CORRECT")
else:
    print(f"❌ Name WRONG: got '{result['name']}', expected '{expected['name']}'")

if 'SHAH ALAM' in result['address']:
    print("✅ Address contains SHAH ALAM")
else:
    print(f"❌ Address missing SHAH ALAM: {result['address']}")
