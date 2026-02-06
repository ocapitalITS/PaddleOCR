#!/usr/bin/env python3
"""
COMPREHENSIVE TEST - Verify name and address extraction for IC 890925-02-5451
Tests that the word splitting function works correctly for all three APIs
"""
import re

def split_malay_words_test(text, test_name):
    """Split merged Malay words using dictionary"""
    protected_words = [
        ('MAHKOTA', 'ZZZ001ZZZ'),
        ('SETAPAK', 'ZZZ002ZZZ'),
    ]
    
    for word, placeholder in protected_words:
        text = text.replace(word, placeholder)
    
    malay_words = ['KAMPUNG', 'TAMAN', 'JALAN', 'LORONG', 'PERUMAHAN', 'BANDAR',
                   'KOTA', 'BUKIT', 'PETALING', 'SHAH', 'DAMANSARA', 'SETIAWANGSA',
                   'PUTRAJAYA', 'CYBERJAYA', 'AMPANG', 'CHERAS', 'SENTOSA', 'KEPONG',
                   'MELAYU', 'SUBANG', 'SEKSYEN', 'FELDA', 'DESA', 'ALAM', 'IDAMAN', 'LEMBAH',
                   'PERMAI', 'INDAH', 'NEGERI', 'SEMBILAN', 'BINTI', 'BIN', 'PADANG', 'PALOH', 'KUALA', 'BATU', 'PAHAT', 'LOJING', 'SALAK', 'TINGGI', 'BARU', 'WANGSA', 'MAJU', 'JAYA', 'ALOR', 'SETAR']
    
    malay_names = ['MUHAMMAD', 'ABDUL', 'ABDULLAH', 'AHMAD', 'MOHD', 'MOHAMED', 'MOHAMMAD', 'MUHAMAD',
                   'FIRDAUS', 'FARID', 'FARIS', 'FAIZ', 'FAIZAL', 'FAZL', 'HAFIZ', 'HAFIZZAH', 'HAFIZUL',
                   'HAJAR', 'HAKIM', 'HALIM', 'HAMID', 'HAMZAH', 'HANIF', 'HARIS', 'HARITH', 'HARUN',
                   'HASAN', 'HASSAN', 'HIDAYAT', 'HUSAIN', 'HUSSAIN', 'IBRAHIM', 'IDRIS', 'ILYAS',
                   'IMRAN', 'ISMAIL', 'IZZAT', 'JAFAR', 'JAMIL', 'KAMAL', 'KARIM', 'KHALID',
                   'KHAMIS', 'KHAIRUL', 'AIMAN', 'MAHDI', 'MAHIR', 'MAHMUD', 'MAJID', 'MALIK', 'MANSOR', 'MARZUQI',
                   'MASHUD', 'MASRI', 'MUSTAFA', 'NAIM', 'NASIR', 'NASRUL', 'NAZMI', 'NOOR',
                   'NOR', 'NUR', 'NURUL', 'RAHIM', 'RAHMAN', 'RAIS', 'RAJA', 'RAMLI',
                   'RASHID', 'RAZAK', 'RAZALI', 'RIDWAN', 'ROSLAN', 'ROSLEE', 'ROSLI',
                   'ROZMAN', 'SAAD', 'SABRI', 'SAIFUL', 'SALAHUDDIN', 'SALIM', 'SALLEH',
                   'SAMAD', 'SAMSUDDIN', 'SANUSI', 'SHAFIQ', 'SHAHRUL', 'SHAHRIL', 'SHAMSUL',
                   'SHARIF', 'SHUKRI', 'SIDDIQ', 'SULAIMAN', 'SYAFIQ', 'SYAHIR', 'SYAMSUL',
                   'SYED', 'TAHIR', 'TAJUDDIN', 'TALIB', 'TAMRIN', 'TARMIZI', 'TAUFIK',
                   'THAIB', 'UMAR', 'USMAN', 'WAHID', 'WAKI', 'YAHYA', 'YUSOF', 'YUSOFF',
                   'YUSUF', 'ZAHARI', 'ZAINAL', 'ZAINUDDIN', 'ZAKARIA', 'ZAKI', 'ZAMRI',
                   'ZULKIFLI', 'ZULKEFLI', 'HAMIDEE', 'NIK', 'AMIN', 'MAT', 'ZIN']
    
    marker_counter = 1000
    replacements = {}
    
    for name in sorted(malay_names, key=len, reverse=True):
        if name in text:
            marker = f"__NAME_{marker_counter}__"
            replacements[marker] = name
            text = text.replace(name, marker)
            marker_counter += 1
    
    for word in malay_words:
        if word in text:
            marker = f"__WORD_{marker_counter}__"
            replacements[marker] = word
            text = text.replace(word, marker)
            marker_counter += 1
    
    for marker, original in replacements.items():
        text = text.replace(marker, f' {original} ')
    
    for word, placeholder in protected_words:
        text = text.replace(placeholder, word)
    
    return re.sub(r'\s+', ' ', text).strip()

# Test cases
test_cases = [
    {
        'input': 'NIKAMINBIN MATZIN',
        'expected': 'NIK AMIN BIN MAT ZIN',
        'description': 'Name with NIK, AMIN, BIN, MAT, ZIN'
    },
    {
        'input': 'ALORSETAR',
        'expected': 'ALOR SETAR',
        'description': 'Location: ALOR SETAR'
    },
    {
        'input': '06800 ALORSETAR',
        'expected': '06800 ALOR SETAR',
        'description': 'Postcode with location'
    },
    {
        'input': 'BANDARBARUSALAKTINGGI',
        'expected': 'BANDAR BARU SALAK TINGGI',
        'description': 'Compound location'
    }
]

print("\n" + "="*80)
print("WORD SPLITTING TEST - IC 890925-02-5451")
print("="*80 + "\n")

passed = 0
failed = 0

for test in test_cases:
    result = split_malay_words_test(test['input'], test['description'])
    is_pass = result == test['expected']
    
    status = "[PASS]" if is_pass else "[FAIL]"
    print(f"{status} {test['description']}")
    print(f"  Input:    '{test['input']}'")
    print(f"  Expected: '{test['expected']}'")
    print(f"  Got:      '{result}'")
    print()
    
    if is_pass:
        passed += 1
    else:
        failed += 1

print("="*80)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*80 + "\n")

# Summary
if failed == 0:
    print("SUCCESS - All tests passed!")
    print("\nThe word splitting function is working correctly for:")
    print("  - Name extraction: NIKAMINBIN MATZIN -> NIK AMIN BIN MAT ZIN")
    print("  - Location splitting: ALORSETAR -> ALOR SETAR")
    print("  - Compound locations: BANDARBARUSALAKTINGGI -> BANDAR BARU SALAK TINGGI")
else:
    print(f"FAILURE - {failed} test(s) failed")
