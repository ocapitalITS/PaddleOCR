# Postman Guide for Malaysia IC OCR FastAPI

## Quick Start

### 1. Import the Collection
1. Open **Postman**
2. Click **Import** (top-left)
3. Select **Upload Files**
4. Choose: `FastAPI_OCR_Postman.postman_collection.json`
5. Click **Import**

---

## Manual Setup (If Not Using Collection)

### Step 1: Create a New Collection
1. Click **Collections** on the left
2. Click **+ New Collection**
3. Name it: `Malaysia IC OCR FastAPI`
4. Click **Create**

### Step 2: Add Requests to the Collection

---

## Test Endpoints

### 1. Health Check (GET)

**Purpose:** Verify the API is running and healthy

**Steps:**
1. Click **+ New Request**
2. Set method to **GET**
3. Enter URL: `http://localhost:8000/api/health`
4. Click **Send**

**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "Malaysia IC OCR API (FastAPI)",
  "version": "1.0.0",
  "timestamp": "2026-01-23T10:30:45.123456"
}
```

**What to check:**
- ✅ Status is 200
- ✅ Response says "healthy"
- ✅ Service name contains "FastAPI"

---

### 2. Get API Info (GET)

**Purpose:** See all available endpoints and API details

**Steps:**
1. Click **+ New Request**
2. Set method to **GET**
3. Enter URL: `http://localhost:8000/api/info`
4. Click **Send**

**Expected Response (200 OK):**
```json
{
  "api_name": "Malaysia IC OCR API (FastAPI)",
  "version": "1.0.0",
  "endpoints": {
    "GET /api/health": "Health check",
    "GET /api/info": "Get API information",
    "POST /api/ocr": "Process single IC image/PDF",
    "POST /api/ocr/batch": "Process multiple IC images/PDFs",
    "GET /docs": "Swagger UI documentation",
    "GET /redoc": "ReDoc documentation"
  },
  "supported_formats": ["JPG", "PNG", "PDF"],
  "max_file_size": "20MB",
  "postcode_db_loaded": true,
  "postcode_count": 3421
}
```

---

### 3. Process Single IC Image (POST with File Upload)

**Purpose:** Extract IC information from a single image

**Steps:**
1. Click **+ New Request**
2. Set method to **POST**
3. Enter URL: `http://localhost:8000/api/ocr`
4. Go to **Body** tab
5. Select **form-data**
6. In the table:
   - **Key:** `file` (type: **File**)
   - **Value:** Click "Select Files" and choose your IC image
7. Click **Send**

**Expected Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "ic_number": "123456-12-1234",
    "name": "JOHN BIN SMITH",
    "gender": "LELAKI (Male)",
    "religion": "ISLAM",
    "address": "NO 25, JALAN MUTIARA, TAMAN BUKIT INDAH, 34600 KAMUNTING, PERAK",
    "postcode_validation": {
      "postcode": "34600",
      "state": "PERAK",
      "valid": true
    },
    "document_type": "Malaysia Identity Card (MyKad)",
    "orientation_angle": 0,
    "raw_ocr_text": [
      "KAD PENGENALAN",
      "123456-12-1234",
      "JOHN BIN SMITH",
      "LELAKI",
      "ISLAM",
      "NO 25, JALAN MUTIARA"
    ]
  }
}
```

**Supported Formats:**
- ✅ JPG (.jpg, .jpeg)
- ✅ PNG (.png)
- ✅ PDF (.pdf)

**Max File Size:** 20MB

---

### 4. Batch Process Multiple ICs (POST with Multiple Files)

**Purpose:** Process multiple IC images in one request

**Steps:**
1. Click **+ New Request**
2. Set method to **POST**
3. Enter URL: `http://localhost:8000/api/ocr/batch`
4. Go to **Body** tab
5. Select **form-data**
6. In the table:
   - **Key:** `files` (type: **File**)
   - **Value:** Click "Select Files" and choose multiple IC images
7. Click **Send**

**Expected Response (200 OK):**
```json
{
  "success": true,
  "total": 3,
  "processed": 3,
  "results": [
    {
      "filename": "ic_001.jpg",
      "success": true,
      "data": {
        "ic_number": "123456-12-1234",
        "name": "JOHN BIN SMITH",
        "gender": "LELAKI (Male)",
        "religion": "ISLAM",
        "address": "NO 25, JALAN MUTIARA, TAMAN BUKIT INDAH, 34600 KAMUNTING, PERAK",
        "postcode_validation": {
          "postcode": "34600",
          "state": "PERAK",
          "valid": true
        },
        "document_type": "Malaysia Identity Card (MyKad)",
        "orientation_angle": 0,
        "raw_ocr_text": []
      }
    },
    {
      "filename": "ic_002.jpg",
      "success": true,
      "data": { ... }
    },
    {
      "filename": "ic_003.jpg",
      "success": false,
      "error": "Could not process image at any orientation"
    }
  ]
}
```

---

## Advanced Testing

### Add Tests to Requests

**Steps:**
1. Open any request
2. Click **Tests** tab
3. Add JavaScript code to validate response

**Example Test Script:**
```javascript
// Check status code
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Check success property
pm.test("Response indicates success", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
});

// Check IC number format
pm.test("IC number has correct format", function () {
    var jsonData = pm.response.json();
    var ic = jsonData.data.ic_number;
    pm.expect(ic).to.match(/\d{6}-\d{2}-\d{4}/);
});

// Save response to variable
pm.globals.set("last_ic_number", jsonData.data.ic_number);
```

### Create Pre-Request Script

**Purpose:** Prepare data before sending request

**Example:**
```javascript
// Log request details
console.log("Sending request to:", pm.request.url);
console.log("Method:", pm.request.method);

// Set dynamic variables
pm.globals.set("test_timestamp", new Date().toISOString());
```

---

## Troubleshooting

### Connection Error: "Could not get any response"
**Solution:**
- Check if FastAPI server is running: `http://localhost:8000/api/health`
- Verify port 8000 is not blocked
- Restart the FastAPI server

### 400 Bad Request - "Invalid file type"
**Solution:**
- Use supported formats: JPG, PNG, PDF
- Check file extension is correct
- File size is under 20MB

### 400 Bad Request - "No file provided"
**Solution:**
- Make sure you selected form-data
- Key name must be exactly: `file` (for single) or `files` (for batch)
- File must be selected in Value field

### 422 Unprocessable Entity
**Solution:**
- Check Content-Type header
- For file uploads, let Postman auto-set headers
- Don't manually set Content-Type for multipart/form-data

### Processing takes too long
**Solution:**
- Large images (>3MB) take longer to process
- Resize images before uploading
- Use PNG instead of PDF when possible

---

## Tips & Tricks

### 1. Use Variables for URLs
```
Base URL: {{base_url}}/api
Set in Environment: base_url = http://localhost:8000
```

**Steps:**
1. Click **Environments** (left sidebar)
2. Click **+ Create** 
3. Add variable: `base_url` = `http://localhost:8000`
4. Select environment in top-right dropdown
5. Use `{{base_url}}/api/health` in requests

### 2. Save Responses
1. Open request
2. Click **Send**
3. Click **Save Response** → **Save as example**
4. Useful for documentation

### 3. Use Collections Runner for Batch Testing
1. Click **Collections**
2. Select your collection
3. Click **Run** (play icon)
4. Select which requests to run
5. Click **Run Malaysia IC OCR FastAPI**

### 4. Export Results
1. Run collection
2. Click **Export Results** (at end)
3. Save as JSON for reporting

### 5. Monitor Performance
1. Open **Request** → **Tests** tab
2. Add script:
```javascript
pm.test("Response time is acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000); // 5 seconds
});
```

---

## Common Response Fields Explained

| Field | Meaning |
|-------|---------|
| `ic_number` | Extracted IC number (format: 123456-12-1234) |
| `name` | Full name from IC |
| `gender` | LELAKI (Male) or PEREMPUAN (Female) |
| `religion` | Religion code from IC |
| `address` | Full address extracted from IC |
| `postcode_validation` | Validates postcode against Malaysia database |
| `document_type` | Type of document detected |
| `orientation_angle` | Rotation angle of image (0, 90, 180, 270) |
| `raw_ocr_text` | Raw text extracted before processing |

---

## Testing Workflow

### Complete Testing Flow:
1. ✅ **Health Check** - Verify API is online
2. ✅ **API Info** - Review available endpoints
3. ✅ **Single IC** - Test with one image
4. ✅ **Batch Processing** - Test with multiple images
5. ✅ **Error Cases** - Test with invalid files
6. ✅ **Performance** - Check response times

---

## Need More Help?

- **Swagger UI:** http://localhost:8000/docs (interactive API explorer)
- **ReDoc:** http://localhost:8000/redoc (detailed API documentation)
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Postman Docs:** https://learning.postman.com/docs/

---

## Sample IC Images for Testing

To test, you need sample IC images. You can:
1. Use real IC images (if available)
2. Download sample images from your test folder
3. Create test images using phone camera
4. Use PDF scans of ICs

**Note:** Ensure all test images comply with privacy regulations.
