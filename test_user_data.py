#!/usr/bin/env python
"""
Test the extraction with the exact raw OCR text provided by the user
"""
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
    
    # First pass: replace names with markers
    for name in sorted(malay_names, key=len, reverse=True):
        if name in text:
            marker = f"__NAME_{marker_counter}__"
            replacements[marker] = name
            text = text.replace(name, marker)
            marker_counter += 1
    
    # Second pass: replace words with markers  
    for word in malay_words_list:
        if word in text:
            marker = f"__WORD_{marker_counter}__"
            replacements[marker] = word
            text = text.replace(word, marker)
            marker_counter += 1
    
    # Third pass: replace markers with spaced versions
    for marker, original in replacements.items():
        text = text.replace(marker, f' {original} ')
    
    for word, placeholder in protected_words:
        text = text.replace(placeholder, word)
    
    return re.sub(r'\s+', ' ', text).strip()

# Test with the user's reported raw OCR text
raw_ocr_text = [
    "SELANGOR",
    "43900 SEPANG",
    "NO 53 JALAN SEROJA 35",
    "BIN NOR TARMIZE",
    "NORMUHAMADILYAS",
    "890708-08-6143",
    "BANDARBARU SALAK TINGGI",
    "TAMAN SEROJA",
    "",
    "ISLAM",
    "WARGANEGARA",
    "LELAKI",
    "086143"
]

# Simulate what the code does:
# IC line is at index 5: "890708-08-6143"
# Line before IC (index 4): "NORMUHAMADILYAS"
# Line 2 before IC (index 3): "BIN NOR TARMIZE"

ic_line_idx = 5
name_tokens = [raw_ocr_text[4], raw_ocr_text[3]]  # ["NORMUHAMADILYAS", "BIN NOR TARMIZE"]

print(f"name_tokens: {name_tokens}")

raw_name = ' '.join(name_tokens).strip()
print(f"raw_name (joined): '{raw_name}'")

# This is what fastapi_app.py does:
name = split_malay_words(raw_name)
print(f"After split_malay_words: '{name}'")

print("\n" + "="*60)
print("Expected output: 'NOR MUHAMAD ILYAS BIN NOR TARMIZE'")
print(f"Actual output:   '{name}'")
print("Match:", name == "NOR MUHAMAD ILYAS BIN NOR TARMIZE")
