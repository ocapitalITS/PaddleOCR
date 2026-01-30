# Malaysia IC OCR Flask API - Setup & Testing Guide

## 📋 Overview

This Flask API provides endpoints for processing Malaysia Identity Cards (MyKad) using OCR technology. It can extract:
- IC Number
- Full Name
- Gender
- Religion
- Address
- Postcode Validation

## 🚀 Quick Start

### 1. Install Flask
```bash
pip install flask
```

### 2. Run the API Server
```bash
# From the PaddleOCR directory
python flask_api.py
```

Expected output:
```
Starting Malaysia IC OCR Flask API...
Available endpoints:
  GET  http://localhost:5000/api/health
  GET  http://localhost:5000/api/info
  POST http://localhost:5000/api/ocr
  POST http://localhost:5000/api/ocr/batch
  ...
 * Running on http://0.0.0.0:5000
```

## 🧪 Testing with Postman

### Option 1: Import Collection File
1. Open Postman
2. Click **Import** → **File** → Select `Malaysia_IC_OCR_API.postman_collection.json`
3. All endpoints will be pre-configured

### Option 2: Manual Setup

#### Endpoint 1: Health Check
```
GET http://localhost:5000/api/health

Response:
{
  "status": "healthy",
  "service": "Malaysia IC OCR API",
  "version": "1.0.0",
  "timestamp": "2026-01-21T10:30:00"
}
```

#### Endpoint 2: API Info
```
GET http://localhost:5000/api/info

Response:
{
  "api_name": "Malaysia IC OCR API",
  "version": "1.0.0",
  "endpoints": {...},
  "supported_formats": ["JPG", "PNG", "PDF"],
  "max_file_size": "20MB",
  "postcode_db_loaded": true,
  "postcode_count": 1500
}
```

#### Endpoint 3: Process Single Image
```
POST http://localhost:5000/api/ocr

Headers:
(None - Postman sets Content-Type automatically)

Body:
- Form-data
- Key: "file"
- Value: Select your IC image/PDF file

Response Example:
{
  "success": true,
  "data": {
    "ic_number": "920521-03-5949",
    "name": "MUHAMAD SAFUAN BIN ABDULLAH SIDEK",
    "gender": "Male",
    "religion": "ISLAM",
    "address": "828, JALAN SEKOLAH CINA, 17200 RANTAU PANJANG, KELANTAN",
    "postcode_validation": {
      "postcode": "17200",
      "state": "KELANTAN",
      "is_valid": true,
      "warning": null
    },
    "document_type": "Malaysia Identity Card (MyKad)",
    "orientation_angle": 0,
    "raw_ocr_text": ["KAD PENGENALAN", "MyKad", "920521-03-5949", ...]
  }
}
```

#### Endpoint 4: Batch Process Multiple Images
```
POST http://localhost:5000/api/ocr/batch

Headers:
(None - Postman sets Content-Type automatically)

Body:
- Form-data
- Key: "files" (note: plural)
- Value: Select multiple IC image/PDF files

Response Example:
{
  "success": true,
  "total": 3,
  "processed": 3,
  "results": [
    {
      "filename": "ic1.jpg",
      "success": true,
      "data": {...}
    },
    {
      "filename": "ic2.jpg",
      "success": true,
      "data": {...}
    },
    {
      "filename": "ic3.pdf",
      "success": false,
      "error": "PDF processing error"
    }
  ]
}
```

## 📝 Postman Step-by-Step Guide

### Step 1: Create Request
1. Click **+** to create new request
2. Enter request name: "Process IC Image"
3. Select method: **POST**
4. Enter URL: `http://localhost:5000/api/ocr`

### Step 2: Set Body
1. Click **Body** tab
2. Select **form-data**
3. In the table:
   - Key: `file`
   - Type: Change to **File**
   - Value: Click **Select Files** and choose your IC image/PDF

### Step 3: Send Request
1. Click **Send** button
2. View response in the panel below

### Step 4: Check Results
- Look for "success": true
- Extract data from "data" object
- If error, check "error" field for details

## 🔄 Common Test Scenarios

### Test 1: Valid IC Image
**File:** JPG/PNG of Malaysia IC front
**Expected:** All fields populated, document_type = "Malaysia Identity Card (MyKad)"

### Test 2: Upside-Down IC
**File:** IC image rotated 180 degrees
**Expected:** API auto-detects orientation, returns correct data, orientation_angle = 180

### Test 3: PDF Format
**File:** PDF scan of Malaysia IC
**Expected:** Converts PDF to image, processes OCR, returns data

### Test 4: Invalid Postcode
**File:** IC with non-existent postcode
**Expected:** is_valid = false, warning contains message

### Test 5: Multiple Files
**Endpoint:** `/api/ocr/batch`
**Files:** 5 IC images
**Expected:** All processed in one request, returns results array

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Change port in flask_api.py line at bottom:
app.run(host='0.0.0.0', port=5001, debug=True)  # Change 5000 to another port
```

### File Not Uploading
- Check file format (JPG, PNG, PDF only)
- Verify file size < 20MB
- Ensure form-data key is "file" (case-sensitive)

### Postcode Database Not Loaded
- Check if `malaysia-postcodes-main/` folder exists
- Verify file path in flask_api.py
- API still works but returns is_valid=false for postcodes

### OCR Results Empty
- Check image quality
- Try rotating image manually
- Ensure image contains readable text

## 📊 Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (missing file, invalid format) |
| 413 | File too large |
| 404 | Endpoint not found |
| 500 | Server error |

## 🔐 Security Notes

- API accepts files up to 20MB
- File types restricted to JPG, PNG, PDF
- Filenames sanitized with `secure_filename()`
- No data is stored on server
- Consider adding authentication for production

## 🚄 Performance Metrics

| Metric | Value |
|--------|-------|
| Single image processing | 30-60 seconds |
| Batch processing | Scales linearly |
| Memory per request | ~500MB |
| GPU | Not required |

## 📚 API Response Structure

```json
{
  "success": true,
  "data": {
    "ic_number": "string",
    "name": "string",
    "gender": "string (LELAKI/PEREMPUAN)",
    "religion": "string (ISLAM/KRISTIAN/etc)",
    "address": "string",
    "postcode_validation": {
      "postcode": "5 digits",
      "state": "string",
      "is_valid": true/false,
      "warning": "null or message"
    },
    "document_type": "string",
    "orientation_angle": 0/90/180/270,
    "raw_ocr_text": ["text line 1", "text line 2", ...]
  }
}
```

## 🔄 Upgrade to Production

For production deployment, consider:

1. Use **Gunicorn** instead of Flask dev server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 flask_api:app
```

2. Add **environment variables** for config:
```python
import os
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 20 * 1024 * 1024))
```

3. Enable **HTTPS/SSL**:
```python
app.run(ssl_context='adhoc')
```

4. Add **logging and monitoring**:
```python
from flask import request
import logging
logging.basicConfig(filename='api.log', level=logging.INFO)
```

5. Implement **rate limiting**:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)
@app.route('/api/ocr')
@limiter.limit("10 per minute")
def process_ocr():
    ...
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API logs in terminal
3. Verify all dependencies are installed
4. Ensure Malaysia postcode database is present

---

**API Version:** 1.0.0  
**Last Updated:** January 21, 2026  
**Status:** Ready for Testing ✅
