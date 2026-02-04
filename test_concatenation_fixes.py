#!/usr/bin/env python3
import re

# Test the BINTI/TAMAN concatenation fixes

patterns = [
    (r'BINTIHAMIDEE', 'BINTI HAMIDEE'),
    (r'TAMANALOR', 'TAMAN ALOR'),
]

test_cases = [
    ('SITI NUR AISYAH BINTIHAMIDEE', 'SITI NUR AISYAH BINTI HAMIDEE'),
    ('TAMANALOR', 'TAMAN ALOR'),
    ('78000 ALOR GAJAH', '78000 ALOR GAJAH'),  # Should not be affected
]

print('\nCONCATENATION FIXES TEST')
print('=' * 80)

for original, expected in test_cases:
    corrected = original
    for pattern, replacement in patterns:
        corrected = re.sub(pattern, replacement, corrected)
    
    status = '✓ PASS' if corrected == expected else '✗ FAIL'
    print(f'{status:8} | Original: {original:35} | Result: {corrected}')
    if corrected != expected:
        print(f'         | Expected: {expected}')

print('\n' + '=' * 80)
print('Test 1: Name with BINTI concatenation')
corrected = 'SITI NUR AISYAH BINTIHAMIDEE'
for pattern, replacement in patterns:
    corrected = re.sub(pattern, replacement, corrected)
print(f'Result:   {corrected}')
print(f'Expected: SITI NUR AISYAH BINTI HAMIDEE')
print(f'Status:   {"✓ PASS" if corrected == "SITI NUR AISYAH BINTI HAMIDEE" else "✗ FAIL"}')

print('\nTest 2: Address with TAMAN concatenation')
corrected = 'TAMANALOR'
for pattern, replacement in patterns:
    corrected = re.sub(pattern, replacement, corrected)
print(f'Result:   {corrected}')
print(f'Expected: TAMAN ALOR')
print(f'Status:   {"✓ PASS" if corrected == "TAMAN ALOR" else "✗ FAIL"}')

print('\n' + '=' * 80)
print('Combined test:')
raw_name = 'SITI NUR AISYAH BINTIHAMIDEE'
raw_address = 'TAMANALOR'
for pattern, replacement in patterns:
    raw_name = re.sub(pattern, replacement, raw_name)
    raw_address = re.sub(pattern, replacement, raw_address)
print(f'Name:    {raw_name} (expected: SITI NUR AISYAH BINTI HAMIDEE)')
print(f'Address: {raw_address} (expected: TAMAN ALOR)')
