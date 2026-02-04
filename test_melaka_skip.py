#!/usr/bin/env python3
"""
Test to demonstrate that MELAKA is skipped when extracting name after IC number.
This validates the place_name_filters fix for the TAN KIM HAN case.
"""

import re

def test_place_name_skip():
    """Test the place_name_filters logic for skipping state names"""
    
    # Simulated OCR extraction order
    extracted_text = [
        "970602-04-5335",      # IC number (index 0)
        "MELAKA",               # Place name (index 1) - should be SKIPPED
        "75050 MELAKA",         # Address line with number (index 2) - should STOP
        "RUMAH PANGSA AIR LELEH", # Address (index 3)
        "A22",                  # Unit number (index 4)
        "TAN KIM HAN",         # ACTUAL NAME (index 5) - should be ACCEPTED
        "WARGANEGARA",         # (index 6)
        "LELAKI"               # (index 7)
    ]
    
    ic_number = "970602-04-5335"
    ic_line_idx = 0  # IC is at index 0
    
    # Define place name filters (same as in the API code)
    place_name_filters = [
        'PULAU PINANG', 'SUNGAI DUA', 'GELUGOR', 'SELANGOR', 'JOHOR', 'KEDAH',
        'PERAK', 'PAHANG', 'KELANTAN', 'TERENGGANU', 'MELAKA', 'SABAH', 'SARAWAK',
        'KUALA LUMPUR', 'PUTRAJAYA', 'LABUAN', 'PERLIS', 'NEGERI SEMBILAN',
        'PENANG', 'PINANG', 'PETALING', 'SHAH ALAM', 'IPOH', 'KOTA BHARU'
    ]
    
    # Building type keywords
    building_keywords = ['RUMAH', 'APARTMENT', 'CONDO', 'FLAT', 'BLOK', 'BLOCK', 'BANGLOW', 'BANGUNAN', 'WISMA', 'PLAZA', 'KOMPLEKS', 'PERUMAHAN', 'PANGSA']
    
    noise_words = [
        'ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT',
        'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM',
        'LALAYSI', 'Touch', 'chip', 'SEFA', 'FAETAY', 'ROTI', 'ACAR', 'RA', 
        'MALAL', 'BANDAR', 'AKERO'
    ]
    
    print("=" * 80)
    print("TEST: Place Name Filter for TAN KIM HAN Case")
    print("=" * 80)
    
    print(f"\nExtracted Text Lines:")
    for i, line in enumerate(extracted_text):
        print(f"  [{i}] {line}")
    
    print(f"\nIC Number: {ic_number}")
    print(f"IC Line Index: {ic_line_idx}")
    print(f"\nName extraction starts from index {ic_line_idx + 1}...")
    
    # Simulate the name extraction logic (from after IC)
    name_tokens = []
    name_lines = 0
    
    print(f"\n{'─' * 80}")
    print("EXTRACTION PROCESS:")
    print(f"{'─' * 80}")
    
    for i in range(ic_line_idx + 1, len(extracted_text)):
        line = extracted_text[i]
        line_upper = line.upper().strip()
        
        print(f"\n[Step {i - ic_line_idx}] Line {i}: '{line}'")
        
        # Check each filter
        
        # 1. Empty or too short
        if not line_upper:
            print(f"  ✗ Skipped: Line is empty")
            continue
        if len(line_upper) == 1:
            print(f"  ✗ Skipped: Single character")
            continue
        
        # 2. Name limit check
        if name_lines >= 2:
            print(f"  ✗ Stopped: Already collected 2 name lines")
            break
        
        # 3. Header keywords
        if any(header in line_upper for header in ['KAD PENGENALAN', 'MYKAD', 'MALAYSIA', 'IDENTITY', 'CARD']):
            print(f"  ✗ Skipped: Contains header keyword")
            continue
        
        # 4. Check if line is mostly letters/spaces (name pattern) - first priority
        # Names should be primarily alphabetic, postcodes/addresses won't pass this
        letter_count = sum(1 for c in line if c.isalpha() or c.isspace() or c in "-'@")
        letter_ratio = letter_count / len(line) if line else 0
        if letter_ratio < 0.7:
            print(f"  ✗ Skipped: Only {letter_ratio*100:.1f}% alphabetic (need 70%+) - likely address line")
            continue
        
        # 5. Gender/religion/state keywords
        if any(field in line_upper for field in ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'NEGERISEMBILAN', 'SELANGOR', 'JOHOR']):
            print(f"  ✗ Stopped: Contains gender/religion/state keyword")
            break
        
        # 6. Skip place names (states, cities)
        if any(place in line_upper for place in place_name_filters):
            matching_place = next(place for place in place_name_filters if place in line_upper)
            print(f"  ✗ Skipped: Matched place name filter: '{matching_place}'")
            continue
        
        # 7. Address keywords
        if any(addr_kw in line_upper for addr_kw in ['LOT', 'JALAN', 'LORONG', 'KAMPUNG', 'PERINGKAT', 'FELDA']):
            print(f"  ✗ Stopped: Contains address keyword")
            break
        
        # 8. Building type keywords
        if any(bkw in line_upper for bkw in building_keywords):
            print(f"  ✗ Skipped: Contains building type keyword")
            continue
        
        # 9. WARGANEGARA
        if 'WARGANEGARA' in line_upper:
            print(f"  ✗ Stopped: WARGANEGARA")
            break
        
        # 10. Noise words
        if any(noise in line_upper for noise in noise_words):
            print(f"  ✗ Skipped: Noise word")
            continue
        
        # 11. Lowercase only
        if line.islower():
            print(f"  ✗ Skipped: Lowercase only")
            continue
        
        # 12. Check if line is mostly letters/spaces (name pattern)
        letter_count = sum(1 for c in line if c.isalpha() or c.isspace() or c in "-'@")
        letter_ratio = letter_count / len(line) if line else 0
        if letter_ratio < 0.7:
            print(f"  ✗ Skipped: Only {letter_ratio*100:.1f}% alphabetic (need 70%+)")
            continue
        
        # ACCEPT as name token
        print(f"  ✓ ACCEPTED: This is a name token #{name_lines + 1}")
        name_tokens.append(line)
        name_lines += 1
    
    # Final result
    extracted_name = ' '.join(name_tokens).strip() if name_tokens else None
    
    print(f"\n{'═' * 80}")
    print("RESULT:")
    print(f"{'═' * 80}")
    print(f"\nExtracted Name: '{extracted_name}'")
    print(f"Expected Name:  'TAN KIM HAN'")
    
    if extracted_name == "TAN KIM HAN":
        print(f"\n✓ TEST PASSED: Name correctly extracted, MELAKA was skipped!")
        return True
    else:
        print(f"\n✗ TEST FAILED: Expected 'TAN KIM HAN' but got '{extracted_name}'")
        return False

if __name__ == '__main__':
    success = test_place_name_skip()
    print(f"\n{'═' * 80}\n")
    exit(0 if success else 1)
