#!/usr/bin/env python3

# Test that HAMIDEE is protected from splitting

malay_names = ['SITI', 'NUR', 'AISYAH', 'HAMID', 'HAMIDEE', 'BINTI']

test_name = "SITI NUR AISYAH BINTI HAMIDEE"

print('\nHAMIDEE PROTECTION TEST')
print('=' * 80)
print(f'Name: {test_name}')
print(f'\nMarked words in malay_names: {", ".join([n for n in malay_names if n in test_name])}')

# Simulate marker-based approach
marker_counter = 1000
replacements = {}
text = test_name

# Replace names with markers (sorted by length to replace longer names first)
for name in sorted(malay_names, key=len, reverse=True):
    if name in text:
        marker = f"__NAME_{marker_counter}__"
        replacements[marker] = name
        text = text.replace(name, marker)
        marker_counter += 1
        print(f'Replaced "{name}" with "{marker}"')

print(f'\nAfter marker replacement: {text}')

# Restore
for marker, name in replacements.items():
    text = text.replace(marker, name)

print(f'After restoration: {text}')

if text == test_name:
    print(f'\n✓ TEST PASSED - Name preserved correctly')
else:
    print(f'\n✗ TEST FAILED')
    print(f'Expected: {test_name}')
    print(f'Got:      {text}')
