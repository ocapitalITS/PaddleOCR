#!/usr/bin/env python3
"""Debug the split_malay_words function"""
import sys
sys.path.insert(0, 'c:\\laragon\\www\\PaddleOCR')

# Test the split_malay_words function
def split_malay_words(text):
    """Split merged Malay words using dictionary with marker approach"""
    protected_words = [
        ('MAHKOTA', 'ZZZ001ZZZ'),
        ('SETAPAK', 'ZZZ002ZZZ'),
    ]
    
    for word, placeholder in protected_words:
        text = text.replace(word, placeholder)
    
    malay_words_list = ['KAMPUNG', 'TAMAN', 'JALAN', 'LORONG', 'PERUMAHAN', 'BANDAR',
                       'KOTA', 'BUKIT', 'PETALING', 'SHAH', 'DAMANSARA', 'SETIAWANGSA',
                       'PUTRAJAYA', 'CYBERJAYA', 'AMPANG', 'CHERAS', 'SENTOSA', 'KEPONG',
                       'MELAYU', 'SUBANG', 'SEKSYEN', 'FELDA', 'DESA', 'ALAM', 'IDAMAN', 'LEMBAH',
                       'PERMAI', 'INDAH', 'NEGERI', 'SEMBILAN', 'BINTI', 'BIN', 'PADANG', 'PALOH', 'KUALA', 'BATU', 'PAHAT', 'LOJING', 'SALAK', 'TINGGI', 'BARU', 'WANGSA', 'MAJU', 'JAYA', 'ALOR', 'SETAR']
    
    # Common Malay names that often get merged in OCR
    malay_names = ['MUHAMMAD', 'MUHAMAD', 'ABDUL', 'ABDULLAH', 'AHMAD', 'MOHD', 'MOHAMED', 'MOHAMMAD',
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
    
    print(f"Input: '{text}'")
    print(f"Checking for name components in text:")
    for name in sorted(malay_names, key=len, reverse=True):
        if name in text:
            print(f"  ✓ Found '{name}' in '{text}'")
    
    print(f"Checking for location words in text:")
    for word in malay_words_list:
        if word in text:
            print(f"  ✓ Found '{word}' in '{text}'")
    
    # Use markers to avoid substring conflicts
    import re
    marker_counter = 1000
    replacements = {}
    
    # First pass: replace names with markers (sort by length to match longest first)
    for name in sorted(malay_names, key=len, reverse=True):
        if name in text:
            marker = f"__NAME_{marker_counter}__"
            replacements[marker] = name
            text = text.replace(name, marker)
            marker_counter += 1
    
    print(f"\nAfter name replacement: '{text}'")
    print(f"Replacements so far: {replacements}")
    
    # Second pass: replace words with markers  
    for word in malay_words_list:
        if word in text:
            marker = f"__WORD_{marker_counter}__"
            replacements[marker] = word
            text = text.replace(word, marker)
            marker_counter += 1
    
    print(f"After word replacement: '{text}'")
    print(f"All replacements: {replacements}")
    
    # Third pass: replace markers with spaced versions
    for marker, original in replacements.items():
        text = text.replace(marker, f' {original} ')
    
    print(f"After adding spaces: '{text}'")
    
    for word, placeholder in protected_words:
        text = text.replace(placeholder, word)
    
    result = re.sub(r'\s+', ' ', text).strip()
    print(f"Final result: '{result}'")
    return result

# Test cases
test_cases = [
    "NIKAMINBIN MATZIN",
    "NIKAMIN",
    "ALORSETAR",
    "06800 ALORSETAR",
]

for test in test_cases:
    print("\n" + "="*60)
    result = split_malay_words(test)
    print(f"\nRESULT: '{test}' → '{result}'")
    print("="*60)
