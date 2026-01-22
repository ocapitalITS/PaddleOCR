"""Debug script for testing OCR on ic_front-15.png"""
import sys
import os

# Make sure we use the local paddleocr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paddleocr import PaddleOCR
from PIL import Image
import numpy as np

print("Creating OCR...")
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    enable_mkldnn=False,
    device='cpu',
    ocr_version='PP-OCRv4',
    text_detection_model_name='PP-OCRv4_mobile_det',
    text_recognition_model_name='PP-OCRv4_mobile_rec'
)

print("\nLoading image...")
image = Image.open('IC/ic_front-15.png')
print(f"Image mode: {image.mode}, size: {image.size}")

if image.mode != 'RGB':
    image = image.convert('RGB')
    print(f"Converted to RGB")

image_array = np.array(image)
print(f"Array shape: {image_array.shape}")

print("\nRunning OCR...")
results = ocr.predict(image_array)

print(f"\nResults type: {type(results)}")
print(f"Results length: {len(results) if results else 'None'}")

if results:
    r = results[0]
    print(f"\nFirst result type: {type(r)}")
    print(f"Is dict: {isinstance(r, dict)}")
    print(f"Is list: {isinstance(r, list)}")
    
    # Check various ways to access rec_texts
    print("\n--- Testing access methods ---")
    
    # Method 1: 'rec_texts' in r
    try:
        check = 'rec_texts' in r
        print(f"1. 'rec_texts' in r: {check}")
    except Exception as e:
        print(f"1. 'rec_texts' in r ERROR: {e}")
    
    # Method 2: r['rec_texts']
    try:
        texts = r['rec_texts']
        print(f"2. r['rec_texts']: SUCCESS, {len(texts)} items")
        print(f"   First 3 texts: {texts[:3]}")
    except Exception as e:
        print(f"2. r['rec_texts'] ERROR: {e}")
    
    # Method 3: hasattr
    try:
        has_attr = hasattr(r, 'rec_texts')
        print(f"3. hasattr(r, 'rec_texts'): {has_attr}")
    except Exception as e:
        print(f"3. hasattr(r, 'rec_texts') ERROR: {e}")
    
    # Method 4: r.rec_texts  
    try:
        texts = r.rec_texts
        print(f"4. r.rec_texts: SUCCESS, {len(texts)} items")
    except Exception as e:
        print(f"4. r.rec_texts ERROR: {e}")
    
    # Show keys/attributes
    print("\n--- Object inspection ---")
    if hasattr(r, 'keys'):
        print(f"Keys: {list(r.keys())[:10]}")
    if hasattr(r, '__dict__'):
        print(f"__dict__ keys: {list(r.__dict__.keys())[:10]}")

print("\n--- Done ---")
