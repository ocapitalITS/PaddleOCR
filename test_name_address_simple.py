#!/usr/bin/env python3
"""Direct test of name and address splitting logic"""
import re

def split_malay_words(text):
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
    
    # First pass: replace names with markers (sort by length to match longest first)
    for name in sorted(malay_names, key=len, reverse=True):
        if name in text:
            marker = f"__NAME_{marker_counter}__"
            replacements[marker] = name
            text = text.replace(name, marker)
            marker_counter += 1
    
    # Second pass: replace words with markers  
    for word in malay_words:
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

# Test with the actual data
print("="*70)
print("TESTING NAME EXTRACTION AND SPLITTING")
print("="*70)

raw_name = "NIKAMINBIN MATZIN"
print(f"\nRaw OCR name: {raw_name}")

# Apply BIN/BINTI spacing like fastapi_app does
name = raw_name
name = re.sub(r'BINTI([A-Z])', r'BINTI \1', name, flags=re.IGNORECASE)
if 'BIN' in name and 'BINTI' not in name:
    name = re.sub(r'BIN([A-Z])', r'BIN \1', name, flags=re.IGNORECASE)
name = re.sub(r'([A-Z]+)(BINTI)\s', r'\1 \2 ', name, flags=re.IGNORECASE)
name = re.sub(r'([A-Z]+)(BIN)\s', r'\1 \2 ', name, flags=re.IGNORECASE)

print(f"After BIN/BINTI spacing: {name}")

# Apply split_malay_words
name = split_malay_words(name)
print(f"After split_malay_words: {name}")

name = re.sub(r'\s+', ' ', name).strip()
print(f"Final cleaned name: {name}")

# Verify
expected = "NIK AMIN BIN MAT ZIN"
if name == expected:
    print(f"\n[PASS] Name correctly extracted: {name}")
else:
    print(f"\n[FAIL] Expected '{expected}' but got '{name}'")

print("\n" + "="*70)
print("TESTING ADDRESS EXTRACTION AND SPLITTING")
print("="*70)

# Test address components
address_lines = [
    "NO 25",
    "KAMPUNG ALOR TERJUN",
    "KOTA SARANG SEMUT",
    "06800 ALORSETAR",
    "KEDAH"
]

print(f"\nRaw OCR address lines:")
for line in address_lines:
    print(f"  - {line}")

# Process each line like fastapi_app does
processed_lines = []
for line in address_lines:
    if line.upper() in ['WARGANEGARA', 'KEDAH', 'ISLAM', 'LELAKI']:
        continue
    
    corrected_line = split_malay_words(line)
    corrected_line = re.sub(r'\s+', ' ', corrected_line).strip()
    
    if corrected_line and corrected_line not in processed_lines:
        processed_lines.append(corrected_line)
        print(f"  Processed: {line} -> {corrected_line}")

address = ', '.join(processed_lines)
print(f"\nFinal address: {address}")

# Verify
if "ALOR SETAR" in address:
    print(f"[PASS] Address correctly split ALORSETAR to ALOR SETAR")
else:
    print(f"[FAIL] Address does not contain split 'ALOR SETAR'")
