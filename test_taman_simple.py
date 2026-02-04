#!/usr/bin/env python3
"""Test for TAMAN SEROJA case - upside-down IC name extraction"""

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
    
    place_name_filters = ['SELANGOR', 'JOHOR', 'MELAKA', 'SEPANG', 'PENANG', 'KUALA LUMPUR']
    area_keywords = ['TAMAN', 'DESA', 'PERMAI', 'SEKSYEN', 'BANDAR', 'WANGSA', 'JAYA']
    building_keywords = ['RUMAH', 'APARTMENT', 'CONDO', 'FLAT', 'BLOK']
    
    print("=" * 70)
    print("TEST: TAMAN SEROJA - Upside-Down IC Name Extraction")
    print("=" * 70)
    
    print("\nRaw OCR Text (Upside-Down Card):")
    for i, line in enumerate(extracted_text):
        marker = " <-- IC" if i == ic_line_idx else ""
        print(f"  [{i}] {line}{marker}")
    
    # Check BEFORE IC
    name_tokens = []
    print("\nBEFORE IC EXTRACTION:")
    
    if ic_line_idx > 0:
        prev_line = extracted_text[ic_line_idx - 1].upper().strip()
        is_place = any(p in prev_line for p in place_name_filters)
        is_area = any(a in prev_line for a in area_keywords)
        is_bldg = any(b in prev_line for b in building_keywords)
        
        print(f"  Line {ic_line_idx - 1}: '{extracted_text[ic_line_idx - 1]}'")
        print(f"    - Place: {is_place}, Area: {is_area}, Building: {is_bldg}")
        print(f"    - Has BIN: {any(w in prev_line for w in ['BIN', 'BINTI'])}")
        print(f"    - Word count: {len(prev_line.split())}")
        
        has_bin = any(w in prev_line for w in ['BIN', 'BINTI'])
        is_multi = len(prev_line.split()) > 2
        is_single_name = len(prev_line.split()) == 1 and len(prev_line) > 3 and prev_line.isalpha()
        
        if prev_line and len(prev_line) > 3 and not is_place and not is_area and not is_bldg:
            if has_bin or is_multi or is_single_name:
                name_tokens = [extracted_text[ic_line_idx - 1]]
                print(f"    -> ACCEPTED (has_bin={has_bin}, is_multi={is_multi}, is_single_name={is_single_name})")
            else:
                print(f"    -> REJECTED (no name pattern)")
        else:
            print(f"    -> REJECTED (filtered/too short)")
        
        # Check line before that
        if ic_line_idx > 1:
            prev2 = extracted_text[ic_line_idx - 2].upper().strip()
            is_prev2_place = any(p in prev2 for p in place_name_filters)
            
            print(f"\n  Line {ic_line_idx - 2}: '{extracted_text[ic_line_idx - 2]}'")
            if prev2 and len(prev2) > 2 and not is_prev2_place and 'BIN' in prev2:
                name_tokens.insert(0, extracted_text[ic_line_idx - 2])
                print(f"    -> ACCEPTED (has BIN)")
            else:
                print(f"    -> REJECTED")
    
    # Check AFTER IC if needed
    if not name_tokens:
        print("\nAFTER IC EXTRACTION:")
        name_lines = 0
        for i in range(ic_line_idx + 1, len(extracted_text)):
            line = extracted_text[i]
            line_upper = line.upper().strip()
            
            if not line_upper or len(line_upper) == 1 or name_lines >= 2:
                continue
            
            print(f"  Line {i}: '{line}'")
            
            if any(h in line_upper for h in ['KAD', 'MYKAD']):
                print(f"    -> REJECTED (header)")
                continue
            
            if any(f in line_upper for f in ['LELAKI', 'PEREMPUAN', 'ISLAM']):
                print(f"    -> REJECTED (gender/religion)")
                break
            
            if any(p in line_upper for p in place_name_filters):
                print(f"    -> REJECTED (place name)")
                continue
            
            if any(a in line_upper for a in area_keywords):
                print(f"    -> REJECTED (area name)")
                continue
            
            if any(b in line_upper for b in building_keywords):
                print(f"    -> REJECTED (building)")
                continue
            
            print(f"    -> ACCEPTED")
            name_tokens.append(line)
            name_lines += 1
    
    extracted_name = ' '.join(name_tokens).strip() if name_tokens else None
    
    print("\n" + "=" * 70)
    print(f"Extracted: {extracted_name}")
    print(f"Expected:  NORMUHAMADILYAS or with father's name included")
    
    if extracted_name and 'NORMUHAMADILYAS' in extracted_name.replace(' ', ''):
        print("PASS - Area names filtered, actual name extracted")
        return True
    else:
        print("FAIL - Wrong name extracted")
        return False

if __name__ == '__main__':
    test_taman_seroja()
