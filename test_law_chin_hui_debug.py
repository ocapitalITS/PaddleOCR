"""
Debug extraction with Law Chin Hui data
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
