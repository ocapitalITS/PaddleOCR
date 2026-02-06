"""
Quick OCR Test for specific image
Shows exactly what PaddleOCR detects
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from paddleocr import PaddleOCR

# Initialize OCR
print("Initializing PaddleOCR...")
ocr = PaddleOCR(use_angle_cls=True, use_gpu=False, lang='en')

# Test image path
image_path = r"IC\ic_front_20260204164113379.jpg"

print(f"Testing image: {image_path}")
print()

# Run OCR
print("Running OCR...")
results = ocr.ocr(image_path, cls=True)

if not results or not results[0]:
    print("ERROR: No OCR results")
    sys.exit(1)

# Display results
print("="*80)
print("RAW OCR OUTPUT (Line by line)")
print("="*80)

extracted_lines = []
for idx, (bbox, (text, conf)) in enumerate(results[0]):
    extracted_lines.append(text)
    print(f"[{idx:2d}] (conf: {conf:6.1%}) {text}")

print("="*80)
print("ANALYSIS")
print("="*80)

# Join text
full_text = " ".join(extracted_lines)
print(f"\nTotal lines: {len(extracted_lines)}")
print(f"\nFull text:")
print(full_text)

# Search for key patterns
print("\n" + "="*80)
print("KEY COMPONENTS FOUND")
print("="*80)

import re

# IC number
ic_match = re.search(r'\d{6}-\d{2}-\d{4}', full_text)
if ic_match:
    ic = ic_match.group()
    ic_idx = extracted_lines.index(ic) if ic in extracted_lines else -1
    print(f"\n✅ IC Number: {ic}")
    if ic_idx >= 0:
        print(f"   Position: Line {ic_idx}")
        print(f"   Lines before IC: {extracted_lines[max(0, ic_idx-3):ic_idx]}")
        print(f"   Lines after IC: {extracted_lines[ic_idx+1:min(len(extracted_lines), ic_idx+5)]}")
else:
    print(f"\n❌ IC Number: NOT FOUND")

# BIN/BINTI
bin_found = False
for idx, line in enumerate(extracted_lines):
    if 'BIN' in line.upper() or 'BINTI' in line.upper():
        print(f"\n✅ BIN/BINTI: Found at line {idx}")
        print(f"   Text: '{line}'")
        if idx > 0:
            print(f"   Before: '{extracted_lines[idx-1]}'")
        if idx < len(extracted_lines) - 1:
            print(f"   After: '{extracted_lines[idx+1]}'")
        bin_found = True
        break

if not bin_found:
    print(f"\n❌ BIN/BINTI: NOT FOUND")

# Address keywords
print(f"\n📍 Address Components:")
addr_keywords = ['LOT', 'JALAN', 'JLN', 'APARTMENT', 'APT', 'BLOK', 'TAMAN', 'DESA', 'SEKSYEN']
found_addr = False
for idx, line in enumerate(extracted_lines):
    if any(kw in line.upper() for kw in addr_keywords):
        print(f"   Line {idx}: {line}")
        found_addr = True

if not found_addr:
    print(f"   ❌ No address keywords found")

# State names
states = ['JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK', 'SELANGOR', 'TERENGGANU']
print(f"\n📍 States:")
found_state = False
for idx, line in enumerate(extracted_lines):
    if any(state in line.upper() for state in states):
        print(f"   Line {idx}: {line}")
        found_state = True

if not found_state:
    print(f"   ❌ No state found")

# Postcode
print(f"\n💾 Postcode:")
postcode_found = False
for idx, line in enumerate(extracted_lines):
    if re.match(r'^\d{5}', line):
        print(f"   Line {idx}: {line}")
        postcode_found = True

if not postcode_found:
    print(f"   ❌ No postcode found")

print("\n" + "="*80)
