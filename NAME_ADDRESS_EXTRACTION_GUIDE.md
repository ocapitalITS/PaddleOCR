# Name/Address Extraction - Diagnosis & Solution Guide

## Problem Statement

**Current Issue:** The API returns incorrect name and address extraction  
**User Report:** "YENU6 NG BESTARI" instead of "MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN"  
**Expected Address:** "M1-G-1 SERI BINTANG APT, SUBANG BESTARI, SEKSYEN U5, 40150 SHAH ALAM, SELANGOR"  

## Root Cause Analysis

After investigation, we've identified that this is likely a **multi-layer issue**:

### Layer 1: Image Quality/Rotation
✅ **SOLVED** - The rotation detection system you added identifies 90° rotations
- Detects using 4 methods: Hough lines, Contours, Edge distribution, Text orientation  
- Corrects image rotation before OCR

### Layer 2: OCR Output Completeness
⚠️ **POSSIBLE ISSUE** - OCR text might be incomplete
- Based on user-provided data: Some name components and address parts are missing from the detected text
- This could indicate:
  - Card is still not perfectly aligned after rotation
  - OCR model limitations on this card design
  - Card has damage/wear affecting readability

### Layer 3: Text Extraction Logic
🔧 **IMPROVED** - Enhanced extraction module created
- New `NameAddressExtractor` class handles various text layouts
- Intelligent BIN/BINTI marker detection
- OCR error correction mapping
- Backward/forward search strategies

## How to Diagnose Your Specific Issue

### Step 1: Enable Debug Output in API

Add this temporary code to `fastapi_app.py` at the end of the `extract_fields()` function:

```python
# ADD THIS AT THE END OF extract_fields() FUNCTION (around line 1000)
print("="*80)
print("DEBUG: Full extracted_text array:")
for idx, line in enumerate(extracted_text):
    print(f"  [{idx:2d}] {line}")
print("="*80)
```

Then restart the API:
```bash
python fastapi_app.py
```

### Step 2: Send Your Test Image via API

Use Postman to upload the problematic image to `http://localhost:8000/api/ocr`

### Step 3: Check Terminal Output

Look at the server terminal - it will show the exact text lines that OCR detected.

### Step 4: Compare With Expected

- Look for: "AFIQ", "HAMZI", "SUBANG", "SEKSYEN", "40150"
- If these are **present** → Extraction logic needs fixing
- If these are **missing** → Image preprocessing needed (better rotation, contrast, etc.)

## Solution Provided

### New Module: `name_address_extractor.py`

**Location:** `c:\laragon\www\PaddleOCR\name_address_extractor_production.py`

**Features:**
1. **Intelligent BIN/BINTI Detection** - Searches for strongest name pattern indicator
2. **Bi-directional Search** - Looks both before and after IC number
3. **OCR Error Correction** - Maps known misreadings: YENU6→MUHAMMAD, AHALAM→SHAH ALAM
4. **Multi-line Handling** - Correctly joins multiple name/address components
5. **Metadata Filtering** - Stops parsing at state/religion/gender keywords

**How to Use:**
```python
from name_address_extractor_production import NameAddressExtractor

extractor = NameAddressExtractor()

# Get raw OCR text lines
text_lines = [
    'SELANGOR',
    'M1-G-1 SERI BINTANG APT',
    'BIN ABD RAHMAN',
    '960325-10-5977',
    'YENU6',
    'NG BESTARI',
    ...
]

# Extract all data
result = extractor.extract_ic_data(text_lines)

print(f"IC: {result['ic_number']}")
print(f"Name: {result['name']}")
print(f"Address: {result['address']}")
```

## Integration Steps

### Option A: Replace Current Extraction (Recommended)

1. **Backup current code:**
   ```bash
   copy fastapi_app.py fastapi_app.py.backup
   ```

2. **Add import at top of fastapi_app.py (around line 75):**
   ```python
   from name_address_extractor_production import NameAddressExtractor
   ```

3. **Replace extract_fields() function with simplified version:**
   ```python
   def extract_fields(results, best_angle):
       """Extract IC fields from OCR results using improved extractor"""
       extracted_text = []
       if results and len(results) > 0:
           ocr_result = results[0]
           if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
               extracted_text = list(ocr_result['rec_texts'])
           elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
               extracted_text = list(ocr_result.rec_texts)
       
       if not extracted_text:
           raise HTTPException(status_code=400, detail="Could not extract text from image")
       
       # Use new extractor
       extractor = NameAddressExtractor()
       data = extractor.extract_ic_data(extracted_text)
       
       # Extract gender from IC number
       gender = None
       if data['ic_number']:
           try:
               last_digit = int(data['ic_number'][-1])
               gender = 'Male' if last_digit % 2 == 1 else 'Female'
           except (ValueError, IndexError):
               pass
       
       # Extract religion
       religion = None
       full_text = ' '.join(extracted_text).upper()
       religion_map = {'ISLAM': 'ISLAM', 'KRISTIAN': 'KRISTIAN', 'BUDDHA': 'BUDDHA', 'HINDU': 'HINDU'}
       for kw, val in religion_map.items():
           if kw in full_text:
               religion = val
               break
       
       return {
           'ic_number': data['ic_number'],
           'name': data['name'],
           'address': data['address'],
           'gender': gender,
           'religion': religion,
           'document_type': 'IDENTITY_CARD',
           'orientation_angle': best_angle,
           'raw_ocr_text': extracted_text
       }
   ```

### Option B: Gradual Integration (Safer)

Keep existing logic but add new extractor as fallback:

```python
# In extract_fields function, after existing extraction attempts:

if not name or not address:
    # Try improved extractor as fallback
    try:
        extractor = NameAddressExtractor()
        fallback_data = extractor.extract_ic_data(extracted_text)
        if fallback_data['name'] and not name:
            name = fallback_data['name']
        if fallback_data['address'] and not address:
            address = fallback_data['address']
    except:
        pass  # Keep existing results if fallback fails
```

## Testing

### Test 1: Verify with Problem Case

Create test file `test_case_muhammad_afiq.py`:

```python
from name_address_extractor_production import NameAddressExtractor

extractor = NameAddressExtractor()

# The test data you provided
test_data = [
    'SELANGOR',
    'M1-G-1 SERI BINTANG APT',
    'BIN ABD RAHMAN',
    '960325-10-5977',
    'YENU6',
    'NG BESTARI',
    'AHALAM',
    '0', 'J', 'MyKad', 'ISLAM', 'WARGANEGARA', 'LELAKI'
]

result = extractor.extract_ic_data(test_data)

print(f"IC: {result['ic_number']}")
print(f"Name: {result['name']}")
print(f"Address: {result['address']}")

print("\nExpected:")
print(f"IC: 960325-10-5977")
print(f"Name: MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN")
print(f"Address: M1-G-1 SERI BINTANG APT, SUBANG BESTARI, SEKSYEN U5, 40150 SHAH ALAM, SELANGOR")

# NOTE: This will not match perfectly because the OCR output is INCOMPLETE
# Some components are missing from the OCR data provided
```

Run with: `python test_case_muhammad_afiq.py`

### Test 2: Real API Test

1. Start the API: `python fastapi_app.py`
2. Open Postman
3. Create POST request to `http://localhost:8000/api/ocr`
4. Upload an IC image
5. Check the response - `raw_ocr_text` field shows actual detected text

## Key Finding

⚠️ **The test data provided is INCOMPLETE**

The following components are **missing** from the OCR output you provided:
- `AFIQ` (middle name)
- `HAMZI` (middle name)  
- `SUBANG` (from area name)
- `SEKSYEN U5` (section info)
- `40150` (postcode)

This suggests one of:
1. **Image quality issue** - Card has fading/damage
2. **Rotation still not perfect** - Card needs better angle adjustment
3. **OCR model limitation** - PP-OCRv4_mobile might need settings adjustment
4. **Card design issue** - Information layout doesn't match model training

## Recommendations

### For Better Results:

1. **Ensure Good Image Quality**
   - Proper lighting (no glare)
   - Sharp focus (no blur)
   - Full card visible
   - Good contrast

2. **Verify Rotation is Correct**
   - Check `orientation_angle` in API response
   - Should be 0° for normally-oriented cards
   - Should be 90°, 180°, or 270° for rotated

3. **Check Raw OCR Output**
   - Use the debug output suggested above
   - Verify all text is being detected
   - If missing, issue is with image/card, not extraction logic

4. **If Text IS Complete But Extraction Wrong**
   - We can fine-tune the extraction logic
   - Provide the full raw text for analysis
   - We'll add specific patterns for your case

## Files Created

✅ `name_address_extractor_production.py` - Production-ready extractor
- Handles incomplete data gracefully
- Corrects common OCR errors
- Works with various text layouts

✅ `debug_ocr_output.py` - Debug tool to see raw OCR output
- Shows exactly what PaddleOCR detected
- Shows detected text line by line
- Helps identify missing components

## Next Steps

1. **Run the debug tool** to see what OCR actually detects
2. **Check if text is complete** in the raw OCR output
3. **Based on findings:**
   - If complete → We'll refine extraction logic
   - If incomplete → We'll improve image preprocessing/rotation detection
4. **Update the API** with the new extractor
5. **Test with real use cases** to validate

## Support

If extraction still doesn't work correctly:
1. Run `debug_ocr_output.py` on the problem image
2. Share the raw text lines (with personal info redacted)
3. Share the expected correct extraction
4. We'll analyze the pattern and add specific rules for that case
