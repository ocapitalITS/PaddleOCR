"""
Test script to debug OCR issue
"""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import cv2

# Initialize PaddleOCR with same parameters as Streamlit
print("Initializing PaddleOCR...")
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
print("PaddleOCR initialized successfully!")

# Load test image
image_path = r'IC\ic_front-3.jpg'
print(f"\nLoading image: {image_path}")

# Load with PIL (like Flask does)
pil_image = Image.open(image_path)
print(f"PIL image mode: {pil_image.mode}, size: {pil_image.size}")

# Convert to numpy array
image_array = np.array(pil_image)
print(f"Numpy array shape: {image_array.shape}, dtype: {image_array.dtype}")

# Test OCR
print("\nRunning OCR...")
results = ocr.predict(image_array)

if results and len(results) > 0:
    ocr_result = results[0]
    print(f"\nOCR Result type: {type(ocr_result)}")
    
    if hasattr(ocr_result, 'rec_texts'):
        text_list = list(ocr_result.rec_texts)
        print(f"Text extracted via rec_texts: {len(text_list)} items")
        for i, text in enumerate(text_list[:10]):
            print(f"  {i+1}. {text}")
    elif isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
        text_list = list(ocr_result['rec_texts'])
        print(f"Text extracted via dict: {len(text_list)} items")
        for i, text in enumerate(text_list[:10]):
            print(f"  {i+1}. {text}")
    else:
        print(f"Unknown result format. Keys/attrs: {dir(ocr_result) if hasattr(ocr_result, '__dict__') else ocr_result}")
else:
    print("No results returned from OCR!")
    print(f"Results: {results}")
