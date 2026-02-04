#!/usr/bin/env python3
"""Test for TAN KIM HAN case - name and address extraction"""

import re

def test_tan_kim_han():
    """Test the TAN KIM HAN case where MELAKA should not be extracted as name"""
    
    # Raw OCR text from the case (in order from API response)
    raw_ocr_text = [
        "970602-04-5335",
        "MELAKA",
        "75050 MELAKA",
        "RUMAH PANGSA AIR LELEH",
        "A22",
        "TAN KIM HAN",
        "WARGANEGARA",
        "LELAKI"
    ]
    
    print("=" * 60)
    print("TEST: TAN KIM HAN - Name Extraction")
    print("=" * 60)
    print(f"\nRaw OCR Lines:")
    for i, line in enumerate(raw_ocr_text):
        print(f"  {i}: {line}")
    
    # Simulate the name extraction logic
    ic_number = "970602-04-5335"
    ic_line_idx = 0  # IC is at index 0
    
    place_name_filters = ['PULAU PINANG', 'SUNGAI DUA', 'GELUGOR', 'SELANGOR', 'JOHOR', 'KEDAH', 
                          'PERAK', 'PAHANG', 'KELANTAN', 'TERENGGANU', 'MELAKA', 'SABAH', 'SARAWAK',
                          'WILAYAH', 'KLANG', 'PUTRAJAYA', 'LABUAN', 'PENANG', 'PINANG', 'PETALING', 'SHAH ALAM', 'IPOH', 'KOTA BHARU']
    
    noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip', 'FAETAY', 'ROTI', 'ACAR', 'RA', 'MALAL', 'BANDAR', 'AKERO']
    
    # Extract name after IC
    name_tokens = []
    name_lines = 0
    
    print(f"\nName Extraction Logic (starting from index {ic_line_idx + 1}):")
    for i in range(ic_line_idx + 1, len(raw_ocr_text)):
        line = raw_ocr_text[i]
        line_upper = line.upper().strip()
        
        print(f"\n  Index {i}: '{line}'")
        
        # Skip empty lines
        if not line_upper:
            print(f"    → Skipped (empty)")
            continue
        
        # Skip single character lines
        if len(line_upper) == 1:
            print(f"    → Skipped (single char)")
            continue
        
        # Stop after 2 name lines
        if name_lines >= 2:
            print(f"    → Stopped (2 name lines reached)")
            break
        
        # Skip header lines
        if any(header in line_upper for header in ['KAD PENGENALAN', 'MYKAD', 'MALAYSIA', 'IDENTITY', 'CARD']):
            print(f"    → Skipped (header)")
            continue
        
        # Stop if line contains numbers
        if re.search(r'\d', line):
            print(f"    → Stopped (contains numbers)")
            break
        
        # Stop if gender/religion/state
        if any(field in line_upper for field in ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'NEGERISEMBILAN', 'SELANGOR', 'JOHOR']):
            print(f"    → Stopped (gender/religion/state keyword)")
            break
        
        # **KEY FIX: Skip place names**
        if any(place in line_upper for place in place_name_filters):
            print(f"    → Skipped (place name: '{line_upper}')")
            continue
        
        # Stop if address keyword
        if any(addr_kw in line_upper for addr_kw in ['LOT', 'JALAN', 'LORONG', 'KAMPUNG', 'PERINGKAT', 'FELDA']):
            print(f"    → Stopped (address keyword)")
            break
        
        # Skip WARGANEGARA
        if 'WARGANEGARA' in line_upper:
            print(f"    → Skipped (WARGANEGARA)")
            break
        
        # Skip noise words
        if any(noise in line_upper for noise in noise_words):
            print(f"    → Skipped (noise word)")
            continue
        
        # Skip lowercase-only lines
        if line.islower():
            print(f"    → Skipped (lowercase only)")
            continue
        
        # This is a name line
        print(f"    → ACCEPTED as name token #{name_lines + 1}")
        name_tokens.append(line)
        name_lines += 1
    
    extracted_name = ' '.join(name_tokens).strip() if name_tokens else None
    
    print(f"\n{'='*60}")
    print(f"RESULT:")
    print(f"  Extracted Name: '{extracted_name}'")
    print(f"  Expected Name:  'TAN KIM HAN'")
    
    if extracted_name == "TAN KIM HAN":
        print(f"  ✓ TEST PASSED")
        return True
    else:
        print(f"  ✗ TEST FAILED")
        return False

if __name__ == '__main__':
    success = test_tan_kim_han()
    exit(0 if success else 1)
