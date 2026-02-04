#!/usr/bin/env python3
"""Test the name extraction logic for the problematic case"""

# Simulated extracted text from the user's case
extracted_text = [
    "KADPENGENAI",
    "MALAD",
    "MyKad",
    "",
    "IDENN",
    "930118-11-5905",      # IC number - index 5
    "RA",                   # index 6 - should be filtered as noise
    "MUHAMMADHAEIZ",        # index 7 - should become MUHAMMAD HAFIZ
    "AYSIANEASIANNEY",      # index 8 - noise
    "BANDARL",              # index 9 - noise
    "BINHUSAIN",            # index 10 - should be part of name
    "RA",                   # index 11 - noise
    "AKERO",                # index 12 - noise
    "MALAL",                # index 13 - noise
    "NO 1979",              # index 14 - address
    "NMALAYSL",             # index 15 - noise
    "MALA",                 # index 16 - noise
    "KAMPUNG PADANGPALOH",  # index 17 - address
    "WARGANEGARA",          # index 18 - marker
    "20050 KUALATERENGGANU", # index 19 - address
    "TERENGGANUKERAAAN",    # index 20 - address (should become TERENGGANU)
    "ISLAM",                # index 21
    "LELAKI"                # index 22
]

# The IC number is at index 5: "930118-11-5905"
ic_line_idx = 5

# Name extraction looks AFTER ic_line_idx
print("Name extraction (after IC number):")
print(f"IC line index: {ic_line_idx}")
print(f"Looking at lines after index {ic_line_idx}:")
for i in range(ic_line_idx + 1, min(ic_line_idx + 10, len(extracted_text))):
    print(f"  {i}: {extracted_text[i]}")

print("\nExpected name composition:")
print("- Line 7: MUHAMMADHAEIZ -> MUHAMMAD HAFIZ (after correction)")
print("- Line 10: BINHUSAIN -> BIN HUSAIN (after word splitting)")
print("- Result: MUHAMMAD HAFIZ BIN HUSAIN")

print("\nNoise filtering:")
noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip', 'SEFA', 'FAETAY', 'ROTI', 'ACAR', 'RA', 'MALAL', 'BANDAR', 'AKERO']

for i in range(ic_line_idx + 1, min(ic_line_idx + 10, len(extracted_text))):
    line = extracted_text[i]
    line_upper = line.upper()
    is_noise = any(noise in line_upper for noise in noise_words)
    print(f"  {i}: {line:20} -> {'FILTERED (noise)' if is_noise else 'KEPT'}")
