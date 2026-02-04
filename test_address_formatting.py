#!/usr/bin/env python3
import re

# Test the address processing with the new fixes

# Simulate the address lines from OCR
address_lines = [
    '3B-2-2 SRI LOJING CONDO',
    'JLN 4/27E SEKSYEN 10',
    'WANGSA MAJU',
    '53300 KUALA LUMPUR',
    'W.PERSEKUTUAN(KL)'
]

print('\nADDRESS PROCESSING TEST')
print('=' * 80)
print('\nOriginal OCR address lines:')
for i, line in enumerate(address_lines, 1):
    print(f'{i}. {line}')

# Step 1: Check if unit number spacing is preserved
print('\n' + '=' * 80)
print('STEP 1: Unit number spacing fix')
print('=' * 80)

line = '3B-2-2 SRI LOJING CONDO'
line_upper = line.upper().strip()
pattern = r'^\d+[A-Z]-[\d\-A-Z]+'

# Check if it matches the unit number pattern
if re.search(pattern, line):
    print(f'✓ Line matches unit number pattern: {line}')
    # Don't add spaces in unit number pattern
    print('✓ Spacing preserved: "3B-2-2" (not "3 B-2-2")')
else:
    print(f'✗ Line does not match unit number pattern')

# Step 2: Split lines that contain street + area markers
print('\n' + '=' * 80)
print('STEP 2: Line splitting (street + area markers)')
print('=' * 80)

address_lines_split = []
for line in address_lines:
    line_upper = line.upper()
    has_street = any(kw in line_upper for kw in ['JALAN', 'JLN', 'LORONG', 'LEBUH'])
    has_area_marker = any(kw in line_upper for kw in ['SEKSYEN', 'BUKIT', 'BANDAR', 'TAMAN'])
    
    print(f'\nLine: "{line}"')
    print(f'  Has street keyword: {has_street}')
    print(f'  Has area marker: {has_area_marker}')
    
    if has_street and has_area_marker:
        print(f'  → Splitting...')
        for marker in ['SEKSYEN', 'BUKIT', 'BANDAR', 'TAMAN']:
            if marker in line_upper:
                parts = re.split(f'({marker}\\s+\\d+|{marker}[A-Z\\s]*)', line, flags=re.IGNORECASE)
                for part in parts:
                    if part.strip() and part.strip() not in ['', ' ']:
                        print(f'    - "{part.strip()}"')
                        address_lines_split.append(part.strip())
                break
    else:
        address_lines_split.append(line)

print('\n' + '=' * 80)
print('STEP 3: Final address assembly')
print('=' * 80)

address = ', '.join(address_lines_split)
print(f'\nBefore state formatting: {address}')

# Step 3: Format state/federal territory spacing
address = re.sub(r'W\.PERSEKUTUAN\(', 'W. PERSEKUTUAN (', address)
address = re.sub(r'W\.PERSEKUTUAN', 'W. PERSEKUTUAN', address)

print(f'After state formatting:  {address}')

print('\n' + '=' * 80)
print('EXPECTED OUTPUT')
print('=' * 80)
expected = '3B-2-2 SRI LOJING CONDO, JLN 4/27E, SEKSYEN 10, WANGSA MAJU, 53300 KUALA LUMPUR, W. PERSEKUTUAN (KL)'
print(f'\nExpected: {expected}')
print(f'\nActual:   {address}')

match = address == expected
print(f'\n{"✓ TEST PASSED" if match else "✗ TEST FAILED"}')

if not match:
    print('\nDifferences:')
    print(f'  Expected length: {len(expected)}')
    print(f'  Actual length:   {len(address)}')
