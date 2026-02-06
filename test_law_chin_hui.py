"""
Test extraction with Law Chin Hui data
"""

from malaysia_ic_extractor_ultimate import UltimateICExtractor

# Simulated OCR output
ocr_text = [
    "KAD PENGENALAN",
    "MyKad",
    "MALAYSIA",
    "CARD",
    "IDENTIT",
    "881215-04-5461",
    "LAW CHIN HUI",
    "NO8",
    "JALAN MAJU B",
    "TAMANJEMENTAH BARU",
    "WARGANEGARA",
    "85200 JEMENTAH",
    "LELAKI",
    "JOHOR"
]

extractor = UltimateICExtractor()
result = extractor.extract(ocr_text)

print("EXTRACTION RESULTS")
print("=" * 80)
print(f"IC Number:  {result['ic_number']}")
print(f"Name:       {result['name']}")
print(f"Address:    {result['address']}")
print(f"Gender:     {result['gender']}")
print(f"Religion:   {result['religion']}")
print("=" * 80)

# Expected values
print("\nEXPECTED VALUES:")
print(f"IC Number:  881215-04-5461")
print(f"Name:       LAW CHIN HUI")
print(f"Address:    NO 8, JALAN MAJU B, TAMAN JEMENTAH BARU, 85200 JEMENTAH, JOHOR")
print(f"Gender:     Male")
print(f"Religion:   N/A (not found)")
