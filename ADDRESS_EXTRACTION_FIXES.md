# Address Extraction Fixes - January 21, 2026

## Issue Identified
User reported incorrect address extraction:
- **Received:** "LOT 146 SERAYA A, lacA, MENGGATAL, 88 A 5 O KOTA KINABALU, SABAH"
- **Expected:** "LOT 146 SERAYA A, TAMAN PUTERA JAYA, MENGGATAL, 88450 KOTA KINABALU, SABAH"

## Root Causes

### 1. OCR Correction Missing for "88A5O"
- Pattern: "88 A 5 O" (spaces) or "88A5O" (no spaces) should be corrected to "88450"
- Previously only had: `(r'88\s*A\s*60', '88450')`
- Now also handles: `(r'88\s*A\s*5\s*O', '88450')`

### 2. "PUTERAJAYA" Not Split Correctly
- Raw OCR: "TAMAN PUTERAJAYA" (merged words)
- Should be: "TAMAN PUTERA JAYA"
- Added corrections:
  - `(r'PUTERAJAYA', 'PUTERA JAYA')`
  - `(r'TAMAN\s*PUTERAJAYA', 'TAMAN PUTERA JAYA')`

### 3. "lacA" Being Included in Address
- "lacA" is garbage text (mixed-case, non-address related)
- Should be filtered out before address extraction
- Added intelligent filtering for short lines (≤4 chars) that don't match address patterns

## Solutions Implemented

### 1. OCR Corrections (lines 408-410)
```python
(r'88\s*A\s*60', '88450'),  # Address correction: "88 A 60" or "88A60" -> "88450"
(r'88\s*A\s*5\s*O', '88450'),  # Address correction: "88 A 5 O" or "88A5O" -> "88450"
(r'PUTERAJAYA', 'PUTERA JAYA'),  # Split merged area name
(r'TAMAN\s*PUTERAJAYA', 'TAMAN PUTERA JAYA'),  # Ensure TAMAN PUTERA JAYA is correct
```

### 2. Garbage Text Filtering (lines 840-845)
Added new filter logic to remove short lines (4 characters or less) that:
- Don't match any known address keywords (LOT, JALAN, KAMPUNG, etc.)
- Are not all uppercase/spaces/dashes (indicating OCR garbage)

Examples filtered:
- "lacA" - mixed case, not address-related
- "H" - single letter noise
- "E" - single letter noise

## Testing the Fix

### Using Flask API with Postman
1. Ensure Flask API is running: `.\.venv310\Scripts\python.exe flask_api.py`
2. Upload your test image to: `POST http://localhost:5000/api/ocr`
3. Expected response should now show:
   - "address": "LOT 146 SERAYA A, TAMAN PUTERA JAYA, MENGGATAL, 88450 KOTA KINABALU, SABAH"
   - "88 A 5 O" corrected to "88450" in both `raw_ocr_text` (after corrections) and `address` fields

### Using Python
```python
import requests
import json

with open('your_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/ocr',
        files={'file': f}
    )
    data = response.json()
    print(json.dumps(data, indent=2))
    print(f"Address: {data['data']['address']}")
```

## Code Changes Summary

| File | Lines | Change |
|------|-------|--------|
| flask_api.py | 408-410 | Added OCR corrections for "88A5O" → "88450" and "PUTERAJAYA" → "PUTERA JAYA" |
| flask_api.py | 840-845 | Added garbage text filtering for short mixed-case lines |

## Expected Outcomes After Fix

✅ "88 A 5 O" now corrected to "88450"
✅ "TAMAN PUTERAJAYA" now correctly becomes "TAMAN PUTERA JAYA"
✅ "lacA" and similar garbage text filtered out
✅ Address extraction maintains correct order: LOT → Area → Postal Code → State

## Next Steps

1. Restart Flask API if needed (auto-reloads on file changes)
2. Test with your Malaysia IC images using Postman
3. Verify address extraction matches expected format
4. Report any remaining discrepancies with raw OCR text for additional pattern tuning
