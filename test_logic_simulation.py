#!/usr/bin/env python
"""
Comprehensive test based on user's reported OCR output.
Tests name extraction and address extraction logic.
"""

# User's reported raw OCR output
raw_ocr_text = [
    "SELANGOR",              # 0
    "43900 SEPANG",          # 1  
    "NO 53 JALAN SEROJA 35", # 2
    "BIN NOR TARMIZE",       # 3
    "NORMUHAMADILYAS",       # 4
    "890708-08-6143",        # 5 (IC line)
    "BANDARBARU SALAK TINGGI", # 6
    "TAMAN SEROJA",          # 7
    "",                      # 8
    "ISLAM",                 # 9
    "WARGANEGARA",           # 10
    "LELAKI",                # 11
    "086143"                 # 12
]

print("="*70)
print("TEST 1: Name Extraction Logic")
print("="*70)

# Simulate the before-IC name extraction from fastapi_app.py
ic_line_idx = 5  # "890708-08-6143"
name_tokens = []

prev_line = raw_ocr_text[ic_line_idx - 1].upper().strip()  # "NORMUHAMADILYAS"
prev_prev_line = raw_ocr_text[ic_line_idx - 2].upper().strip()  # "BIN NOR TARMIZE"

print(f"IC line index: {ic_line_idx}")
print(f"Line at ic_line_idx - 1 ({ic_line_idx-1}): '{prev_line}'")
print(f"Line at ic_line_idx - 2 ({ic_line_idx-2}): '{prev_prev_line}'")

# Check if it's a single-word name (NORMUHAMADILYAS)
is_single_word_name = len(prev_line.split()) == 1 and len(prev_line) > 3 and prev_line.isalpha()
print(f"\nis_single_word_name: {is_single_word_name}")

if is_single_word_name:
    print("Path: Single-word name detected")
    name_tokens = [raw_ocr_text[ic_line_idx - 1]]  # ["NORMUHAMADILYAS"]
    print(f"Initial name_tokens: {name_tokens}")
    
    # Check for father's name before it
    if "BIN" in prev_prev_line:
        print(f"Found BIN in line before: '{prev_prev_line}'")
        name_tokens.append(raw_ocr_text[ic_line_idx - 2])
        print(f"After appending father's name: {name_tokens}")

print(f"\nFinal name_tokens: {name_tokens}")
raw_name = ' '.join(name_tokens).strip()
print(f"Joined raw_name: '{raw_name}'")

print("\n" + "="*70)
print("TEST 2: Address Extraction Logic")
print("="*70)

# Simulate address extraction
location_keywords_in_line = ['BANDAR', 'TAMAN', 'DESA', 'SEKSYEN', 'SALAK', 'TINGGI', 
                              'WANGSA', 'JAYA', 'INDAH', 'MAJU', 'SUBANG', 'PERMAI']

address_lines = []
collecting_address = False

for i in range(len(raw_ocr_text)):
    line = raw_ocr_text[i]
    line_upper = line.upper().strip()
    
    if not line_upper or i == 5:  # Skip empty lines and IC line
        continue
    
    # Check for location keywords
    location_count = sum(1 for kw in location_keywords_in_line if kw in line_upper)
    
    print(f"\nLine {i}: '{line}'")
    print(f"  Location keywords found: {location_count}")
    
    if location_count >= 2:
        print(f"  -> Compound location detected! Start collecting address")
        collecting_address = True
    
    if collecting_address:
        # Only skip pure area keyword lines (single word)
        is_area_only = any(area in line_upper for area in ['BANDAR', 'TAMAN', 'DESA', 'SEKSYEN', 'SALAK', 'TINGGI']) and len(line_upper.split()) == 1
        
        if is_area_only:
            print(f"  -> Skip: Area keyword only")
        else:
            print(f"  -> Adding to address")
            address_lines.append(line)
        
        if line_upper == 'WARGANEGARA':
            print(f"  -> WARGANEGARA found, stop collecting address")
            collecting_address = False

print(f"\nCollected address lines: {address_lines}")
address = ', '.join(address_lines)
print(f"Final address: '{address}'")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Name (raw): '{raw_name}'")
print(f"Name (expected after split): 'NOR MUHAMAD ILYAS BIN NOR TARMIZE'")
print(f"\nAddress lines collected: {address_lines}")
print(f"Address (expected): 'NO 53 JALAN SEROJA 35, TAMAN SEROJA, BANDARBARU SALAK TINGGI, 43900 SEPANG, SELANGOR'")
