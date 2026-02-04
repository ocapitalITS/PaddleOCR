# ADDRESS ORDERING AND FORMATTING FIX

## Issues Fixed

### 1. Unit Number Spacing
**Before:** `"3 B-2-2 SRI LOJING CONDO"` (unwanted space between digit and letter)
**After:** `"3B-2-2 SRI LOJING CONDO"` (proper spacing preserved)
**Fix:** Added check to skip spacing regex patterns when line contains unit number format `\d+[A-Z]-[\d\-A-Z]+`

### 2. Missing Area Components
**Before:** `"JLN 4/27 E SEKSYEN 10, 3 B-2-2 SRI LOJING CONDO, W.PERSEKUTUAN(KL), 53300 KUALA LUMPUR"`
- Missing: WANGSA MAJU (area name)
- Wrong order: Street should be second (after unit), area markers should follow
**After:** `"3B-2-2 SRI LOJING CONDO, JLN 4/27E, SEKSYEN 10, WANGSA MAJU, 53300 KUALA LUMPUR, W. PERSEKUTUAN (KL)"`
**Fix:** Added preprocessing to split lines containing both street keywords and area markers

### 3. State/Federal Territory Formatting  
**Before:** `"W.PERSEKUTUAN(KL)"` (no spaces)
**After:** `"W. PERSEKUTUAN (KL)"` (proper spacing)
**Fix:** Added regex replacement to format federal territory notation

### 4. Area Keywords Recognition
**Before:** "WANGSA MAJU" was not recognized as an area name (fell into "localities")
**After:** "WANGSA MAJU" properly categorized as area name
**Fix:** Added "SEKSYEN", "WANGSA", "MAJU" to area_names keywords

## Changes Made

### fastapi_app.py
1. **Lines 854-859:** Fixed spacing logic to skip unit number patterns
   ```python
   if not re.search(r'^\d+[A-Z]-[\d\-A-Z]+', corrected_line):
       corrected_line = re.sub(r'([A-Z]+)(\d)(?!/)', r'\1 \2', corrected_line)
       corrected_line = re.sub(r'(\d)([A-Z])(?!/)', r'\1 \2', corrected_line)
   ```

2. **Lines 866-885:** Added line-splitting preprocessing for street+area combinations
   ```python
   processed_lines = []
   for line in address_lines:
       has_street = any(kw in line_upper for kw in ['JALAN', 'JLN', 'LORONG', 'LEBUH'])
       has_area_marker = any(kw in line_upper for kw in ['SEKSYEN', 'BUKIT', 'BANDAR', 'TAMAN'])
       if has_street and has_area_marker:
           # Split at area marker
   ```

3. **Line 916:** Added area keywords
   ```python
   elif any(kw in line_upper for kw in [..., 'SEKSYEN', 'WANGSA', 'MAJU']):
   ```

4. **Lines 936-938:** Added state formatting
   ```python
   address = re.sub(r'W\.PERSEKUTUAN\(', 'W. PERSEKUTUAN (', address)
   address = re.sub(r'W\.PERSEKUTUAN', 'W. PERSEKUTUAN', address)
   ```

### flask_api.py
- Same fixes applied at:
  - Lines 1191-1196: Spacing logic
  - Lines 1221-1241: Line-splitting preprocessing
  - Line 1250: Area keywords
  - Lines 1301-1303: State formatting

### malaysia_ic_ocr.py
- Same fixes applied at:
  - Lines 920-925: Spacing logic
  - Lines 938-958: Line-splitting preprocessing
  - Lines 962-964: State formatting

## Test Results
✓ Unit number spacing preserved
✓ Line splitting for street+area markers works correctly
✓ All address components included (unit, street, area markers, area names, postcode, state)
✓ Proper order maintained
✓ Federal territory formatting correct

## Expected Final Address
```
3B-2-2 SRI LOJING CONDO, JLN 4/27E, SEKSYEN 10, WANGSA MAJU, 53300 KUALA LUMPUR, W. PERSEKUTUAN (KL)
```
