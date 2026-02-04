#!/usr/bin/env python
import re

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
                       'PERMAI', 'INDAH', 'NEGERI', 'SEMBILAN', 'BINTI', 'BIN', 'PADANG', 'PALOH', 'KUALA', 'BATU', 'PAHAT', 'LOJING']
    
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
                   'ZULKIFLI', 'ZULKEFLI', 'HAMIDEE']
    
    # Use markers to avoid substring conflicts
    marker_counter = 1000
    replacements = {}
    
    print(f"Input text: {text}")
    print(f"Looking for names in text...")
    
    # First pass: replace names with markers
    for name in sorted(malay_names, key=len, reverse=True):
        if name in text:
            print(f"  Found: {name}")
            marker = f"__NAME_{marker_counter}__"
            replacements[marker] = name
            text = text.replace(name, marker)
            marker_counter += 1
    
    print(f"After name replacement: {text}")
    print(f"Replacements: {replacements}")
    
    # Second pass: replace words with markers  
    for word in malay_words_list:
        if word in text:
            marker = f"__WORD_{marker_counter}__"
            replacements[marker] = word
            text = text.replace(word, marker)
            marker_counter += 1
    
    print(f"After word replacement: {text}")
    
    # Third pass: replace markers with spaced versions
    for marker, original in replacements.items():
        text = text.replace(marker, f' {original} ')
    
    for word, placeholder in protected_words:
        text = text.replace(placeholder, word)
    
    result = re.sub(r'\s+', ' ', text).strip()
    print(f"Final result: {result}")
    return result

# Test cases
print("=" * 60)
print("Test 1: NORMUHAMADILYAS")
print("=" * 60)
result1 = split_malay_words("NORMUHAMADILYAS")
print()

print("=" * 60)
print("Test 2: NORMUHAMADILYAS BIN NOR TARMIZE")
print("=" * 60)
result2 = split_malay_words("NORMUHAMADILYAS BIN NOR TARMIZE")
print()

print("=" * 60)
print("Test 3: NOR MUHAMADILYAS BIN NOR TARMIZE")
print("=" * 60)
result3 = split_malay_words("NOR MUHAMADILYAS BIN NOR TARMIZE")
