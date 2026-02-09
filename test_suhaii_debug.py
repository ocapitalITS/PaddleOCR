"""
Debug extraction with Suhaii Permai Inda data
"""

from malaysia_ic_extractor_ultimate import UltimateICExtractor

# Simulated OCR output
ocr_text = [
    "PULAU PINANG",
    "SUNGAI DUA",
    "MUHAMAD KHAIRUL IKHWAN",
    "990610-07-6113",
    "1700 GELUGOR",
    "SUHAII",
    "PERMAI INDA",
    "?",
    "LORONG HELANG3",
    "MyKad",
    "ISLAM",
    "WARGANEGARA",
    "LELAKI"
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
        print(f"\nIC found at index {ic_idx}")
        break

# Check name position
name_in_filtered = "MUHAMAD KHAIRUL IKHWAN" in ' '.join(filtered_lines)
name_pos = -1
for idx, line in enumerate(filtered_lines):
    if "MUHAMAD KHAIRUL IKHWAN" in line:
        name_pos = idx
        break

print(f"Name found at index {name_pos}")
print(f"IC index: {ic_idx}")
print(f"Name is before IC: {name_pos < ic_idx}")

result = extractor.extract(ocr_text)

print("\nEXTRACTION RESULTS")
print("=" * 80)
print(f"IC Number:  {result['ic_number']}")
print(f"Name:       {result['name']}")
print(f"Address:    {result['address']}")
