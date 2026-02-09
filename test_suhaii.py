"""
Test extraction with Suhaii Permai Inda data (name before IC)
"""

from malaysia_ic_extractor_ultimate import UltimateICExtractor

# Simulated OCR output - name appears BEFORE IC number
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

print("OCR TEXT WITH INDICES:")
for i, line in enumerate(ocr_text):
    print(f"[{i:2d}] {line}")

extractor = UltimateICExtractor()
result = extractor.extract(ocr_text)

print("\nEXTRACTION RESULTS")
print("=" * 80)
print(f"IC Number:  {result['ic_number']}")
print(f"Name:       {result['name']}")
print(f"Address:    {result['address']}")
print(f"Gender:     {result['gender']}")
print(f"Religion:   {result['religion']}")
print("=" * 80)

print("\nEXPECTED VALUES:")
print(f"IC Number:  990610-07-6113")
print(f"Name:       MUHAMAD KHAIRUL IKHWAN (+ BIN SUHAIMY if detected)")
print(f"Address:    DG-12 LORONG HELANG 3, DESA PERMAI INDAH, SUNGAI DUA, 11700 GELUGOR, PULAU PINANG")
print(f"Gender:     Female (last digit 3 = female)")
print(f"Religion:   ISLAM")
