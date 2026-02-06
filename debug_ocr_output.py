"""
Debug tool to extract and display raw OCR output from Malaysia IC images
Run this to understand what text is being detected before extraction logic processes it
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR imported successfully")
except ImportError as e:
    print(f"❌ Failed to import PaddleOCR: {e}")
    sys.exit(1)

def debug_ocr_output(image_path):
    """
    Debug OCR output for a given image
    Shows raw text extracted line by line
    """
    
    print("=" * 80)
    print(f"DEBUG OCR OUTPUT FOR: {image_path}")
    print("=" * 80)
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return
    
    # Load image
    print(f"\n1. Loading image from: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image")
        return
    
    height, width = image.shape[:2]
    print(f"   Image dimensions: {width}x{height}")
    
    # Initialize OCR
    print(f"\n2. Initializing PaddleOCR...")
    ocr = PaddleOCR(use_angle_cls=True, use_gpu=False, lang='en')
    
    # Run OCR
    print(f"\n3. Running OCR...")
    results = ocr.ocr(image_path, cls=True)
    
    if not results or not results[0]:
        print("❌ No OCR results found")
        return
    
    print(f"   ✅ OCR completed")
    
    # Extract and display text
    print(f"\n4. RAW OCR OUTPUT (Line by line):")
    print("-" * 80)
    
    extracted_lines = []
    for idx, (bbox, (text, conf)) in enumerate(results[0]):
        extracted_lines.append(text)
        print(f"   [{idx:2d}] (conf: {conf:.2%}) {text}")
    
    print("-" * 80)
    
    # Join and display
    print(f"\n5. FULL TEXT (joined):")
    print("-" * 80)
    full_text = " ".join(extracted_lines)
    print(full_text)
    print("-" * 80)
    
    # Extract IC number
    import re
    ic_match = re.search(r'\d{6}-\d{2}-\d{4}', full_text)
    if ic_match:
        ic_number = ic_match.group()
        ic_idx = extracted_lines.index(ic_match.group()) if ic_match.group() in extracted_lines else None
        print(f"\n6. IC NUMBER FOUND:")
        print(f"   IC: {ic_number}")
        if ic_idx is not None:
            print(f"   Position: Line {ic_idx}")
            print(f"   Before IC: {[extracted_lines[i] for i in range(max(0, ic_idx-3), ic_idx)]}")
            print(f"   After IC: {[extracted_lines[i] for i in range(ic_idx+1, min(len(extracted_lines), ic_idx+4))]}")
    else:
        print(f"\n6. IC NUMBER: NOT FOUND")
    
    # Look for name patterns
    print(f"\n7. NAME PATTERNS:")
    bin_binti_found = False
    for idx, line in enumerate(extracted_lines):
        if 'BIN' in line.upper() or 'BINTI' in line.upper():
            print(f"   Found BIN/BINTI at line {idx}: {line}")
            if idx > 0:
                print(f"      Before: {extracted_lines[idx-1]}")
            if idx < len(extracted_lines) - 1:
                print(f"      After:  {extracted_lines[idx+1]}")
            bin_binti_found = True
    
    if not bin_binti_found:
        print(f"   ❌ BIN/BINTI not found in OCR output")
    
    # Show line count
    print(f"\n8. SUMMARY:")
    print(f"   Total lines extracted: {len(extracted_lines)}")
    print(f"   Lines with numbers: {sum(1 for line in extracted_lines if any(c.isdigit() for c in line))}")
    print(f"   Lines with letters: {sum(1 for line in extracted_lines if any(c.isalpha() for c in line))}")
    
    return extracted_lines


if __name__ == "__main__":
    # Test with IC images in the IC folder
    ic_folder = "IC"
    
    if not os.path.exists(ic_folder):
        print(f"❌ Folder '{ic_folder}' not found")
        sys.exit(1)
    
    # Find and process IC images
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        image_files.extend(Path(ic_folder).glob(f'*{ext}'))
    
    # Sort by modification time (most recent first)
    image_files = sorted(image_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not image_files:
        print(f"❌ No image files found in {ic_folder}")
        sys.exit(1)
    
    # Process first 3 recent images
    for image_path in image_files[:3]:
        debug_ocr_output(str(image_path))
        print("\n" + "="*80 + "\n")
