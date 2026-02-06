"""
Test Name and Address Extractor with Real Problem Cases
"""

from name_address_extractor import NameAddressExtractor


def test_muhammad_afiq_hamzi_case():
    """Test the MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN case"""
    
    print("=" * 70)
    print("TEST: MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN")
    print("=" * 70)
    
    # Raw OCR data from the user's report
    raw_ocr_text = [
        "SELANGOR",
        "M1-G-1 SERI BINTANG APT",
        "BIN ABD RAHMAN",
        "960325-10-5977",
        "YENU6",                    # Should be MUHAMMAD
        "NG BESTARI",               # Should be AFIQ HAMZI (misread)
        "AHALAM",                   # Should be SHAH ALAM
        "0",
        "J",
        "MyKad",
        "ISLAM",
        "WARGANEGARA",
        "LELAKI"
    ]
    
    extractor = NameAddressExtractor()
    
    print("\nRaw OCR Output:")
    for i, line in enumerate(raw_ocr_text):
        print(f"  [{i}]: {line}")
    
    # Extract data
    result = extractor.extract_ic_data(raw_ocr_text)
    
    print("\n" + "=" * 70)
    print("EXTRACTED DATA:")
    print("=" * 70)
    print(f"IC Number: {result['ic_number']}")
    print(f"Name:      {result['name']}")
    print(f"Address:   {result['address']}")
    
    print("\n" + "=" * 70)
    print("EXPECTED DATA:")
    print("=" * 70)
    expected_name = "MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN"
    expected_address = "M1-G-1 SERI BINTANG APT, SUBANG BESTARI, SEKSYEN U5, 40150 SHAH ALAM, SELANGOR"
    expected_ic = "960325-10-5977"
    
    print(f"IC Number: {expected_ic}")
    print(f"Name:      {expected_name}")
    print(f"Address:   {expected_address}")
    
    print("\n" + "=" * 70)
    print("VALIDATION:")
    print("=" * 70)
    
    # Check IC number
    ic_match = result['ic_number'] == expected_ic
    print(f"IC Number Match:   {ic_match} {'✅' if ic_match else '❌'}")
    
    # Check name (partial match - at least contains key parts)
    name_parts = ['MUHAMMAD', 'AFIQ', 'HAMZI', 'ABD RAHMAN']
    name_matched = all(part in result['name'].upper() for part in name_parts if result['name'])
    print(f"Name Contains Key Parts: {name_matched} {'✅' if name_matched else '❌'}")
    print(f"  - MUHAMMAD: {'✅' if 'MUHAMMAD' in result['name'].upper() else '❌'}")
    print(f"  - AFIQ: {'✅' if 'AFIQ' in result['name'].upper() else '❌'}")
    print(f"  - HAMZI: {'✅' if 'HAMZI' in result['name'].upper() else '❌'}")
    print(f"  - ABD RAHMAN: {'✅' if 'ABD RAHMAN' in result['name'].upper() else '❌'}")
    
    # Check address (partial match)
    address_parts = ['SERI BINTANG', 'SUBANG BESTARI', 'SHAH ALAM', '40150', 'SELANGOR']
    address_matched_count = sum(1 for part in address_parts if result['address'] and part.upper() in result['address'].upper())
    print(f"\nAddress Contains Key Parts ({address_matched_count}/{len(address_parts)}): {address_matched_count > 3} {'✅' if address_matched_count > 3 else '⚠️'}")
    for part in address_parts:
        found = result['address'] and part.upper() in result['address'].upper()
        print(f"  - {part}: {'✅' if found else '❌'}")
    
    print("\n" + "=" * 70)


def test_ocr_text_correction():
    """Test OCR text correction function"""
    
    print("\n" + "=" * 70)
    print("TEST: OCR Text Correction")
    print("=" * 70)
    
    extractor = NameAddressExtractor()
    
    test_cases = [
        ("YENU6", "MUHAMMAD"),
        ("MUHAMMAH", "MUHAMMAD"),
        ("AHALAM", "SHAH ALAM"),
        ("SERIBINTANG", "SERI BINTANG"),
        ("SUBANGBESTARI", "SUBANG BESTARI"),
    ]
    
    print("\nTesting OCR corrections:")
    for incorrect, expected_correct in test_cases:
        corrected = extractor.correct_ocr_text(incorrect)
        match = corrected == expected_correct
        print(f"  {incorrect:20} → {corrected:20} (Expected: {expected_correct:20}) {'✅' if match else '❌'}")


def test_name_extraction_patterns():
    """Test name extraction with different patterns"""
    
    print("\n" + "=" * 70)
    print("TEST: Name Extraction Patterns")
    print("=" * 70)
    
    extractor = NameAddressExtractor()
    
    # Pattern 1: Normal order
    text_lines_1 = [
        "960325-10-5977",
        "YENU6",
        "NG BESTARI",
        "BIN ABD RAHMAN",
        "40150 SHAH ALAM"
    ]
    
    print("\nPattern 1 - Normal Order:")
    result_1 = extractor.extract_name(text_lines_1, "960325-10-5977")
    print(f"  Input lines: {text_lines_1[1:4]}")
    print(f"  Extracted: {result_1}")
    
    # Pattern 2: BIN/BINTI appears early
    text_lines_2 = [
        "BIN ABD RAHMAN",
        "YENU6 NG BESTARI",
        "960325-10-5977",
    ]
    
    print("\nPattern 2 - BIN/BINTI Early:")
    result_2 = extractor.extract_name(text_lines_2, "960325-10-5977")
    print(f"  Input lines: {text_lines_2}")
    print(f"  Extracted: {result_2}")


if __name__ == "__main__":
    test_ocr_text_correction()
    test_name_extraction_patterns()
    test_muhammad_afiq_hamzi_case()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 70 + "\n")
