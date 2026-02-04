#!/usr/bin/env python3
import re

# Test the unit number pattern
unit_number_pattern = r'^\d+[A-Z]*-[\d\-A-Z]+'

test_cases = [
    ('3B-2-2 SRI LOJING CONDO', True),
    ('3-B-2-2 SRI LOJING', True),
    ('5A-2-3 JALAN TAMAN', True),
    ('LOT 123-A', False),  # This starts with "LOT", not a digit
    ('NO 45', False),  # This is "NO", not matching our pattern
    ('A-01-25', False),  # This starts with letter, not digit
    ('DG-12', False),  # This starts with letter
]

print('\nUNIT NUMBER PATTERN TEST')
print('=' * 70)
print(f'Pattern: {unit_number_pattern}\n')

for text, expected_match in test_cases:
    line_upper = text.upper().strip()
    matches = bool(re.match(unit_number_pattern, line_upper))
    status = '✓ PASS' if matches == expected_match else '✗ FAIL'
    print(f'{status:8} | {text:35} | Match: {matches} (Expected: {expected_match})')

print('\n' + '=' * 70)

# Test the full address extraction scenario
print('\nADDRESS EXTRACTION SCENARIO')
print('=' * 70)

address_lines = [
    '3B-2-2 SRI LOJING CONDO',
    'JLN 4/27E SEKSYEN 10',
    'WANGSA MAJU',
    '53300 KUALA LUMPUR',
    'W.PERSEKUTUAN(KL)'
]

print('\nExtracted address lines:')
for i, line in enumerate(address_lines):
    print(f'{i+1}. {line}')

address = ', '.join(address_lines)
print(f'\nFinal address: {address}')

print('\n' + '=' * 70)
print('✓ All tests completed!')
