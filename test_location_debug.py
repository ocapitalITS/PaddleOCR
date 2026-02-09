"""
Debug location collection
"""

from malaysia_ic_extractor_ultimate import UltimateICExtractor

ocr_text = [
    "PULAU PINANG",      # [0] State
    "SUNGAI DUA",        # [1] Location
    "MUHAMAD KHAIRUL IKHWAN",  # [2] Name
    "990610-07-6113",    # [3] IC
    "1700 GELUGOR",      # [4] Postcode + city
    "SUHAII",            # [5] Father's name
    "PERMAI INDA",       # [6] Area
    "?",                 # [7] Placeholder
    "LORONG HELANG3",    # [8] Street
    "MyKad",             # [9] Header
    "ISLAM",             # [10] Religion
    "WARGANEGARA",       # [11] Metadata
    "LELAKI"             # [12] Gender
]

extractor = UltimateICExtractor()

# Filter out Chinese characters manually
filtered_lines = [line.strip() for line in ocr_text if line.strip() and extractor.is_valid_latin_line(line)]

print("Filtered lines:")
for i, line in enumerate(filtered_lines):
    print(f"[{i}] {line}")

# Find IC index
ic_idx = -1
for idx, line in enumerate(filtered_lines):
    if '990610-07-6113' in line:
        ic_idx = idx
        break

print(f"\nIC index: {ic_idx}")
print(f"Lines before IC:")
for i in range(0, ic_idx):
    line = filtered_lines[i].upper()
    print(f"  [{i}] {line}")
    
    # Check if state
    is_state = any(state in line for state in extractor.states)
    print(f"      - Is state? {is_state}")
    if is_state:
        print(f"      - Matched: {[state for state in extractor.states if state in line]}")

result = extractor.extract(ocr_text)
print(f"\n\nFinal Address: {result['address']}")
