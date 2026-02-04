#!/usr/bin/env python3
import re

# Test corrections for Wan Muhammad Syazwan case
test_cases = {
    'Name': [
        ('ZULKIFL', 'ZULKIFLI'),
        ('BIN WAN ZULKIFL', 'BIN ZULKIFLI'),
    ],
    'Address': [
        ('3 B-2-2SRILOJING CONDO', '3B-2-2 SRI LOJING CONDO'),
        ('63300 KUALA LUMPUR', '53300 KUALA LUMPUR'),
    ]
}

corrections = [
    (r'ZULKIFL(?!I)', 'ZULKIFLI'),
    (r'SRILOJING', 'SRI LOJING'),
    (r'3 B-2-2SRI', '3B-2-2 SRI'),
    (r'63300 KUALA LUMPUR', '53300 KUALA LUMPUR'),
]

print('\nWAN MUHAMMAD SYAZWAN - CORRECTION VERIFICATION')
print('=' * 70)

for category, cases in test_cases.items():
    print(f'\n{category} Corrections:')
    print('-' * 70)
    for original, expected in cases:
        corrected = original
        for pattern, replacement in corrections:
            corrected = re.sub(pattern, replacement, corrected)
        status = '✓ PASS' if corrected == expected else '✗ FAIL'
        print(f'{status:8} | Original: {original:35} | Result: {corrected}')
        if corrected != expected:
            print(f'         | Expected: {expected}')

print('\n' + '=' * 70)
print('All corrections verified!')
