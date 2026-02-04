#!/usr/bin/env python3
"""Test the corrections for Muhammad Hafiz Bin Husain case"""
import re

print("=" * 60)
print("Testing OCR corrections and name processing")
print("=" * 60)

# OCR corrections
ocr_corrections = [
    (r'HAEIZ', 'HAFIZ'),
    (r'MUHAMMADHAFIZ', 'MUHAMMAD HAFIZ'),
    (r'PADANGPALOH', 'PADANG PALOH'),
    (r'KUALATERENGGANU', 'KUALA TERENGGANU'),
    (r'TERENGGANUKERAA+N', 'TERENGGANU'),
]

# Test 1: Name correction
print("\n--- Test 1: Name OCR Correction ---")
raw_text = "MUHAMMADHAEIZ"
print(f"Original: {raw_text}")

for pattern, replacement in ocr_corrections:
    raw_text = re.sub(pattern, replacement, raw_text)

print(f"After OCR corrections: {raw_text}")

# Test 2: Noise word filtering
print("\n--- Test 2: Noise Word Filtering ---")
noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip', 'SEFA', 'FAETAY', 'ROTI', 'ACAR', 'RA', 'MALAL', 'BANDAR', 'AKERO']

test_names = ['RA', 'MUHAMMADHAEIZ', 'AKERO', 'MALAL', 'BANDAR L']

for name in test_names:
    is_noise = any(noise in name.upper() for noise in noise_words)
    print(f"{name:20} -> {'FILTERED' if is_noise else 'KEPT'}")

# Test 3: Address splitting
print("\n--- Test 3: Address Word Splitting ---")
malay_words = ['KAMPUNG', 'TAMAN', 'JALAN', 'LORONG', 'PERUMAHAN', 'BANDAR',
               'KOTA', 'BUKIT', 'PETALING', 'SHAH', 'DAMANSARA', 'SETIAWANGSA',
               'PUTRAJAYA', 'CYBERJAYA', 'AMPANG', 'CHERAS', 'SENTOSA', 'KEPONG',
               'MELAYU', 'SUBANG', 'SEKSYEN', 'FELDA', 'DESA', 'ALAM', 'IDAMAN', 'LEMBAH',
               'PERMAI', 'INDAH', 'NEGERI', 'SEMBILAN', 'BINTI', 'BIN', 'PADANG', 'PALOH', 'KUALA']

addresses = [
    ('PADANGPALOH', 'PADANG PALOH'),
    ('KUALATERENGGANU', 'KUALA TERENGGANU'),
    ('TERENGGANUKERAAAN', 'TERENGGANU'),
    ('KAMPUNGPADANGPALOH', 'KAMPUNG PADANG PALOH'),
]

for addr, expected in addresses:
    corrected = addr
    for pattern, replacement in ocr_corrections:
        corrected = re.sub(pattern, replacement, corrected)
    print(f"{addr:25} -> {corrected:30} (expected: {expected})")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
