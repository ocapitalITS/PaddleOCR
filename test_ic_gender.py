#!/usr/bin/env python3

# Test gender determination from IC number last digit

test_cases = [
    # (IC number, expected gender)
    ('950316-01-6965', 'Male'),    # Last digit 5 (odd) = Male ✓
    ('991227-04-5466', 'Female'),  # Last digit 6 (even) = Female ✓
    ('890402-03-5415', 'Male'),    # Last digit 5 (odd) = Male ✓
    ('123456-78-9001', 'Male'),    # Last digit 1 (odd) = Male
    ('123456-78-9002', 'Female'),  # Last digit 2 (even) = Female
    ('111111-11-1111', 'Male'),    # Last digit 1 (odd) = Male
    ('222222-22-2222', 'Female'),  # Last digit 2 (even) = Female
]

print('\nIC NUMBER GENDER EXTRACTION TEST')
print('=' * 80)
print('Rule: Odd last digit = Male, Even last digit = Female\n')

all_pass = True
for ic_number, expected_gender in test_cases:
    try:
        last_digit = int(ic_number[-1])
        gender = 'Male' if last_digit % 2 == 1 else 'Female'
        status = '✓ PASS' if gender == expected_gender else '✗ FAIL'
        
        print(f'{status:8} | IC: {ic_number:16} | Last digit: {last_digit} ({["Even", "Odd"][last_digit % 2]}) | Gender: {gender}')
        
        if gender != expected_gender:
            print(f'         | Expected: {expected_gender}')
            all_pass = False
    except (ValueError, IndexError) as e:
        print(f'✗ ERROR | IC: {ic_number:16} | {str(e)}')
        all_pass = False

print('\n' + '=' * 80)
if all_pass:
    print('✓ ALL TESTS PASSED')
else:
    print('✗ SOME TESTS FAILED')
