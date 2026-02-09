"""
Debug address extraction for Suhaii
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
result = extractor.extract(ocr_text)

print("EXTRACTION RESULTS")
print("=" * 80)
print(f"Address:    {result['address']}")
print("=" * 80)

print("\nAddress components breakdown:")
for comp in result['address'].split(','):
    print(f"  - {comp.strip()}")

print("\n\nExpected address:")
print("  - DG-12")
print("  - LORONG HELANG 3")
print("  - DESA PERMAI INDAH")
print("  - SUNGAI DUA")
print("  - 11700 GELUGOR")
print("  - PULAU PINANG")
