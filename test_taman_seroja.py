#!/usr/bin/env python3
"""
Test for TAMAN SEROJA case - upside-down card name extraction
The IC is rotated (180°), and the actual name is "NOR MUHAMADILYAS"
but "TAMAN SEROJA" (an area name) is being extracted instead.
"""

import re

def test_taman_seroja():
    """Test extraction of upside-down IC where name comes before IC"""
    
    # Raw OCR text from the rotated/upside-down IC
    extracted_text = [
        "SELANGOR",                      # [0] Place name
        "43900 SEPANG",                  # [1] Postcode + place name
        "NO 53 JALAN SEROJA35",          # [2] Address
        "BIN NOR TARMIZE",               # [3] Father's name
        "NORMUHAMADILYAS",               # [4] ACTUAL NAME (single word, before IC)
        "890708-08-6143",                # [5] IC number
        "BANDARBARU SALAK TINGGI",       # [6] Area name
        "TAMAN SEROJA",                  # [7] Area name (wrongly extracted as name)
        "",                              # [8]
        "ISLAM",                         # [9]
        "WARGANEGARA",                   # [10]
        "LELAKI",                        # [11]
        "086143"                         # [12]
    ]
    
    ic_number = "890708-08-6143"
    ic_line_idx = 5  # IC is at index 5
    
    place_name_filters = [
        'PULAU PINANG', 'SUNGAI DUA', 'GELUGOR', 'SELANGOR', 'JOHOR', 'KEDAH',
        'PERAK', 'PAHANG', 'KELANTAN', 'TERENGGANU', 'MELAKA', 'SABAH', 'SARAWAK',
        'KUALA LUMPUR', 'PUTRAJAYA', 'LABUAN', 'PERLIS', 'NEGERI SEMBILAN',
        'PENANG', 'PINANG', 'PETALING', 'SHAH ALAM', 'IPOH', 'KOTA BHARU', 'SEPANG'
    ]
    
    area_keywords = ['TAMAN', 'DESA', 'PERMAI', 'SEKSYEN', 'BANDAR', 'WANGSA', 'JAYA', 'INDAH', 'MAJU', 'SALAK', 'TINGGI']
    
    building_keywords = ['RUMAH', 'APARTMENT', 'CONDO', 'FLAT', 'BLOK', 'BLOCK', 'BANGLOW', 'BANGUNAN', 'WISMA', 'PLAZA', 'KOMPLEKS', 'PERUMAHAN', 'PANGSA']
    
    print("=" * 80)
    print("TEST: TAMAN SEROJA - Upside-Down IC Name Extraction")
    print("=" * 80)
    
    print(f"\nRaw OCR Text (Upside-Down Card):")
    for i, line in enumerate(extracted_text):
        marker = " <-- IC" if i == ic_line_idx else ""
        print(f"  [{i}] {line}{marker}")
    
    print(f"\n{'─' * 80}")
    print("BEFORE IC EXTRACTION (indices {ic_line_idx-2} to {ic_line_idx-1}):")
    print(f"{'─' * 80}")
    
    # Check BEFORE IC
    name_tokens = []
    
    # Try to get name from BEFORE IC number first (some cards have name before IC)
    if ic_line_idx > 0:
        prev_line = extracted_text[ic_line_idx - 1].upper().strip()
        is_place_name = any(place in prev_line for place in place_name_filters)
        is_area_name = any(area in prev_line for area in area_keywords)
        is_building = any(bkw in prev_line for bkw in building_keywords)
        
        print(f"\n  Line {ic_line_idx - 1}: '{extracted_text[ic_line_idx - 1]}'")
        print(f"    - Length: {len(prev_line)} chars")
        print(f"    - Is place name: {is_place_name}")
        print(f"    - Is area name: {is_area_name}")
        print(f"    - Is building: {is_building}")
        print(f"    - Has BIN/BINTI: {any(word in prev_line for word in ['BIN', 'BINTI'])}")
        print(f"    - Word count: {len(prev_line.split())}")
        
        # Accept if: has BIN/BINTI, OR is multi-word, OR is single word (name pattern)
        has_name_indicator = any(word in prev_line for word in ['BIN', 'BINTI'])
        is_multi_word = len(prev_line.split()) > 2
        is_single_word_name = len(prev_line.split()) == 1 and len(prev_line) > 3 and prev_line.isalpha()
        
        if prev_line and len(prev_line) > 3 and not is_place_name and not is_area_name and not is_building:
            if has_name_indicator or is_multi_word or is_single_word_name:
                name_tokens = [extracted_text[ic_line_idx - 1]]
                print(f"    ✓ ACCEPTED: Name token")
            else:
                print(f"    ✗ Not a name pattern")
        else:
            print(f"    ✗ Filtered out (place/area/building or too short)")
        
        # Also check line before that if it's part of the name
        if ic_line_idx > 1:
            prev_prev_line = extracted_text[ic_line_idx - 2].upper().strip()
            print(f"\n  Line {ic_line_idx - 2}: '{extracted_text[ic_line_idx - 2]}'")
            is_prev_prev_place = any(place in prev_prev_line for place in place_name_filters)
            is_prev_prev_area = any(area in prev_prev_line for area in area_keywords)
            
            if prev_prev_line and len(prev_prev_line) > 2 and not is_prev_prev_place and not is_prev_prev_area and not any(keyword in prev_prev_line for keyword in ['KAD', 'MALAYSIA', 'IDENTITY', 'MYKAD']):
                if 'BIN' in prev_prev_line or 'BINTI' in prev_prev_line:
                    name_tokens.insert(0, extracted_text[ic_line_idx - 2])
                    print(f"    ✓ ACCEPTED: Father's name (has BIN/BINTI)")
                else:
                    print(f"    ✗ Not a name pattern")
            else:
                print(f"    ✗ Filtered out")
    
    # Check AFTER IC
    print(f"\n{'─' * 80}")
    print("AFTER IC EXTRACTION (starting from index {ic_line_idx + 1}):")
    print(f"{'─' * 80}")
    
    if not name_tokens:
        name_lines = 0
        for i in range(ic_line_idx + 1, len(extracted_text)):
            line = extracted_text[i]
            line_upper = line.upper().strip()
            
            if not line_upper or len(line_upper) == 1:
                continue
            
            if name_lines >= 2:
                break
            
            print(f"\n  Line {i}: '{line}'")
            
            # Check filters
            if any(header in line_upper for header in ['KAD PENGENALAN', 'MYKAD', 'MALAYSIA', 'IDENTITY', 'CARD']):
                print(f"    ✗ Header line")
                continue
            
            if any(field in line_upper for field in ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH']):
                print(f"    ✗ Gender/religion")
                break
            
            if any(place in line_upper for place in place_name_filters):
                print(f"    ✗ Place name")
                continue
            
            if any(area in line_upper for area in area_keywords):
                print(f"    ✗ Area name (TAMAN, DESA, SEKSYEN, etc.)")
                continue
            
            if any(addr_kw in line_upper for addr_kw in ['LOT', 'JALAN', 'LORONG', 'KAMPUNG', 'PERINGKAT', 'FELDA']):
                print(f"    ✗ Address keyword")
                break
            
            if any(bkw in line_upper for bkw in building_keywords):
                print(f"    ✗ Building keyword")
                continue
            
            if 'WARGANEGARA' in line_upper:
                print(f"    ✗ WARGANEGARA")
                break
            
            letter_count = sum(1 for c in line if c.isalpha() or c.isspace() or c in "-'@")
            letter_ratio = letter_count / len(line) if line else 0
            if letter_ratio < 0.7:
                print(f"    ✗ Only {letter_ratio*100:.1f}% letters")
                continue
            
            print(f"    ✓ ACCEPTED as name")
            name_tokens.append(line)
            name_lines += 1
    
    extracted_name = ' '.join(name_tokens).strip() if name_tokens else None
    
    print(f"\n{'═' * 80}")
    print("RESULT:")
    print(f"{'═' * 80}")
    print(f"\nExtracted Name: '{extracted_name}'")
    print(f"Expected Name:  'NORMUHAMADILYAS' or 'NOR MUHAMADILYAS'")
    
    if extracted_name and ('NORMUHAMADILYAS' in extracted_name.replace(' ', '') or 'NOR MUHAMADILYAS' in extracted_name):
        print(f"\n✓ TEST PASSED: Correct name extracted, area names filtered!")
        return True
    else:
        print(f"\n✗ TEST FAILED: Expected name with NORMUHAMADILYAS")
        return False

if __name__ == '__main__':
    success = test_taman_seroja()
    print(f"\n{'═' * 80}\n")
    exit(0 if success else 1)
