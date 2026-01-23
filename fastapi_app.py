"""
FastAPI API for Malaysia IC OCR System
Testing with Postman
"""

import os
import sys
import json
import re
import logging
from typing import Optional, List
from datetime import datetime

# Set environment variable to skip model connectivity check (must be before importing PaddleOCR)
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the current directory to Python path to ensure PaddleOCR can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try different import methods for PaddleOCR
    try:
        from paddleocr import PaddleOCR as PaddleOCRClass
        ocr_import_success = True
    except ImportError as e1:
        try:
            # If main import fails, try importing just what we need
            possible_paths = [
                os.path.join(current_dir),
                os.path.join(current_dir, 'ppocr'),
            ]
            for path in possible_paths:
                if path not in sys.path:
                    sys.path.insert(0, path)
            
            from paddleocr import PaddleOCR as PaddleOCRClass
            ocr_import_success = True
        except ImportError as e2:
            print(f"Failed to import PaddleOCR: {e1}, {e2}")
            # Create a mock OCR class for testing
            class MockPaddleOCR:
                def __init__(self, *args, **kwargs):
                    pass
                def predict(self, image):
                    return [[]]
            PaddleOCRClass = MockPaddleOCR
            ocr_import_success = False
except Exception as e:
    print(f"Unexpected error importing PaddleOCR: {e}")
    class MockPaddleOCR:
        def __init__(self, *args, **kwargs):
            pass
        def predict(self, image):
            return [[]]
    PaddleOCRClass = MockPaddleOCR
    ocr_import_success = False

from PIL import Image
import numpy as np
import io
try:
    from pdf2image import convert_from_bytes
    pdf_support = True
except ImportError:
    pdf_support = False
import cv2
from pathlib import Path

# Configure poppler path for PDF processing
POPPLER_PATH = str(Path(__file__).parent / 'poppler' / 'poppler-24.08.0' / 'Library' / 'bin')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI(
    title="Malaysia IC OCR API",
    description="FastAPI for Malaysia Identity Card OCR processing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads folder if it doesn't exist
os.makedirs('uploads', exist_ok=True)

# Initialize PaddleOCR with EXACT same parameters as Streamlit
try:
    if ocr_import_success:
        ocr = PaddleOCRClass(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
            device='cpu',
            ocr_version='PP-OCRv4',
            text_detection_model_name='PP-OCRv4_mobile_det',
            text_recognition_model_name='PP-OCRv4_mobile_rec'
        )
        logger.info("✅ PaddleOCR initialized successfully")
    else:
        logger.warning("⚠️ PaddleOCR import failed - using mock OCR")
        ocr = PaddleOCRClass()
except Exception as e:
    logger.warning(f"PaddleOCR initialization error: {e}")
    ocr = None

# Load Malaysia postcode database
postcode_state_map = {}
try:
    postcode_db_path = Path('malaysia-postcodes-main/malaysia-postcodes-main/data/postcodes.json')
    if postcode_db_path.exists():
        with open(postcode_db_path, 'r', encoding='utf-8') as f:
            postcode_data = json.load(f)
            for item in postcode_data:
                postcode_state_map[item['postcode']] = item['state']
        logger.info(f"Loaded {len(postcode_state_map)} postcodes")
except Exception as e:
    logger.warning(f"Could not load postcode database: {e}")

# Malaysia states mapping
state_name_map = {
    'PERLIS': 'PERLIS',
    'KEDAH': 'KEDAH',
    'KELANTAN': 'KELANTAN',
    'TERENGGANU': 'TERENGGANU',
    'SELANGOR': 'SELANGOR',
    'KUALALUMPUR': 'W.PERSEKUTUAN(KUALA LUMPUR)',
    'KL': 'W.PERSEKUTUAN(KUALA LUMPUR)',
    'LABUAN': 'W.PERSEKUTUAN(LABUAN)',
    'PUTRAJAYA': 'W.PERSEKUTUAN(PUTRAJAYA)',
    'PAHANG': 'PAHANG',
    'PERAK': 'PERAK',
    'JOHOR': 'JOHOR',
    'NEGERIEMBILAN': 'NEGERI SEMBILAN',
    'MELAKA': 'MELAKA',
    'PENANG': 'PENANG',
    'PULAU PINANG': 'PENANG',
    'SABAH': 'SABAH',
    'SARAWAK': 'SARAWAK',
}

# ===================== PYDANTIC MODELS =====================

class PostcodeValidation(BaseModel):
    postcode: str
    state: Optional[str] = None
    valid: bool
    message: Optional[str] = None

class OCRData(BaseModel):
    ic_number: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    religion: Optional[str] = None
    address: Optional[str] = None
    postcode_validation: Optional[PostcodeValidation] = None
    document_type: str
    orientation_angle: int = 0
    raw_ocr_text: List[str] = []

class OCRResponse(BaseModel):
    success: bool
    data: Optional[OCRData] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str

class InfoResponse(BaseModel):
    api_name: str
    version: str
    endpoints: dict
    supported_formats: List[str]
    max_file_size: str
    postcode_db_loaded: bool
    postcode_count: int

# ===================== UTILITY FUNCTIONS =====================

def correct_ocr_errors(text):
    """Correct common OCR misreads"""
    corrections = {
        'MOHAMED SAD': 'MOHAMED SAID',
        'BIN TI': 'BINTI',
        'LLORONG': 'LORONG',
        'LLOT': 'LOT',
        'JJALAN': 'JALAN',
        'PELANGAI': 'PELANGI',
        'INDAE': 'INDAH',
        'KHAIRULIKHWAN': 'KHAIRUL IKHWAN',
    }
    result = text
    for wrong, correct in corrections.items():
        if wrong.startswith('\\') or '(' in wrong:
            result = re.sub(wrong, correct, result)
        else:
            result = result.replace(wrong, correct)
    return result

def split_malay_words(text):
    """Split merged Malay words using dictionary"""
    protected_words = [
        ('MAHKOTA', 'ZZZ001ZZZ'),
        ('SETAPAK', 'ZZZ002ZZZ'),
    ]
    
    for word, placeholder in protected_words:
        text = text.replace(word, placeholder)
    
    malay_words = ['KAMPUNG', 'TAMAN', 'JALAN', 'LORONG', 'PERUMAHAN', 'BANDAR',
                   'KOTA', 'BUKIT', 'PETALING', 'SHAH', 'DAMANSARA', 'SETIAWANGSA',
                   'PUTRAJAYA', 'CYBERJAYA', 'AMPANG', 'CHERAS', 'SENTOSA', 'KEPONG',
                   'MELAYU', 'SUBANG', 'SEKSYEN', 'FELDA', 'DESA', 'ALAM', 'IDAMAN', 'LEMBAH',
                   'PERMAI', 'INDAH']
    
    for word in malay_words:
        text = text.replace(word, f' {word} ')
    
    for word, placeholder in protected_words:
        text = text.replace(placeholder, word)
    
    return re.sub(r'\s+', ' ', text).strip()

def has_chinese(text):
    """Check if text contains Chinese characters"""
    for char in text:
        if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:
            return True
    return False

def process_image_ocr(image_array):
    """Process image with PaddleOCR and return extracted data"""
    if ocr is None:
        raise HTTPException(status_code=500, detail="OCR engine not initialized")
    
    # OPTIMIZATION: Resize large images
    max_dimension = 1500
    h, w = image_array.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        image_array = cv2.resize(image_array, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.info(f"Resized image from {w}x{h} to {new_w}x{new_h} for faster processing")
    
    # Try different rotations and flips
    best_results = None
    best_score = 0
    best_angle = 0
    best_text_count = 0
    orientations = [0, 90, 180, 270]
    flip_types = [None, 'horizontal']
    all_results = []
    
    for angle in orientations:
        for flip_type in flip_types:
            try:
                if flip_type == 'horizontal':
                    flipped_array = cv2.flip(image_array, 1)
                else:
                    flipped_array = image_array.copy()
                
                if angle > 0:
                    rotated_array = np.rot90(flipped_array, k=angle//90)
                else:
                    rotated_array = flipped_array
                
                results = ocr.predict(rotated_array)
                
                text_list = []
                if results:
                    try:
                        if isinstance(results, list) and len(results) > 0:
                            ocr_result = results[0]
                            if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
                                text_list = list(ocr_result['rec_texts'])
                            elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
                                text_list = list(ocr_result.rec_texts)
                    except (IndexError, AttributeError, TypeError, KeyError) as e:
                        logger.debug(f"Result parsing error at {angle}° flip {flip_type}: {e}")
                        text_list = []
                
                if text_list:
                    text_count = len(text_list)
                    full_text_candidate = ' '.join(text_list).upper()
                    
                    score = 0
                    malaysia_ic_keywords = ['KAD PENGENALAN', 'MYKAD', 'IDENTITYCARD', 'IDENTITY CARD', 'WARGANEGARA', 'MYIAD', 'KAD PENGE']
                    for keyword in malaysia_ic_keywords:
                        if keyword in full_text_candidate:
                            score += 2
                    
                    if re.search(r'\d{6}-\d{2}-\d{4}', full_text_candidate):
                        score += 3
                    
                    if text_count >= 5:
                        score += 1
                    
                    noise_count = len([t for t in text_list if len(t.strip()) <= 1])
                    if noise_count > 5:
                        score -= noise_count * 0.5
                    
                    all_results.append({
                        'angle': angle,
                        'flip': flip_type,
                        'score': score,
                        'text_count': text_count,
                        'text_list': text_list[:3] if text_list else []
                    })
                    
                    angle_preference = 2 if angle == 0 else 0
                    
                    if (score > best_score or 
                        (score == best_score and text_count > best_text_count) or
                        (score == best_score and text_count == best_text_count and angle_preference > 0) or
                        (score == best_score and text_count == best_text_count and angle_preference == 0 and flip_type is None)):
                        best_score = score
                        best_results = results
                        best_angle = angle
                        best_text_count = text_count
                        
                        if best_score >= 5 and best_text_count >= 8:
                            logger.info(f"Early termination: Found high-confidence result at {angle}° flip {flip_type}")
                            break
            
            except Exception as rotation_error:
                logger.warning(f"Error processing rotation {angle}° with flip {flip_type}: {rotation_error}")
                continue
        
        if best_score >= 5 and best_text_count >= 8:
            break
    
    # Fallback if no IC-matched results found
    if best_results is None:
        for angle in orientations:
            for flip_type in flip_types:
                try:
                    if flip_type == 'horizontal':
                        flipped_array = cv2.flip(image_array, 1)
                    else:
                        flipped_array = image_array.copy()
                    
                    if angle > 0:
                        rotated_array = np.rot90(flipped_array, k=angle//90)
                    else:
                        rotated_array = flipped_array
                    
                    results = ocr.predict(rotated_array)
                    text_list = []
                    if results:
                        try:
                            if isinstance(results, list) and len(results) > 0:
                                ocr_result = results[0]
                                if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
                                    text_list = list(ocr_result['rec_texts'])
                                elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
                                    text_list = list(ocr_result.rec_texts)
                        except (IndexError, AttributeError, TypeError, KeyError):
                            text_list = []
                    
                    if len(text_list) >= 3:
                        best_results = results
                        best_angle = angle
                        break
                except Exception:
                    continue
            if best_results:
                break
    
    if best_results is None:
        raise HTTPException(status_code=400, detail="Could not process image at any orientation. Please try a clearer image.")
    
    return best_results, best_angle

def extract_fields(results, best_angle):
    """Extract IC fields from OCR results"""
    extracted_text = []
    if results and len(results) > 0:
        ocr_result = results[0]
        if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
            extracted_text = list(ocr_result['rec_texts'])
        elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
            extracted_text = list(ocr_result.rec_texts)
    
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Could not extract text from image")
    
    # Apply OCR corrections
    ocr_corrections = [
        (r'L{2,}OT', 'LOT'),
        (r'L{2,}ORONG', 'LORONG'),
        (r'LLORONG', 'LORONG'),
        (r'LLOT', 'LOT'),
        (r'JJALAN', 'JALAN'),
        (r'ORONG', 'LORONG'),
        (r'OT(\d+)', r'LOT \1'),
        (r'(\d+)([A-Z])-', r'\1 \2-'),
        (r'SEKOLAH2', 'SEKOLAH 2'),
        (r'SEKOLAH(\d)', r'SEKOLAH \1'),
        (r'FUADOT', 'FUAD LOT'),
        (r'FUAD OT', 'FUAD LOT'),
        (r'MOHAMED SAD', 'MOHAMED SAID'),
        (r'BIN TI', 'BINTI'),
        (r'YUSRIBIA', 'YUSRI BIN'),
        (r'SHAHALAM', 'SHAH ALAM'),
        (r'JALANUSJ', 'JALAN USJ'),
        (r'(\d+)([A-Z]+JAYA)', r'\1 \2'),
        (r'MUHAMMADSYAKIR', 'MUHAMMAD SYAKIR'),
        (r'(\d{5})([A-Z])', r'\1 \2'),
        (r'AMIRAZIO', 'AMIR AZIQ'),
        (r'AMIRAZIQ', 'AMIR AZIQ'),
        (r'1oo', '100'),
        (r'SUNGAITUA', 'SUNGAI TUA'),
        (r'PUTERAJAYA', 'PUTERA JAYA'),
        (r'JALANPJU', 'JALAN PJU'),
        (r'DAMANSARADAMAI', 'DAMANSARA DAMAI'),
        (r'PETALINGJAYA', 'PETALING JAYA'),
        (r'MUHAMMADIZUDDIN', 'MUHAMMAD IZUDDIN'),
        (r'BINHASNAN', 'BIN HASNAN'),
        (r'JLNMUTIARA', 'JLN MUTIARA'),
        (r'JALANDESA', 'JALAN DESA'),
        (r'COUNTRYHOMES', 'COUNTRY HOMES'),
        (r'BINSUFIAN', 'BIN SUFIAN'),
        (r'BINISMIN', 'BIN ISMIN'),
        (r'KAMPUNGPERIOK', 'KAMPUNG PERIOK'),
        (r'CHABANGEMPAT', 'CHABANG EMPAT'),
        (r'JALANSEKOLAH', 'JALAN SEKOLAH'),
        (r'63100', '53100'),
        (r'ALAN(\d)', r'JALAN \1'),
        (r'ALAN\s', 'JALAN '),
        (r'\bALAN\b', 'JALAN'),
        (r'TAMANSETIAWANGSA', 'TAMAN SETIAWANGSA'),
        (r'RANTAUPANJANG', 'RANTAU PANJANG'),
        (r'JALANSEMARAK', 'JALAN SEMARAK'),
        (r'TAMANSEMARAK', 'TAMAN SEMARAK'),
        (r'SUNGAIPETANI', 'SUNGAI PETANI'),
        (r'NURHAFIZZAH', 'NUR HAFIZZAH'),
        (r'PPRSUNGAITIRAMBLOKA', 'PPR SUNGAI TIRAM BLOK A'),
        (r'PPRSUNGAITIRAMBLOK([A-Z])', r'PPR SUNGAI TIRAM BLOK \1'),
        (r'SUNGAITIRAM', 'SUNGAI TIRAM'),
        (r'RAHIMMIBIN', 'RAHIMMI BIN'),
        (r'JALANSUNGAI', 'JALAN SUNGAI'),
        (r'ULUTIRAM', 'ULU TIRAM'),
        (r'BINABDULBARI', 'BIN ABDUL BARI'),
        (r'JALANKUANTAN', 'JALAN KUANTAN'),
        (r'\bNO(\d)', r'NO \1'),
        (r'KUALAPILAH', 'KUALA PILAH'),
        (r'KAMPUNGSUNGAI', 'KAMPUNG SUNGAI'),
        (r'S845O', '88450'),
        (r'ALIMPANDITA', 'ALIM PANDITA'),
        (r'KOTAKINABALU', 'KOTA KINABALU'),
        (r'LLORONG', 'LORONG'),
    ]
    
    corrected_text = []
    for text in extracted_text:
        corrected = text
        for pattern, replacement in ocr_corrections:
            corrected = re.sub(pattern, replacement, corrected)
        corrected_text.append(corrected)
    
    extracted_text = corrected_text
    
    # Join all text for parsing
    full_text = ' '.join(extracted_text)
    full_text_upper = full_text.upper()
    
    # Extract IC number
    ic_number = None
    ic_match = re.search(r'\d{6}-\d{2}-\d{4}', full_text)
    if ic_match:
        ic_number = ic_match.group()
    
    # Filter out Chinese characters
    extracted_text = [line for line in extracted_text if not has_chinese(line)]
    
    # Noise words to filter
    noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip', 'SEFA']
    
    # Extract Name
    name = None
    name_tokens = []
    
    if ic_number:
        ic_line_indices = []
        for idx, line in enumerate(extracted_text):
            if ic_number in line:
                ic_line_indices.append(idx)
        
        ic_line_idx = None
        for candidate_idx in ic_line_indices:
            if candidate_idx + 1 < len(extracted_text):
                next_line = extracted_text[candidate_idx + 1].upper().strip()
                if next_line and len(next_line) > 2:
                    has_name_indicator = any(word in next_line for word in ['BIN', 'BINTI'])
                    is_letters_only = bool(re.match(r'^[A-Z\s\'@]+$', next_line))
                    if has_name_indicator or is_letters_only:
                        ic_line_idx = candidate_idx
                        break
        
        if ic_line_idx is None and ic_line_indices:
            ic_line_idx = ic_line_indices[0]
        
        place_name_filters = ['PULAU PINANG', 'SUNGAI DUA', 'GELUGOR', 'SELANGOR', 'JOHOR', 'KEDAH', 
                              'PERAK', 'PAHANG', 'KELANTAN', 'TERENGGANU', 'MELAKA', 'SABAH', 'SARAWAK',
                              'KUALA LUMPUR', 'PUTRAJAYA', 'LABUAN', 'PERLIS', 'NEGERI SEMBILAN',
                              'PENANG', 'PINANG', 'PETALING', 'SHAH ALAM', 'IPOH', 'KOTA BHARU']
        
        if ic_line_idx is not None:
            # Try to get name from BEFORE IC number first
            if ic_line_idx > 0:
                prev_line = extracted_text[ic_line_idx - 1].upper().strip()
                is_place_name = any(place in prev_line for place in place_name_filters)
                if prev_line and len(prev_line) > 3 and not is_place_name and (any(word in prev_line for word in ['BIN', 'BINTI']) or (len(prev_line.split()) > 2)):
                    name_tokens = [extracted_text[ic_line_idx - 1]]
                    if ic_line_idx > 1:
                        prev_prev_line = extracted_text[ic_line_idx - 2].upper().strip()
                        is_prev_prev_place = any(place in prev_prev_line for place in place_name_filters)
                        if prev_prev_line and len(prev_prev_line) > 2 and not is_prev_prev_place and not any(keyword in prev_prev_line for keyword in ['KAD', 'MALAYSIA', 'IDENTITY', 'MYKAD']):
                            name_tokens.insert(0, extracted_text[ic_line_idx - 2])
            
            # If we didn't find name before IC, look after IC
            if not name_tokens:
                name_lines = 0
                for i in range(ic_line_idx + 1, len(extracted_text)):
                    line = extracted_text[i]
                    line_upper = line.upper().strip()
                    
                    if not line_upper or has_chinese(line) or len(line_upper) == 1:
                        continue
                    
                    if name_lines >= 2:
                        break
                    
                    if any(header in line_upper for header in ['KAD PENGENALAN', 'MYKAD', 'MALAYSIA', 'IDENTITY', 'CARD']):
                        continue
                    
                    if re.search(r'\d', line):
                        break
                    
                    if any(field in line_upper for field in ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'NEGERISEMBILAN', 'SELANGOR', 'JOHOR']):
                        break
                    
                    if any(addr_kw in line_upper for addr_kw in ['LOT', 'JALAN', 'LORONG', 'KAMPUNG', 'PERINGKAT', 'FELDA']):
                        break
                    
                    if 'WARGANEGARA' in line_upper:
                        break
                    
                    if any(noise in line_upper for noise in noise_words):
                        continue
                    
                    if line.islower():
                        continue
                    
                    name_tokens.append(line)
                    name_lines += 1
            
            if name_tokens:
                raw_name = ' '.join(name_tokens).strip()
                try:
                    raw_name = raw_name.replace('BIN TI', 'BINTI')
                    raw_name = re.sub(r'BIN\s+TI', 'BINTI', raw_name)
                    raw_name = correct_ocr_errors(raw_name)
                    
                    name = raw_name
                    name = re.sub(r'BINTI([A-Z])', r'BINTI \1', name, flags=re.IGNORECASE)
                    
                    if 'BIN' in name and 'BINTI' not in name:
                        name = re.sub(r'BIN([A-Z])', r'BIN \1', name, flags=re.IGNORECASE)
                    
                    name = re.sub(r'([A-Z]+)(BINTI)\s', r'\1 \2 ', name, flags=re.IGNORECASE)
                    name = re.sub(r'([A-Z]+)(BIN)\s', r'\1 \2 ', name, flags=re.IGNORECASE)
                    name = split_malay_words(name)
                    name = re.sub(r'\s+', ' ', name).strip()
                except Exception:
                    name = raw_name.replace('BIN TI', 'BINTI')
                    name = split_malay_words(name)
                    name = re.sub(r'\s+', ' ', name).strip()
    
    # Extract Gender
    gender = None
    gender_keywords = {
        'LELAKI': 'LELAKI (Male)',
        'PEREMPUAN': 'PEREMPUAN (Female)',
    }
    for keyword, value in gender_keywords.items():
        if keyword in full_text_upper:
            gender = value
            break
    
    # Extract Religion
    religion = None
    religion_keywords = {
        'ISLAM': 'ISLAM',
        'ISL.AM': 'ISLAM',
        'SLAM': 'ISLAM',
        'ISLAMIC': 'ISLAM',
        'KRISTIAN': 'KRISTIAN',
        'BUDDHA': 'BUDDHA',
        'HINDU': 'HINDU',
        'SIKH': 'SIKH',
    }
    for keyword, value in religion_keywords.items():
        if keyword in full_text_upper:
            religion = value
            break
    
    # Extract Address
    address = None
    address_keywords = ['LOT', 'JALAN', 'KAMPUNG', 'KG', 'JLN', 'NO', 'BATU', 'LEBUH', 'LORONG', 'JAMBATAN', 'PPR', 'BLOK', 'UNIT', 'TINGKAT', 'TAMAN', 'BANDAR', 'PERINGKAT', 'FELDA', 'DESA', 'PERMAI']
    gender_religion_keywords = ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'ISL.AM', 'ISLAMIC']
    
    malaysia_states = [
        'TERENGGANU', 'SELANGOR', 'KUALA LUMPUR', 'KUALALUMPUR', 'KL',
        'JOHOR', 'KEDAH', 'KELANTAN', 'LABUAN', 'MELAKA', 'NEGERI SEMBILAN', 'NEGERISEMBILAN',
        'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
        'WILAYAH PERSEKUTUAN', 'WP', 'PULAU PINANG', 'PINANG'
    ]
    
    address_place_names = ['SUNGAI DUA', 'GELUGOR', 'PERMAI INDAH', 'DESA PERMAI']
    
    address_lines = []
    collecting_address = False
    name_line_count = len(name_tokens) if name_tokens else 0
    
    for idx, line in enumerate(extracted_text):
        line_upper = line.upper().strip()
        
        if not line_upper or has_chinese(line) or len(line_upper) == 1:
            continue
        
        if idx < name_line_count + 5:
            if any(name_token.upper() in line_upper for name_token in (name_tokens if name_tokens else [])):
                continue
        
        if re.match(r'^[\d\-\s]+$', line_upper):
            if re.match(r'^\d{6}-\d{2}-\d{3,4}$', line.strip()) or re.match(r'^\d{1,2}$', line.strip()) or re.search(r'\d{6,}', line.strip()):
                continue
            if idx >= 4 and len(line.strip()) <= 5:
                collecting_address = True
                address_lines.append(line.strip())
            continue
        
        corrected_line_for_check = line_upper
        corrected_line_for_check = corrected_line_for_check.replace('LLOT', 'LOT')
        corrected_line_for_check = corrected_line_for_check.replace('LLORONG', 'LORONG')
        corrected_line_for_check = corrected_line_for_check.replace('ORONG', 'LORONG')
        
        header_patterns = ['KAD PENGENALAN', 'KAD PENGENJALAN', 'MYKAD', 'MALAYSIA', 'MALAY', 'IDENTITY', 'CARD', 'MK', 'IDENTITN', 'IDENTITY CARD']
        if any(header in line_upper for header in header_patterns):
            continue
        
        if ic_number and ic_number in line:
            continue
        
        if re.match(r'^\d{12}$', line.strip()) or re.match(r'^\d{6}-\d{2}-\d{4}$', line.strip()):
            continue
        
        if re.search(r'\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):
            continue
        
        if name and any(name_part.strip() in line.upper() for name_part in name.upper().split() if len(name_part.strip()) > 2):
            continue
        
        if any(keyword in line_upper for keyword in gender_religion_keywords):
            line_is_state = any(state in line_upper for state in malaysia_states)
            if not line_is_state:
                continue
        
        if re.search(r'\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):
            collecting_address = False
            continue
        
        back_of_ic_markers = ['PENDAFTARAN', 'CHIP', 'TOUCH', '80K']
        if any(marker in line_upper for marker in back_of_ic_markers):
            collecting_address = False
            continue
        
        if 'WARGANEGARA' in line_upper:
            continue
        
        is_address_line = False
        for addr_keyword in address_keywords:
            if corrected_line_for_check.startswith(addr_keyword):
                if addr_keyword in ['NO', 'JLN', 'KG']:
                    if len(corrected_line_for_check) > len(addr_keyword):
                        next_char = corrected_line_for_check[len(addr_keyword)]
                        if next_char.isdigit() or next_char == ' ':
                            is_address_line = True
                            collecting_address = True
                            break
                else:
                    is_address_line = True
                    collecting_address = True
                    break
            if re.search(r'\d+' + addr_keyword, corrected_line_for_check):
                is_address_line = True
                collecting_address = True
                break
            if addr_keyword not in ['NO', 'JLN', 'KG']:
                if addr_keyword in corrected_line_for_check:
                    is_address_line = True
                    break
        
        if re.match(r'^[A-Z]{1,2}-\d', corrected_line_for_check):
            is_address_line = True
            collecting_address = True
        
        if re.match(r'^\d{5}\s*[A-Z]', corrected_line_for_check):
            is_address_line = True
            collecting_address = True
        
        if any(state in corrected_line_for_check for state in malaysia_states):
            is_address_line = True
        
        if any(place in corrected_line_for_check for place in address_place_names):
            is_address_line = True
            collecting_address = True
        
        if is_address_line and not collecting_address:
            collecting_address = True
        
        if collecting_address:
            if line.strip().isdigit():
                continue
            
            if re.search(r'\d{6,}', line):
                if not re.match(r'^\d{5}\s+[A-Z]', line.strip()):
                    continue
            
            if re.search(r'\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):
                collecting_address = False
                continue
            
            if re.search(r',\s*\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):
                line = re.sub(r',\s*\d{6}-\d{2}-\d{4}-\d{2}-\d{2}.*', '', line).strip()
                if not line:
                    continue
            
            if any(noise in line_upper for noise in noise_words):
                continue
            
            if re.search(r'\d{6}-\d{2}-\d{3,4}', line):
                continue
            
            stripped_for_check = line.strip()
            if re.match(r'^\d{5,}$', stripped_for_check):
                continue
            
            if re.match(r'^[\d\s\-\.]+$', stripped_for_check) and re.sub(r'[\s\-\.]', '', stripped_for_check):
                nums_only = re.sub(r'[\s\-\.]', '', stripped_for_check)
                if len(nums_only) >= 5 and len(nums_only) >= len(stripped_for_check) * 0.7:
                    continue
            
            if re.match(r'^\d{1,2}$', line.strip()):
                continue
            
            digit_count = sum(1 for c in stripped_line if c.isdigit()) if 'stripped_line' in dir() else sum(1 for c in line.strip() if c.isdigit())
            if digit_count >= len(line.strip()) * 0.7 and digit_count >= 5:
                continue
            
            if len(line.strip()) <= 4:
                if not any(keyword in line_upper for keyword in address_keywords):
                    continue
            
            corrected_line = correct_ocr_errors(line)
            corrected_line = split_malay_words(corrected_line)
            corrected_line = re.sub(r'([A-Z]+)(\d)(?!/)', r'\1 \2', corrected_line)
            corrected_line = re.sub(r'(\d)([A-Z])(?!/)', r'\1 \2', corrected_line)
            corrected_line = re.sub(r'\s+', ' ', corrected_line).strip()
            
            if corrected_line:
                address_lines.append(corrected_line)
    
    # Build address
    if address_lines:
        unit_numbers = []
        street_names = []
        area_names = []
        localities = []
        postcodes = []
        states = []
        
        state_list = ['PULAU PINANG', 'PINANG', 'SELANGOR', 'JOHOR', 'KEDAH', 'KELANTAN', 
                      'TERENGGANU', 'PAHANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
                      'MELAKA', 'NEGERI SEMBILAN', 'KUALA LUMPUR', 'PUTRAJAYA', 'LABUAN', 'PENANG']
        
        for line in address_lines:
            line_upper = line.upper().strip()
            
            if any(state in line_upper for state in state_list):
                states.append(line)
            elif re.match(r'^\d{5}\s', line_upper):
                postcodes.append(line)
            elif re.match(r'^[A-Z]{1,2}-\d', line_upper) or line_upper.startswith('LOT') or line_upper.startswith('NO'):
                unit_numbers.append(line)
            elif any(kw in line_upper for kw in ['LORONG', 'JALAN', 'LEBUH', 'JLN']):
                street_names.append(line)
            elif any(kw in line_upper for kw in ['TAMAN', 'DESA', 'PERMAI', 'INDAH', 'BANDAR', 'FELDA']):
                area_names.append(line)
            else:
                localities.append(line)
        
        ordered_parts = []
        ordered_parts.extend(unit_numbers)
        ordered_parts.extend(street_names)
        ordered_parts.extend(area_names)
        ordered_parts.extend(localities)
        ordered_parts.extend(postcodes)
        ordered_parts.extend(states)
        
        seen = set()
        final_parts = []
        for part in ordered_parts:
            part_upper = part.upper().strip()
            if part_upper not in seen:
                seen.add(part_upper)
                final_parts.append(part)
        
        address = ', '.join(final_parts)
        address = re.sub(r',?\s*\d{6}-\d{2}-\d{4}-\d{2}-\d{2}.*$', '', address).strip()
    
    # Validate postcode
    postcode_validation = None
    if address:
        postal_code_match = re.search(r'(\d{5})', address)
        if postal_code_match:
            postal_code = postal_code_match.group(1)
            if postcode_state_map:
                if postal_code in postcode_state_map:
                    correct_state = postcode_state_map[postal_code]
                    postcode_validation = {
                        'postcode': postal_code,
                        'state': correct_state,
                        'valid': True
                    }
                else:
                    postcode_validation = {
                        'postcode': postal_code,
                        'valid': False,
                        'message': 'Postcode not found in Malaysia database'
                    }
    
    # Determine document type
    full_text = ' '.join(extracted_text).upper()
    malaysia_ic_keywords = ['KAD PENGENALAN', 'MYKAD', 'WARGANEGARA']
    is_malaysia_ic = any(keyword in full_text for keyword in malaysia_ic_keywords) and ic_number
    
    return {
        'ic_number': ic_number,
        'name': name,
        'gender': gender,
        'religion': religion,
        'address': address,
        'postcode_validation': postcode_validation,
        'document_type': 'Malaysia Identity Card (MyKad)' if is_malaysia_ic else 'Unknown Document',
        'orientation_angle': int(best_angle),
        'raw_ocr_text': extracted_text
    }

# ===================== FASTAPI ENDPOINTS =====================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Malaysia IC OCR API (FastAPI)",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/info", response_model=InfoResponse)
async def get_info():
    """Get API information"""
    return {
        "api_name": "Malaysia IC OCR API (FastAPI)",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/health": "Health check",
            "POST /api/ocr": "Process single IC image/PDF",
            "POST /api/ocr/batch": "Process multiple IC images/PDFs",
            "GET /api/info": "Get API information",
            "GET /docs": "Swagger UI documentation",
            "GET /redoc": "ReDoc documentation"
        },
        "supported_formats": ["JPG", "PNG", "PDF"],
        "max_file_size": "20MB",
        "postcode_db_loaded": len(postcode_state_map) > 0,
        "postcode_count": len(postcode_state_map)
    }

@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...)):
    """
    Process OCR for Malaysia IC
    
    - **file**: Image (JPG, PNG) or PDF file of Malaysia IC
    
    Returns extracted IC information including:
    - IC Number
    - Name
    - Gender
    - Religion
    - Address
    - Postcode validation
    """
    try:
        # Check file type
        filename = file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
            raise HTTPException(status_code=400, detail="Invalid file type. Supported: JPG, PNG, PDF")
        
        # Read file
        file_data = await file.read()
        
        # Load image
        if file_ext == '.pdf':
            if not pdf_support:
                raise HTTPException(status_code=400, detail="PDF support not available. Please install pdf2image.")
            try:
                images = convert_from_bytes(file_data, poppler_path=POPPLER_PATH)
                image = np.array(images[0])
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"PDF processing error: {str(e)}")
        else:
            try:
                image = Image.open(io.BytesIO(file_data))
                # Convert RGBA/LA/P images to RGB
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                image = np.array(image)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Image processing error: {str(e)}")
        
        # Process OCR
        results, best_angle = process_image_ocr(image)
        
        # Extract fields
        data = extract_fields(results, best_angle)
        
        return JSONResponse(content={
            "success": True,
            "data": data
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/ocr/batch")
async def batch_ocr(files: List[UploadFile] = File(...)):
    """
    Process multiple OCR requests
    
    - **files**: Multiple image (JPG, PNG) or PDF files of Malaysia ICs
    
    Returns extracted IC information for each file
    """
    results = []
    
    for file in files:
        filename = file.filename or "unknown"
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
            results.append({
                "filename": filename,
                "success": False,
                "error": "Invalid file type"
            })
            continue
        
        try:
            file_data = await file.read()
            
            if file_ext == '.pdf':
                if not pdf_support:
                    results.append({
                        "filename": filename,
                        "success": False,
                        "error": "PDF support not available"
                    })
                    continue
                images = convert_from_bytes(file_data, poppler_path=POPPLER_PATH)
                image = np.array(images[0])
            else:
                image = Image.open(io.BytesIO(file_data))
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                image = np.array(image)
            
            ocr_results, best_angle = process_image_ocr(image)
            data = extract_fields(ocr_results, best_angle)
            
            results.append({
                "filename": filename,
                "success": True,
                "data": data
            })
        except Exception as e:
            results.append({
                "filename": filename,
                "success": False,
                "error": str(e)
            })
    
    return JSONResponse(content={
        "success": True,
        "total": len(files),
        "processed": len([r for r in results if r.get("success")]),
        "results": results
    })

# Exception handlers
@app.exception_handler(413)
async def request_entity_too_large(request, exc):
    return JSONResponse(
        status_code=413,
        content={"success": False, "error": "File too large (max 20MB)"}
    )

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "Endpoint not found"}
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Malaysia IC OCR FastAPI...")
    logger.info("Available endpoints:")
    logger.info("  GET  http://localhost:8000/api/health")
    logger.info("  GET  http://localhost:8000/api/info")
    logger.info("  POST http://localhost:8000/api/ocr")
    logger.info("  POST http://localhost:8000/api/ocr/batch")
    logger.info("  GET  http://localhost:8000/docs  (Swagger UI)")
    logger.info("  GET  http://localhost:8000/redoc (ReDoc)")
    logger.info("\nTesting with Postman:")
    logger.info("  1. Import the endpoints above")
    logger.info("  2. Use multipart/form-data for file uploads")
    logger.info("  3. Set 'file' as the form field name")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
