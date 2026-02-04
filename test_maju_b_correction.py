#!/usr/bin/env python3
"""Test the MAJU B -> MAJU 6 correction"""
import re

test_cases = [
    "JALAN MAJU B",
    "JJALAN MAJU B",
    "JALAN MAJU B, TAMAN JEMENTAH",
]

corrections = [
    (r'JJALAN', 'JALAN'),
    (r'MAJU B(?!\s*[A-Z])', 'MAJU 6'),
]

print("Testing MAJU B -> MAJU 6 correction")
print("=" * 60)

for text in test_cases:
    print(f"\nOriginal: {text}")
    corrected = text
    for pattern, replacement in corrections:
        corrected = re.sub(pattern, replacement, corrected)
    print(f"Corrected: {corrected}")

print("\n" + "=" * 60)
