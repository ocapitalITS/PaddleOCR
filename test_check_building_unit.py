import os
import sys
sys.path.insert(0, '/usr/local/lib/python3.10/site-packages')

# Test image path
test_image_path = r'c:\laragon\www\PaddleOCR\IC\test_image.jpg'

if not os.path.exists(test_image_path):
    print(f"Image not found: {test_image_path}")
    sys.exit(1)

# Initialize OCR
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, model_storage_directory=r'c:\laragon\www\PaddleOCR\models')

# Run OCR
result = ocr.ocr(test_image_path, cls=True)

# Extract all text lines
print("All OCR lines (raw):")
print("=" * 80)
for line_idx, line in enumerate(result[0]):
    text = line[1][0]
    print(f"[{line_idx}] '{text}'")

# Find the line with ?
print("\nLooking for placeholder lines:")
print("=" * 80)
for line_idx, line in enumerate(result[0]):
    text = line[1][0]
    if '?' in text or text.strip() == '?':
        print(f"[{line_idx}] Found placeholder: '{text}'")
        # Check raw character codes
        print(f"  Raw bytes: {[ord(c) for c in text]}")
        print(f"  Character analysis:")
        for c in text:
            print(f"    '{c}' (ord={ord(c)})")
