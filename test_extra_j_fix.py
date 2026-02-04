#!/usr/bin/env python3
import re

# Test the extra J's corrections for "NO 15JJJALAN 13"

patterns = [
    (r'(\d+)J+JALAN', r'\1 JALAN'),  # Fix extra J's
    (r'\bJ\s+JALAN', 'JALAN'),  # Remove duplicate J
]

test_cases = [
    ('NO 15JJJALAN 13', 'NO 15 JALAN 13'),
    ('NO 5JJALAN 7', 'NO 5 JALAN 7'),
    ('NO 15 J JALAN 13', 'NO 15 JALAN 13'),  # After first pattern, might have J JALAN
    ('NO 15JJJALAN', 'NO 15 JALAN'),
]

print('\nEXTRA J\'S CORRECTION TEST')
print('=' * 80)

for original, expected in test_cases:
    corrected = original
    for pattern, replacement in patterns:
        corrected = re.sub(pattern, replacement, corrected)
    
    status = '✓ PASS' if corrected == expected else '✗ FAIL'
    print(f'{status:8} | Original: {original:25} | Result: {corrected}')
    if corrected != expected:
        print(f'         | Expected: {expected}')

print('\n' + '=' * 80)
print('Key test: NO 15JJJALAN 13')
corrected = 'NO 15JJJALAN 13'
for pattern, replacement in patterns:
    corrected = re.sub(pattern, replacement, corrected)
print(f'Result:   {corrected}')
print(f'Expected: NO 15 JALAN 13')
print(f'\n{"✓ TEST PASSED" if corrected == "NO 15 JALAN 13" else "✗ TEST FAILED"}')

