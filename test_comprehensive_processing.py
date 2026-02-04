#!/usr/bin/env python3
"""Comprehensive test of the OCR processing for Muhammad Hafiz case"""
import re

print("=" * 70)
print("COMPREHENSIVE TEST: Muhammad Hafiz Bin Husain Case")
print("=" * 70)

# Step 1: Simulated extracted text
extracted_text = [
    "KADPENGENAI",
    "MALAD",
    "MyKad",
    "",
    "IDENN",
    "930118-11-5905",      # IC number - index 5
    "RA",                   # Should be filtered as noise
    "MUHAMMADHAEIZ",        # Name part 1
    "AYSIANEASIANNEY",      # Noise
    "BANDARL",              # Noise
    "BINHUSAIN",            # Name part 2
    "RA",                   # Noise (filtered before name_lines >= 2)
    "AKERO",                # Noise
    "MALAL",                # Noise
    "NO 1979",              # Address
    "NMALAYSL",             # Noise
    "MALA",                 # Noise
    "KAMPUNG PADANGPALOH",  # Address
    "WARGANEGARA",          # Marker
    "20050 KUALATERENGGANU", # Address
    "TERENGGANUKERAAAN",    # Address/State
    "ISLAM",
    "LELAKI"
]

noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip', 'SEFA', 'FAETAY', 'ROTI', 'ACAR', 'RA', 'MALAL', 'BANDAR', 'AKERO']

malay_names = ['MUHAMMAD', 'ABDUL', 'ABDULLAH', 'AHMAD', 'MOHD', 'MOHAMED', 'MOHAMMAD',
               'FIRDAUS', 'FARID', 'FARIS', 'FAIZ', 'FAIZAL', 'FAZL', 'HAFIZ', 'HAFIZZAH', 'HAFIZUL',
               'HAJAR', 'HAKIM', 'HALIM', 'HAMID', 'HAMZAH', 'HANIF', 'HARIS', 'HARITH', 'HARUN',
               'HASAN', 'HASSAN', 'HIDAYAT', 'HUSAIN', 'HUSSAIN', 'IBRAHIM', 'IDRIS',
               'IMRAN', 'ISMAIL', 'IZZAT']

malay_words = ['KAMPUNG', 'TAMAN', 'JALAN', 'LORONG', 'PERUMAHAN', 'BANDAR',
               'KOTA', 'BUKIT', 'PETALING', 'SHAH', 'DAMANSARA', 'SETIAWANGSA',
               'PUTRAJAYA', 'CYBERJAYA', 'AMPANG', 'CHERAS', 'SENTOSA', 'KEPONG',
               'MELAYU', 'SUBANG', 'SEKSYEN', 'FELDA', 'DESA', 'ALAM', 'IDAMAN', 'LEMBAH',
               'PERMAI', 'INDAH', 'NEGERI', 'SEMBILAN', 'BINTI', 'BIN', 'PADANG', 'PALOH', 'KUALA']

ocr_corrections = [
    (r'HAEIZ', 'HAFIZ'),
    (r'MUHAMMADHAFIZ', 'MUHAMMAD HAFIZ'),
    (r'PADANGPALOH', 'PADANG PALOH'),
    (r'KUALATERENGGANU', 'KUALA TERENGGANU'),
    (r'TERENGGANUKERAA+N', 'TERENGGANU'),
]

# Step 2: Simulate name extraction
print("\nSTEP 1: Name Extraction")
print("-" * 70)
ic_line_idx = 5
name_tokens = []
name_lines = 0

for i in range(ic_line_idx + 1, len(extracted_text)):
    line = extracted_text[i]
    line_upper = line.upper().strip()
    
    if not line_upper or len(line_upper) == 1:
        continue
    
    if name_lines >= 2:
        print(f"  [Line {i}] STOP: Already collected 2 name lines")
        break
    
    # Check if noise
    if any(noise in line_upper for noise in noise_words):
        print(f"  [Line {i}] SKIP (noise): {line}")
        continue
    
    # Check if address keyword
    if re.search(r'\d', line):
        print(f"  [Line {i}] STOP (contains digit): {line}")
        break
    
    print(f"  [Line {i}] ADD: {line}")
    name_tokens.append(line)
    name_lines += 1

print(f"\nCollected name tokens: {name_tokens}")

# Step 3: Process name tokens
print("\nSTEP 2: Name Processing")
print("-" * 70)

raw_name = ' '.join(name_tokens).strip()
print(f"1. Raw name (joined): {raw_name}")

# Apply OCR corrections
for pattern, replacement in ocr_corrections:
    raw_name = re.sub(pattern, replacement, raw_name)
print(f"2. After OCR corrections: {raw_name}")

# Apply word splitting (simplified)
def split_malay_words_simple(text, malay_names, malay_words):
    """Simplified version of split_malay_words"""
    protected_words = [
        ('MAHKOTA', 'ZZZ001ZZZ'),
        ('SETAPAK', 'ZZZ002ZZZ'),
    ]
    
    for word, placeholder in protected_words:
        text = text.replace(word, placeholder)
    
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

processed_name = split_malay_words_simple(raw_name, malay_names, malay_words)
print(f"3. After word splitting: {processed_name}")

# Step 4: Address extraction
print("\nSTEP 3: Address Extraction")
print("-" * 70)

address_lines = []
address_keywords = ['LOT', 'JALAN', 'KAMPUNG', 'KG', 'JLN', 'NO', 'BATU', 'LEBUH', 'LORONG', 'JAMBATAN', 'PPR', 'BLOK', 'UNIT', 'TINGKAT', 'TAMAN', 'BANDAR', 'PERINGKAT', 'FELDA', 'DESA', 'PERMAI']

for i in range(ic_line_idx + 1, len(extracted_text)):
    line = extracted_text[i]
    line_upper = line.upper().strip()
    
    # Skip lines that are part of extracted name
    if line in name_tokens:
        continue
    
    # Skip noise words
    if any(noise in line_upper for noise in noise_words):
        continue
    
    # Check if it's an address line
    if any(addr_kw in line_upper for addr_kw in address_keywords):
        print(f"  [Line {i}] ADDRESS: {line}")
        address_lines.append(line)

address = ' '.join(address_lines).strip() if address_lines else None
print(f"\nExtracted address: {address}")

# Apply address corrections
if address:
    for pattern, replacement in ocr_corrections:
        address = re.sub(pattern, replacement, address)
    print(f"After corrections: {address}")
    
    # Apply word splitting
    address = split_malay_words_simple(address, malay_names, malay_words)
    print(f"After word splitting: {address}")

print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print(f"Name:    {processed_name}")
print(f"Address: {address}")
print(f"\nExpected Name:    Muhammad Hafiz Bin Husain")
print(f"Expected Address: No 1979, Kampung Padang Paloh, 20050 Kuala Terengganu, Terengganu")
print("=" * 70)
