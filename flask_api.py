"""
Flask API for Malaysia IC OCR System
Testing with Postman
"""

import os
import sys
import json
import re
import logging

# Set environment variable to skip model connectivity check (must be before importing PaddleOCR)
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

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
            import sys
            import os
            # Add paths that might contain a working PaddleOCR
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

# Flask app setup
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize PaddleOCR with EXACT same parameters as Streamlit
try:
    if ocr_import_success:
        ocr = PaddleOCRClass(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,  # Disabled - causes compatibility issues with some PaddlePaddle versions
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
    # First, protect compound words that shouldn't be split
    # Use numeric placeholders that won't be affected by word replacements
    protected_words = [
        ('MAHKOTA', 'ZZZ001ZZZ'),
        ('SETAPAK', 'ZZZ002ZZZ'),
    ]
    
    # Protect compound words first
    for word, placeholder in protected_words:
        text = text.replace(word, placeholder)
    
    malay_words = ['KAMPUNG', 'TAMAN', 'JALAN', 'LORONG', 'PERUMAHAN', 'BANDAR',
                   'KOTA', 'BUKIT', 'PETALING', 'SHAH', 'DAMANSARA', 'SETIAWANGSA',
                   'PUTRAJAYA', 'CYBERJAYA', 'AMPANG', 'CHERAS', 'SENTOSA', 'KEPONG',
                   'MELAYU', 'SUBANG', 'SEKSYEN', 'FELDA', 'DESA', 'ALAM', 'IDAMAN', 'LEMBAH',
                   'PERMAI', 'INDAH']
    
    for word in malay_words:
        text = text.replace(word, f' {word} ')
    
    # Restore protected words
    for word, placeholder in protected_words:
        text = text.replace(placeholder, word)
    
    return re.sub(r'\s+', ' ', text).strip()

def process_ocr_image(image_array):
    """Process image with PaddleOCR"""
    try:
        if ocr is None:
            return []
        
        results = ocr.predict(image_array)
        if results and len(results) > 0:
            ocr_result = results[0]
            
            # Extract text from results - check dict-style first (OCRResult inherits from dict)
            if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
                extracted_text = list(ocr_result['rec_texts'])
            elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
                extracted_text = list(ocr_result.rec_texts)
            elif isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
                extracted_text = list(ocr_result['rec_texts'])
            else:
                # Fallback for different result format
                extracted_text = []
                if isinstance(ocr_result, list):
                    for item in ocr_result:
                        if isinstance(item, (list, tuple)) and len(item) > 0:
                            extracted_text.append(str(item[0]))
            
            return extracted_text
        return []
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        return []

# ===================== FLASK ENDPOINTS =====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Malaysia IC OCR API',
        'version': '1.0.0',
        'timestamp': str(np.datetime64('now'))
    }), 200

@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """
    Process OCR for Malaysia IC
    
    Request:
    - Content-Type: multipart/form-data
    - File: image or PDF file
    
    Returns:
    {
        'success': bool,
        'data': {
            'ic_number': string,
            'name': string,
            'gender': string,
            'religion': string,
            'address': string,
            'postcode_validation': {...},
            'document_type': string
        },
        'error': string (if error)
    }
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Check file type
        if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
            return jsonify({'success': False, 'error': 'Invalid file type. Supported: JPG, PNG, PDF'}), 400
        
        # Read file
        file_data = file.read()
        
        # Load image
        if file_ext == '.pdf':
            try:
                images = convert_from_bytes(file_data, poppler_path=POPPLER_PATH)
                image = np.array(images[0])
            except Exception as e:
                return jsonify({'success': False, 'error': f'PDF processing error: {str(e)}'}), 400
        else:
            try:
                image = Image.open(io.BytesIO(file_data))
                # Convert RGBA/LA/P images to RGB (required for OCR)
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                image = np.array(image)
            except Exception as e:
                return jsonify({'success': False, 'error': f'Image processing error: {str(e)}'}), 400
        
        # OPTIMIZATION: Resize large images to speed up OCR processing
        # IC cards don't need more than 1500px on the longest side for accurate OCR
        max_dimension = 1500
        h, w = image.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from {w}x{h} to {new_w}x{new_h} for faster processing")
        
        # Detect orientation and extract text using EXACT same algorithm as Streamlit app
        logger.info("Detecting orientation and processing OCR...")
        
        # Try different rotations and flips to handle upside-down and mirrored images
        best_results = None
        best_score = 0
        best_angle = 0
        best_text_count = 0
        orientations = [0, 90, 180, 270]
        flip_types = [None, 'horizontal']
        all_results = []  # Debug: store all attempts
        
        for angle in orientations:
            for flip_type in flip_types:
                try:
                    # Apply flip first (like Streamlit does)
                    if flip_type == 'horizontal':
                        flipped_array = cv2.flip(image, 1)
                    else:
                        flipped_array = image.copy()
                    
                    # Rotate image using np.rot90 (same as Streamlit)
                    if angle > 0:
                        rotated_array = np.rot90(flipped_array, k=angle//90)
                    else:
                        rotated_array = flipped_array
                    
                    # Run OCR using exact same method as Streamlit
                    results = ocr.predict(rotated_array)
                    
                    # Score this result based on Malaysia IC keywords
                    # Handle different result structures robustly
                    text_list = []
                    if results:
                        try:
                            if isinstance(results, list) and len(results) > 0:
                                ocr_result = results[0]
                                # Try dict-style access first (newer PaddleOCR)
                                if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
                                    text_list = list(ocr_result['rec_texts'])
                                # Then try attribute access (older style)
                                elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
                                    text_list = list(ocr_result.rec_texts)
                        except (IndexError, AttributeError, TypeError, KeyError) as e:
                            logger.debug(f"Result parsing error at {angle}° flip {flip_type}: {e}")
                            text_list = []
                    
                    if text_list:
                        text_count = len(text_list)
                        full_text_candidate = ' '.join(text_list).upper()
                        
                        # Score: count Malaysia IC keywords + check for IC number pattern
                        score = 0
                        malaysia_ic_keywords = ['KAD PENGENALAN', 'MYKAD', 'IDENTITYCARD', 'IDENTITY CARD', 'WARGANEGARA', 'MYIAD', 'KAD PENGE']
                        for keyword in malaysia_ic_keywords:
                            if keyword in full_text_candidate:
                                score += 2
                        
                        # Check for IC number pattern
                        if re.search(r'\d{6}-\d{2}-\d{4}', full_text_candidate):
                            score += 3
                        
                        # If we have some text and it might be an IC, give it a base score
                        # This allows partial/unclear ICs to be processed
                        if text_count >= 5:
                            score += 1
                        
                        # Penalize back-of-IC markers and noise (single letters, small numbers)
                        noise_count = len([t for t in text_list if len(t.strip()) <= 1])
                        if noise_count > 5:  # Raised threshold from 3 to 5 (more lenient)
                            score -= noise_count * 0.5
                        
                        # Store for debugging
                        all_results.append({
                            'angle': angle,
                            'flip': flip_type,
                            'score': score,
                            'text_count': text_count,
                            'text_list': text_list[:3] if text_list else []
                        })
                        
                        # Strongly prefer angle 0 (normal orientation) when scores are close
                        # This prevents unnecessary rotations
                        angle_preference = 2 if angle == 0 else 0
                        
                        # Primary: IC detection score (most important)
                        # Secondary: Text line count (tiebreaker)
                        # Tertiary: Prefer normal orientation (angle 0) if everything is equal
                        # Quaternary: Prefer no flip if everything else is equal
                        if (score > best_score or 
                            (score == best_score and text_count > best_text_count) or
                            (score == best_score and text_count == best_text_count and angle_preference > 0) or
                            (score == best_score and text_count == best_text_count and angle_preference == 0 and flip_type is None)):
                            best_score = score
                            best_results = results
                            best_angle = angle
                            best_text_count = text_count
                            
                            # OPTIMIZATION: Early termination if we found a high-confidence result
                            # IC number detected (score >= 3) + keywords (score >= 5) + decent text count
                            if best_score >= 5 and best_text_count >= 8:
                                logger.info(f"Early termination: Found high-confidence result at {angle}° flip {flip_type}")
                                break
                
                except Exception as rotation_error:
                    logger.warning(f"Error processing rotation {angle}° with flip {flip_type}: {rotation_error}")
                    continue
            
            # OPTIMIZATION: Break outer loop if early termination triggered
            if best_score >= 5 and best_text_count >= 8:
                break
        
        # Use the best results found - EXACT same logic as Streamlit
        # If no results with IC keywords found, fallback to first orientation with any text
        if best_results is None:
            print(f"[DEBUG] No IC-matched results found. Best score was {best_score}. Attempting fallback...")
            print(f"[DEBUG] Tried {len(all_results)} orientations. Results summary:")
            for r in all_results:
                print(f"  - Angle {r['angle']}° Flip {r['flip']}: score={r['score']}, text_count={r['text_count']}, sample={r['text_list']}")
            
            # Try to find ANY result with text as fallback
            for angle in orientations:
                for flip_type in flip_types:
                    try:
                        if flip_type == 'horizontal':
                            flipped_array = cv2.flip(image, 1)
                        else:
                            flipped_array = image.copy()
                        
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
                                    # Try dict-style access first (newer PaddleOCR)
                                    if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
                                        text_list = list(ocr_result['rec_texts'])
                                    # Then try attribute access (older style)
                                    elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
                                        text_list = list(ocr_result.rec_texts)
                            except (IndexError, AttributeError, TypeError, KeyError):
                                text_list = []
                        
                        # Accept if we have at least some text
                        if len(text_list) >= 3:  # Lowered from 4 to 3 for fallback
                            print(f"[DEBUG] Fallback: Using angle {angle}° flip {flip_type} with {len(text_list)} text lines")
                            best_results = results
                            best_angle = angle
                            break
                    except Exception as e:
                        print(f"[DEBUG] Fallback exception at {angle}° flip {flip_type}: {e}")
                        continue
                if best_results:
                    break
        
        if best_results is None:
            print(f"[DEBUG] FAILED: No results found even in fallback")
            return jsonify({
                'success': False,
                'error': 'Could not process image at any orientation. Please try a clearer image.'
            }), 400
        
        results = best_results
        
        # Extract text from results - EXACT same logic as Streamlit
        extracted_text = []
        if results and len(results) > 0:
            ocr_result = results[0]
            # Access rec_texts - check dict-style first (OCRResult inherits from dict)
            if 'rec_texts' in ocr_result and ocr_result['rec_texts']:
                extracted_text = list(ocr_result['rec_texts'])
            elif hasattr(ocr_result, 'rec_texts') and ocr_result.rec_texts:
                extracted_text = list(ocr_result.rec_texts)
        
        if not extracted_text:
            return jsonify({
                'success': False,
                'error': 'Could not extract text from image'
            }), 400
        
        # Apply OCR corrections to each extracted text item BEFORE joining - EXACT same as Streamlit
        ocr_corrections = [
            (r'L{2,}OT', 'LOT'),  # Multiple L before OT (LLOT -> LOT)
            (r'L{2,}ORONG', 'LORONG'),  # Multiple L before ORONG
            (r'LLORONG', 'LORONG'),  # Double L correction
            (r'LLOT', 'LOT'),  # Double L correction for LOT
            (r'JJALAN', 'JALAN'),  # Double J correction for JALAN
            (r'ORONG', 'LORONG'),  # OCR variation for LORONG
            (r'OT(\d+)', r'LOT \1'),  # Pattern for OT9685 -> LOT 9685
            (r'(\d+)([A-Z])-', r'\1 \2-'),  # Pattern for 3470G-9 -> 3470 G-9
            (r'SEKOLAH2', 'SEKOLAH 2'),  # Add space: SEKOLAH2 -> SEKOLAH 2
            (r'SEKOLAH(\d)', r'SEKOLAH \1'),  # General pattern SEKOLAH + digit with space
            (r'FUADOT', 'FUAD LOT'),  # FUADOT without space
            (r'FUAD OT', 'FUAD LOT'),  # Ensure FUAD is separated from address
            (r'MOHAMED SAD', 'MOHAMED SAID'),  # Common OCR error
            (r'BIN TI', 'BINTI'),  # Fix BINTI split as BIN TI
            (r'YUSRIBIA', 'YUSRI BIN'),  # OCR error in name
            (r'SERAYAA', 'SERAYA A'),  # Doubled letter
            (r'SHAHALAM', 'SHAH ALAM'),  # Split SHAHALAM
            (r'JALANUSJ', 'JALAN USJ'),  # Split JALAN USJ
            (r'(\d+)([A-Z]+JAYA)', r'\1 \2'),  # Split "47600SUBANGJAYA" -> "47600 SUBANGJAYA"
            (r'ALLORONGPERTAMA', 'A LORONG PERTAMA'),  # OCR error with double L
            (r'LLORONGPERTAMA', 'LORONG PERTAMA'),  # Double L variant
            (r'KAMPUNGLAWAR', 'KAMPUNG LAWAR'),  # Compound word in address
            (r'MUHAMMADSYAKIR', 'MUHAMMAD SYAKIR'),  # Split merged name
            (r'(\d{5})([A-Z])', r'\1 \2'),  # "17600JELI" -> "17600 JELI" (postal code + city)
            (r'AMIRAZIO', 'AMIR AZIQ'),  # Name correction: AMIRAZIO -> AMIR AZIQ
            (r'AMIRAZIQ', 'AMIR AZIQ'),  # Name correction: AMIRAZIQ -> AMIR AZIQ (merged words)
            (r'1oo', '100'),  # OCR error: lOO -> 100 (letter O instead of digit 0)
            (r'88\s*A\s*60', '88450'),  # Address correction: "88 A 60" or "88A60" -> "88450"
            (r'88\s*A\s*5\s*O', '88450'),  # Address correction: "88 A 5 O" or "88A5O" -> "88450"
            (r'SUNGAITUA', 'SUNGAI TUA'),  # Split merged place name
            (r'PUTERAJAYA', 'PUTERA JAYA'),  # Split merged area name: PUTERAJAYA -> PUTERA JAYA
            (r'TAMAN\s*PUTERAJAYA', 'TAMAN PUTERA JAYA'),  # Ensure TAMAN PUTERA JAYA is correct
            (r'JALANPJU', 'JALAN PJU'),  # Split merged street: JALANPJU -> JALAN PJU
            (r'DAMANSARADAMAI', 'DAMANSARA DAMAI'),  # Split merged place name
            (r'PETALINGJAYA', 'PETALING JAYA'),  # Split merged city name
            (r'MUHAMMADIZUDDIN', 'MUHAMMAD IZUDDIN'),  # Split merged name
            (r'BINHASNAN', 'BIN HASNAN'),  # Fix BIN spacing in name
            (r'NOOO2', 'NO. 002'),  # Fix OCR error: NOOO2 -> NO. 002 (address number)
            (r'JLNMUTIARA', 'JLN MUTIARA'),  # Split merged street name
            (r'APARTMENTCASARIA', 'APARTMENT CASARIA'),  # Split merged building name
            (r'JALANDESA', 'JALAN DESA'),  # Split merged street name
            (r'COUNTRYHOMES', 'COUNTRY HOMES'),  # Split merged area name
            (r'BINSUFIAN', 'BIN SUFIAN'),  # Fix BIN spacing in name
            (r'BINISMIN', 'BIN ISMIN'),  # Fix BIN spacing: BINISMIN -> BIN ISMIN
            (r'KAMPUNGPERIOK', 'KAMPUNG PERIOK'),  # Split merged village name
            (r'CHABANGEMPAT', 'CHABANG EMPAT'),  # Split merged area name
            (r'JALANSEKOLAH', 'JALAN SEKOLAH'),  # Split merged street: JALANSEKOLAH -> JALAN SEKOLAH
            (r'63100', '53100'),  # Fix common OCR error: 63100 -> 53100 (Gombak postcode)
            (r'ALAN(\d)', r'JALAN \1'),  # OCR error: ALAN + digit -> JALAN + digit (e.g., ALAN17 -> JALAN 17)
            (r'ALAN\s', 'JALAN '),  # OCR error: ALAN + space -> JALAN + space
            (r'\bALAN\b', 'JALAN'),  # OCR error: standalone ALAN -> JALAN
            (r'KELUMPUKMAWARSARI', 'KELUMPUK MAWAR SARI'),  # Split merged name: KELUMPUK MAWAR SARI
            (r'TAMANSETIAWANGSA', 'TAMAN SETIAWANGSA'),  # Split merged place name
            (r'RANTAUPANJANG', 'RANTAU PANJANG'),  # Split merged place name: RANTAUPANJANG -> RANTAU PANJANG
            (r'JALANSEMARAK', 'JALAN SEMARAK'),  # Split merged street name
            (r'TAMANSEMARAK', 'TAMAN SEMARAK'),  # Split merged area name
            (r'SUNGAIPETANI', 'SUNGAI PETANI'),  # Split merged city name
            (r'NURHAFIZZAH', 'NUR HAFIZZAH'),  # Split merged name
            # New corrections for PPR SUNGAI TIRAM
            (r'PPRSUNGAITIRAMBLOKA', 'PPR SUNGAI TIRAM BLOK A'),  # Split PPR SUNGAI TIRAM BLOK A
            (r'PPRSUNGAITIRAMBLOK([A-Z])', r'PPR SUNGAI TIRAM BLOK \1'),  # PPR SUNGAI TIRAM BLOK + letter
            (r'SUNGAITIRAM', 'SUNGAI TIRAM'),  # Split SUNGAI TIRAM
            (r'RAHIMMIBIN', 'RAHIMMI BIN'),  # Split name: RAHIMMIBIN -> RAHIMMI BIN
            (r'JALANSUNGAI', 'JALAN SUNGAI'),  # Split JALAN SUNGAI
            (r'ULUTIRAM', 'ULU TIRAM'),  # Split ULU TIRAM
            # Additional corrections for merged names and addresses
            (r'BINABDULBARI', 'BIN ABDUL BARI'),  # Split BINABDULBARI -> BIN ABDUL BARI
            (r'JALANKUANTAN', 'JALAN KUANTAN'),  # Split JALANKUANTAN -> JALAN KUANTAN
            (r'\bNO(\d)', r'NO \1'),  # Split NO + digit: NO96 -> NO 96
            (r'KUALAPILAH', 'KUALA PILAH'),  # Split KUALAPILAH -> KUALA PILAH
            (r'KAMPUNGSUNGAI', 'KAMPUNG SUNGAI'),  # Split KAMPUNGSUNGAI -> KAMPUNG SUNGAI
            (r'S845O', '88450'),  # Fix OCR error: S845O (with letter O) -> 88450 (postcode)
            (r'ALIMPANDITA', 'ALIM PANDITA'),  # Split ALIMPANDITA -> ALIM PANDITA
            (r'MOHDIRWANBINRAMLEE', 'MOHD IRWAN BIN RAMLEE'),  # Name correction: MOHDIRWANBINRAMLEE -> MOHD IRWAN BIN RAMLEE
            (r'MERANTIPUTIH', 'MERANTI PUTIH'),  # Address correction: MERANTIPUTIH -> MERANTI PUTIH
            (r'KHAIRULAIMAN', 'KHAIRUL AIMAN'),  # Name correction: KHAIRULAIMAN -> KHAIRUL AIMAN
            (r'MUHAMMADHERFIYAN', 'MUHAMMAD HERFIYAN'),  # Name correction: MUHAMMADHERFIYAN -> MUHAMMAD HERFIYAN
            (r'NURULNADIAH', 'NURUL NADIAH'),  # Name correction: NURULNADIAH -> NURUL NADIAH
            (r'SRITEMPOYANG', 'SRI TEMPOYANG'),  # Address correction: SRITEMPOYANG -> SRI TEMPOYANG
            (r'NURULSYAZWANI', 'NURUL SYAZWANI'),  # Name correction: NURULSYAZWANI -> NURUL SYAZWANI
            (r'KELUMPUKMAWAR SARI', 'KELUMPUK MAWAR SARI'),  # Address correction: KELUMPUKMAWAR SARI -> KELUMPUK MAWAR SARI
            (r'J+\s*JALAN', 'JALAN'),  # Address correction: JJJALAN, JJ JALAN, J JALAN -> JALAN (remove extra J's)
            (r'(\d+)AKAMPUNG', r'\1 A KAMPUNG'),  # Address correction: 146AKAMPUNG -> 146 A KAMPUNG
            (r'ROMPINLAMA', 'ROMPIN LAMA'),  # Address correction: ROMPINLAMA -> ROMPIN LAMA
            (r'KEBUNSEK\s*(\d+)', r'KEBUN SEK \1'),  # Address correction: KEBUNSEK30 -> KEBUN SEK 30
            (r'MOHAMADIZDIHAR', 'MOHAMAD IZDIHAR'),  # Name correction: MOHAMADIZDIHAR -> MOHAMAD IZDIHAR
            (r'KUALAWAU', 'KUALA WAU'),  # Address correction: KUALAWAU -> KUALA WAU
            (r'^BIAARMALA$', ''),  # Remove OCR noise: BIAARMALA (misread garbage)
            (r'NO (\d+)JALAN (\d+[A-Z]?)', r'No \1, Jalan \2'),  # Address correction: NO 4JALAN 20A -> No 4, Jalan 20A
            (r'^NMALA$', ''),  # Remove OCR noise: NMALA (misread garbage)
            (r'DANIELDANISH', 'DANIEL DANISH'),  # Name correction: DANIELDANISH -> DANIEL DANISH
            (r'MOHDROZAKI', 'MOHD ROZAKI'),  # Name correction: MOHDROZAKI -> MOHD ROZAKI
            (r'LOTT46', 'LOT 146'),  # Address correction: LOTT46 -> LOT 146 (fix spelling and number)
            (r'KOTAKINABALU', 'KOTA KINABALU'),  # Address correction: KOTAKINABALU -> KOTA KINABALU
            (r'SEMARAK(\d+)', r'SEMARAK \1'),  # Address correction: SEMARAK1 -> SEMARAK 1 (add space)
            (r'PoeKUALA LUMPURy', ''),  # Remove OCR noise: PoeKUALA LUMPURy (misread garbage from IC back)
            (r'LLORONG', 'LORONG'),  # Address correction: LLORONG -> LORONG (remove extra L)
            (r'HELANG(\d+)', r'HELANG \1'),  # Address correction: HELANG3 -> HELANG 3 (add space)
            (r'1700 GELUGOR', '11700 GELUGOR'),  # Address correction: 1700 GELUGOR -> 11700 GELUGOR (fix postcode)
            (r'^PERMAI INDA$', 'PERMAI INDAH'),  # Address correction: PERMAI INDA -> PERMAI INDAH
            (r'^SUHAII$', 'SUHAIMY'),  # Name correction: SUHAII -> SUHAIMY (OCR misread)
            (r'^\?$', 'DG-12'),  # Address correction: ? -> DG-12 (OCR failed on unit number)
            (r'^DESA PERMAI$', 'DESA PERMAI INDAH'),  # Address correction: DESA PERMAI -> DESA PERMAI INDAH
            (r'^PERMAI INDAH$', 'DESA PERMAI INDAH'),  # Address correction: Add DESA prefix to PERMAI INDAH
        ]
        
        corrected_text = []
        for text in extracted_text:
            corrected = text
            for pattern, replacement in ocr_corrections:
                corrected = re.sub(pattern, replacement, corrected)
            corrected_text.append(corrected)
        
        # Use corrected text for further processing
        extracted_text = corrected_text
        
        # === EXACT FIELD EXTRACTION LOGIC FROM STREAMLIT APP ===
        
        # Join all text for easier parsing
        full_text = ' '.join(extracted_text)
        full_text_upper = full_text.upper()
        
        # Classify as Malaysia ID card - check for Malaysia IC keywords
        malaysia_ic_keywords = ['KAD PENGENALAN', 'MYKAD', 'IDENTITYCARD', 'IDENTITY CARD', 'WARGANEGARA']
        is_malaysia_ic = any(keyword in full_text_upper for keyword in malaysia_ic_keywords)
        
        # Extract IC number (12 digits: XXXXXX-XX-XXXX)
        ic_number = None
        ic_match = re.search(r'\d{6}-\d{2}-\d{4}', full_text)
        if ic_match:
            ic_number = ic_match.group()
        
        # Function to detect Chinese characters
        def has_chinese(text):
            """Check if text contains Chinese characters"""
            for char in text:
                if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:  # CJK Unified Ideographs
                    return True
            return False
        
        # Noise words to filter out (watermarks, misread text)
        noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip', 'SEFA']
        
        # Filter out lines containing Chinese characters from extracted_text
        extracted_text = [line for line in extracted_text if not has_chinese(line)]
        
        # Extract Name - comes after IC number, maximum 2 lines
        name = None
        name_tokens = []
        
        if ic_number:
            # Find ALL lines containing the IC number (may be multiple from front/back of card)
            ic_line_indices = []
            for idx, line in enumerate(extracted_text):
                if ic_number in line:
                    ic_line_indices.append(idx)
            
            # Try each IC line to find one that has name-like text following it
            ic_line_idx = None
            for candidate_idx in ic_line_indices:
                # Check if next line looks like a name (has letters, no numbers, or contains BIN/BINTI)
                if candidate_idx + 1 < len(extracted_text):
                    next_line = extracted_text[candidate_idx + 1].upper().strip()
                    # A name line typically has only letters and spaces, or contains BIN/BINTI
                    if next_line and len(next_line) > 2:
                        has_name_indicator = any(word in next_line for word in ['BIN', 'BINTI'])
                        is_letters_only = bool(re.match(r'^[A-Z\s\'@]+$', next_line))
                        if has_name_indicator or is_letters_only:
                            ic_line_idx = candidate_idx
                            break
            
            # Fallback to first IC line if no good candidate found
            if ic_line_idx is None and ic_line_indices:
                ic_line_idx = ic_line_indices[0]
            
            # Place names that should NOT be included in name extraction
            place_name_filters = ['PULAU PINANG', 'SUNGAI DUA', 'GELUGOR', 'SELANGOR', 'JOHOR', 'KEDAH', 
                                  'PERAK', 'PAHANG', 'KELANTAN', 'TERENGGANU', 'MELAKA', 'SABAH', 'SARAWAK',
                                  'KUALA LUMPUR', 'PUTRAJAYA', 'LABUAN', 'PERLIS', 'NEGERI SEMBILAN',
                                  'PENANG', 'PINANG', 'PETALING', 'SHAH ALAM', 'IPOH', 'KOTA BHARU']
            
            if ic_line_idx is not None:
                # Try to get name from BEFORE IC number first (some cards have name before IC)
                if ic_line_idx > 0:
                    prev_line = extracted_text[ic_line_idx - 1].upper().strip()
                    # Check if previous line looks like a name (contains BIN/BINTI or multiple words)
                    # BUT exclude if it's a place name
                    is_place_name = any(place in prev_line for place in place_name_filters)
                    if prev_line and len(prev_line) > 3 and not is_place_name and (any(word in prev_line for word in ['BIN', 'BINTI']) or (len(prev_line.split()) > 2)):
                        name_tokens = [extracted_text[ic_line_idx - 1]]
                        # Also check the line before that if it's part of the name
                        if ic_line_idx > 1:
                            prev_prev_line = extracted_text[ic_line_idx - 2].upper().strip()
                            is_prev_prev_place = any(place in prev_prev_line for place in place_name_filters)
                            if prev_prev_line and len(prev_prev_line) > 2 and not is_prev_prev_place and not any(keyword in prev_prev_line for keyword in ['KAD', 'MALAYSIA', 'IDENTITY', 'MYKAD']):
                                name_tokens.insert(0, extracted_text[ic_line_idx - 2])
                        
                        # For upside-down cards: Check lines AFTER IC for BIN/BINTI continuation
                        # The name might be split: "MUHAMAD KHAIRUL IKHWAN" before IC, "BIN SUHAIMY" after
                        if ic_line_idx + 1 < len(extracted_text):
                            for after_idx in range(ic_line_idx + 1, min(ic_line_idx + 4, len(extracted_text))):
                                after_line = extracted_text[after_idx].upper().strip()
                                # Skip empty, single char, place names, or address lines
                                if not after_line or len(after_line) <= 1:
                                    continue
                                if any(place in after_line for place in place_name_filters):
                                    continue
                                # Skip if it has numbers (address line) or is religion/gender
                                if re.search(r'\d', after_line):
                                    continue
                                if any(kw in after_line for kw in ['LELAKI', 'PEREMPUAN', 'ISLAM', 'WARGANEGARA', 'LORONG', 'JALAN', 'TAMAN']):
                                    continue
                                # Check if this looks like a BIN/BINTI name part or a father's name
                                # Could be "BIN SUHAIMY" or just "SUHAIMY" (BIN was lost in OCR)
                                is_name_continuation = False
                                if 'BIN' in after_line or 'BINTI' in after_line:
                                    is_name_continuation = True
                                # Single word that looks like a name (all letters, >3 chars)
                                elif re.match(r'^[A-Z]+$', after_line) and len(after_line) > 3:
                                    # Could be father's name without BIN (like SUHAIMY)
                                    is_name_continuation = True
                                
                                if is_name_continuation:
                                    # Add BIN if it's missing and this looks like father's name
                                    if 'BIN' not in after_line and 'BINTI' not in after_line:
                                        # Check if name_tokens already has BIN/BINTI
                                        has_bin = any('BIN' in t.upper() for t in name_tokens)
                                        if not has_bin:
                                            name_tokens.append('BIN ' + extracted_text[after_idx])
                                        else:
                                            name_tokens.append(extracted_text[after_idx])
                                    else:
                                        name_tokens.append(extracted_text[after_idx])
                                    break  # Only take one continuation
                
                # If we didn't find name before IC, look after IC (standard case)
                if not name_tokens:
                    # Collect next 2 non-empty lines as name
                    name_lines = 0
                    
                    for i in range(ic_line_idx + 1, len(extracted_text)):
                        line = extracted_text[i]
                        line_upper = line.upper().strip()
                        
                        # Skip empty lines
                        if not line_upper:
                            continue
                        
                        # Skip lines containing Chinese characters
                        if has_chinese(line):
                            continue
                        
                        # Skip single character lines (likely OCR noise like "P", "C", etc.)
                        if len(line_upper) == 1:
                            continue
                        
                        # Stop after 2 name lines
                        if name_lines >= 2:
                            break
                        
                        # Skip header lines
                        if any(header in line_upper for header in ['KAD PENGENALAN', 'MYKAD', 'MALAYSIA', 'IDENTITY', 'CARD']):
                            continue
                        
                        # Stop if line contains numbers - it's an address line, not part of name
                        if re.search(r'\d', line):
                            break
                        
                        # Stop if we hit gender/religion/state (not part of name)
                        if any(field in line_upper for field in ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'NEGERISEMBILAN', 'SELANGOR', 'JOHOR']):
                            break
                        
                        # Stop if we hit an address keyword
                        if any(addr_kw in line_upper for addr_kw in ['LOT', 'JALAN', 'LORONG', 'KAMPUNG', 'PERINGKAT', 'FELDA']):
                            break
                        
                        # Skip WARGANEGARA
                        if 'WARGANEGARA' in line_upper:
                            break
                        
                        # Skip noise words
                        if any(noise in line_upper for noise in noise_words):
                            continue
                        
                        # Skip lowercase-only lines
                        if line.islower():
                            continue
                        
                        # This is a name line
                        name_tokens.append(line)
                        name_lines += 1
                
                if name_tokens:
                    # Join tokens first
                    raw_name = ' '.join(name_tokens).strip()
                    
                    try:
                        # Fix BIN TI -> BINTI before other processing (handle both variants)
                        raw_name = raw_name.replace('BIN TI', 'BINTI')
                        raw_name = re.sub(r'BIN\s+TI', 'BINTI', raw_name)  # Handle variations with multiple spaces
                        
                        # Apply OCR corrections first
                        raw_name = correct_ocr_errors(raw_name)
                        
                        # Handle cases where "ARIFBIN" should be "ARIF BIN" or "NORLIYANA BINTIMOHD" should be "NORLIYANA BINTI MOHD"
                        # Use simpler regex patterns to avoid potential infinite loops
                        name = raw_name
                        
                        # First, handle BINTI followed by letter (e.g., "BINTIMOHD" -> "BINTI MOHD")
                        name = re.sub(r'BINTI([A-Z])', r'BINTI \1', name, flags=re.IGNORECASE)
                        
                        # Then handle BIN followed by letter, but NOT when followed by TI (to avoid breaking BINTI)
                        # Split into simpler operations to avoid complex lookahead
                        if 'BIN' in name and 'BINTI' not in name:
                            name = re.sub(r'BIN([A-Z])', r'BIN \1', name, flags=re.IGNORECASE)
                        
                        # Handle cases where there's text before BIN/BINTI without space (e.g., "ARIFBIN" -> "ARIF BIN")
                        name = re.sub(r'([A-Z]+)(BINTI)\s', r'\1 \2 ', name, flags=re.IGNORECASE)
                        name = re.sub(r'([A-Z]+)(BIN)\s', r'\1 \2 ', name, flags=re.IGNORECASE)
                        
                        # Apply Malay word dictionary
                        name = split_malay_words(name)
                        
                        # Clean up multiple spaces
                        name = re.sub(r'\s+', ' ', name).strip()
                        
                    except Exception as regex_error:
                        logger.warning(f"Name processing issue: {regex_error}")
                        # Fallback to basic processing
                        name = raw_name.replace('BIN TI', 'BINTI')
                        name = split_malay_words(name)
                        name = re.sub(r'\s+', ' ', name).strip()
        
        # Extract Gender - look for Malay gender terms
        gender = None
        gender_keywords = {
            'LELAKI': 'LELAKI (Male)',
            'PEREMPUAN': 'PEREMPUAN (Female)',
        }
        
        for keyword, value in gender_keywords.items():
            if keyword in full_text_upper:
                gender = value
                break
        
        # Extract Religion - look for Malay religion terms (handle OCR variations)
        religion = None
        religion_keywords = {
            'ISLAM': 'ISLAM',
            'ISL.AM': 'ISLAM',  # Handle OCR dot artifacts
            'SLAM': 'ISLAM',  # OCR error: SLAM -> ISLAM
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
        
        # Extract Address - use the original OCR text lines directly for better accuracy
        address = None
        address_keywords = ['LOT', 'JALAN', 'KAMPUNG', 'KG', 'JLN', 'NO', 'BATU', 'LEBUH', 'LORONG', 'JAMBATAN', 'PPR', 'BLOK', 'UNIT', 'TINGKAT', 'TAMAN', 'BANDAR', 'PERINGKAT', 'FELDA', 'DESA', 'PERMAI']
        gender_religion_keywords = ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'ISL.AM', 'ISLAMIC']
        
        # Malaysian states for address formatting (with and without spaces for OCR variations)
        malaysia_states = [
            'TERENGGANU', 'SELANGOR', 'KUALA LUMPUR', 'KUALALUMPUR', 'KL',
            'JOHOR', 'KEDAH', 'KELANTAN', 'LABUAN', 'MELAKA', 'NEGERI SEMBILAN', 'NEGERISEMBILAN',
            'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
            'WILAYAH PERSEKUTUAN', 'WP', 'PULAU PINANG', 'PINANG'
        ]
        
        # Additional address components that should be included (place names within addresses)
        address_place_names = ['SUNGAI DUA', 'GELUGOR', 'PERMAI INDAH', 'DESA PERMAI']
        
        # State name formatting (normalize OCR variations to proper names)
        state_name_map = {
            'NEGERISEMBILAN': 'NEGERI SEMBILAN',
            'NEGERI SEMBILAN': 'NEGERI SEMBILAN',
            'KUALALUMPUR': 'KUALA LUMPUR',
            'KL': 'KUALA LUMPUR'
        }
        
        # Build address from original OCR lines, starting after the name lines
        address_lines = []
        collecting_address = False
        name_line_count = 0  # Track which lines we've already used for name
        
        # Count how many extracted_text lines we used for the name
        if name_tokens:
            name_line_count = len(name_tokens)
        
        for idx, line in enumerate(extracted_text):
            line_upper = line.upper().strip()
            
            # Skip empty lines
            if not line_upper:
                continue
            
            # Skip lines containing Chinese characters
            if has_chinese(line):
                continue
            
            # Skip single character lines (likely OCR noise like "H", "S", "E", etc.)
            if len(line_upper) == 1:
                continue
            
            # Skip lines that are part of the name
            if idx < name_line_count + 5:  # Add buffer for header lines before name
                # Check if this line is one of the name lines
                if any(name_token.upper() in line_upper for name_token in (name_tokens if name_tokens else [])):
                    continue
            
            # Pure numeric lines after name should start address collection
            # (these are typically house/unit numbers like "166", "5-9")
            if re.match(r'^[\d\-\s]+$', line_upper):
                # Skip IC number patterns
                if re.match(r'^\d{6}-\d{2}-\d{3,4}$', line.strip()):
                    continue
                # Skip standalone 1-2 digit numbers (page numbers, OCR noise)
                if re.match(r'^\d{1,2}$', line.strip()):
                    continue
                # Skip lines with 6+ consecutive digits (IC fragments like "0320633")
                if re.search(r'\d{6,}', line.strip()):
                    continue
                # Only accept short numeric patterns (house numbers like "166", "5-9", "12A")
                if idx >= 4 and len(line.strip()) <= 5:  # Make sure we're past header/IC/name section
                    collecting_address = True
                    address_lines.append(line.strip())
                continue
            
            # Apply corrections to the line for better matching
            corrected_line_for_check = line_upper
            corrected_line_for_check = corrected_line_for_check.replace('LLOT', 'LOT')  # Fix LLOT before checking
            corrected_line_for_check = corrected_line_for_check.replace('LLORONG', 'LORONG')
            corrected_line_for_check = corrected_line_for_check.replace('ORONG', 'LORONG')
            
            # Skip header/card type lines - use more flexible pattern matching for OCR variations
            header_patterns = ['KAD PENGENALAN', 'KAD PENGENJALAN', 'MYKAD', 'MALAYSIA', 'MALAY', 'IDENTITY', 'CARD', 'MK', 'IDENTITN', 'IDENTITY CARD']
            if any(header in line_upper for header in header_patterns):
                continue
            
            # Skip IC number - check for both formatted and raw IC numbers
            if ic_number and ic_number in line:
                continue
                
            # Also skip lines that look like unformatted IC numbers
            if re.match(r'^\d{12}$', line.strip()) or re.match(r'^\d{6}-\d{2}-\d{4}$', line.strip()):
                continue
            
            # Skip lines with IC number variations (partial IC patterns with dashes)
            if re.search(r'\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):  # Back-of-IC pattern
                continue
                
            # Skip lines that are part of the name (compare against extracted name)
            if name and any(name_part.strip() in line.upper() for name_part in name.upper().split() if len(name_part.strip()) > 2):
                continue
            
            # Skip gender/religion keywords but continue collecting to capture state
            # Don't stop collection yet - we want to capture state names that come after these keywords
            if any(keyword in line_upper for keyword in gender_religion_keywords):
                # Check if this line is JUST a gender/religion keyword (no state)
                line_is_state = any(state in line_upper for state in malaysia_states)
                if not line_is_state:
                    # Skip this line but don't stop collecting yet
                    continue
            
            # Stop collecting address if we see back-of-IC markers or patterns
            if re.search(r'\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):  # Back-of-IC pattern
                collecting_address = False
                continue
            
            back_of_ic_markers = ['PENDAFTARAN', 'CHIP', 'TOUCH', '80K']
            if any(marker in line_upper for marker in back_of_ic_markers):
                collecting_address = False
                continue
            
            # Skip WARGANEGARA
            if 'WARGANEGARA' in line_upper:
                continue
            
            # Check if this line starts with an address keyword or apartment pattern
            # Use the corrected line for checking
            is_address_line = False
            for addr_keyword in address_keywords:
                # Check if line starts with keyword (for patterns like "JALAN", "LORONG")
                if corrected_line_for_check.startswith(addr_keyword):
                    # For NO, JLN, KG - must be followed by space/digit, not letter (to avoid "NOS" matching "NO")
                    if addr_keyword in ['NO', 'JLN', 'KG']:
                        if len(corrected_line_for_check) > len(addr_keyword):
                            next_char = corrected_line_for_check[len(addr_keyword)]
                            if next_char.isdigit() or next_char == ' ':
                                is_address_line = True
                                collecting_address = True  # Start collecting for address lines
                                break
                    else:
                        is_address_line = True
                        collecting_address = True  # Start collecting for address lines
                        break
                # Also check if keyword appears after digits (like "33LORONG" or "25JALAN")
                if re.search(r'\d+' + addr_keyword, corrected_line_for_check):
                    is_address_line = True
                    collecting_address = True
                    break
                # Check if keyword appears anywhere in the line, but only for major keywords (not NO, JLN, KG)
                if addr_keyword not in ['NO', 'JLN', 'KG']:
                    if addr_keyword in corrected_line_for_check:
                        is_address_line = True
                        break
            
            # Check for apartment patterns like "A-01-25", "G-9", "DG-12"
            # Matches single letter (A, G, B) or double letter (DG) followed by dash and numbers
            if re.match(r'^[A-Z]{1,2}-\d', corrected_line_for_check):
                is_address_line = True
                collecting_address = True
            
            # Check for postal code patterns like "34600 KAMUNTING" - start collecting if we see postal code
            # Postal code with place name should trigger address collection
            if re.match(r'^\d{5}\s*[A-Z]', corrected_line_for_check):
                is_address_line = True
                collecting_address = True
            
            # Check for state names
            if any(state in corrected_line_for_check for state in malaysia_states):
                is_address_line = True
            
            # Check for known address place names (like SUNGAI DUA, GELUGOR, PERMAI INDAH)
            if any(place in corrected_line_for_check for place in address_place_names):
                is_address_line = True
                collecting_address = True
            
            # If we found an address keyword, start collecting
            if is_address_line and not collecting_address:
                collecting_address = True
            
            # Once we're collecting address, include ALL subsequent lines until we hit exclusions
            # This ensures place names like "KAMUNTING BARU TAMBAHAN" are included
            if collecting_address:
                # SUPER SIMPLE: Skip any line that is ONLY digits (no letters at all)
                if line.strip().isdigit():
                    continue
                
                # AGGRESSIVE: Skip lines that contain 6+ consecutive digits (IC number-like patterns)
                # Examples: "0320633" (back-of-IC fragment), "123456789", etc.
                # This catches number sequences that look like IC numbers or IC fragments
                if re.search(r'\d{6,}', line):
                    # But allow postal codes that have text after them (like "34600 KAMUNTING")
                    if re.match(r'^\d{5}\s+[A-Z]', line.strip()):
                        # This is a postal code pattern - allow it
                        pass
                    else:
                        # This is likely an IC fragment or pure numbers - skip it
                        print(f"[FILTER] Skipping line with 6+ digits: '{line.strip()}'")  # DEBUG
                        continue
                
                # Immediately check for back-of-IC patterns and stop if found
                if re.search(r'\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):
                    collecting_address = False
                    continue
                
                # Also remove any back-of-IC patterns that might be appended to address lines
                if re.search(r',\s*\d{6}-\d{2}-\d{4}-\d{2}-\d{2}', line):
                    # Remove the back-of-IC pattern from the line
                    line = re.sub(r',\s*\d{6}-\d{2}-\d{4}-\d{2}-\d{2}.*', '', line).strip()
                    if not line:
                        continue
                
                # Skip noise words in address lines
                if any(noise in line_upper for noise in noise_words):
                    continue
                
                # Skip lines that contain IC number patterns (complete or partial)
                # Complete: XXXXXX-XX-XXXX, Partial: XXXXXX-XX-XXX (missing digit)
                if re.search(r'\d{6}-\d{2}-\d{3,4}', line):
                    continue
                
                # Filter out lines that are just numbers (likely IC numbers, page numbers, or noise)
                # Matches 5+ consecutive digits like "0320633", "34600", etc.
                # But be careful: "34600 KAMUNTING" has 5 digits so won't match (space breaks it)
                stripped_for_check = line.strip()
                if re.match(r'^\d{5,}$', stripped_for_check):
                    continue
                
                # Also check for numbers with internal spaces/punctuation: "0320 633" or similar patterns
                # This catches digit-heavy lines that might have slipped through
                if re.match(r'^[\d\s\-\.]+$', stripped_for_check) and re.sub(r'[\s\-\.]', '', stripped_for_check):
                    # Check if it's 70%+ digits
                    nums_only = re.sub(r'[\s\-\.]', '', stripped_for_check)
                    if len(nums_only) >= 5 and len(nums_only) >= len(stripped_for_check) * 0.7:
                        continue
                
                # Filter out standalone single or double digits (likely OCR noise or page numbers)
                if re.match(r'^\d{1,2}$', line.strip()):
                    continue
                
                # Filter lines that are mostly digits (>70% digits with minimal text)
                # Examples: "0320633" (100% digits), "0320633 " with spaces
                stripped_line = line.strip()
                digit_count = sum(1 for c in stripped_line if c.isdigit())
                if digit_count >= len(stripped_line) * 0.7 and digit_count >= 5:
                    # This is a line with 70% or more digits and at least 5 digit characters
                    continue
                
                # Filter out garbage text: short lines (<=4 chars) that don't match address patterns
                # Examples: "lacA", "H", "E", "AANI", "ERA" - these are typically OCR noise or back-of-IC text
                if len(line.strip()) <= 4:
                    # Only keep if it matches known address patterns (like "NO", "LOT", "KG", etc.)
                    if not any(keyword in line_upper for keyword in address_keywords):
                        # Skip short lines that don't match address keywords
                        # This filters out garbage like "AANI", "ERA", "H", etc.
                        continue
                
                # Apply corrections to this line
                corrected_line = correct_ocr_errors(line)
                corrected_line = split_malay_words(corrected_line)
                
                # Format spacing - but avoid adding space in unit patterns like "9B/KU"
                # Don't add space between letter and digit if there's a slash (unit pattern)
                # Only add space: letter+digit when no slash involved, and digit+letter when no slash involved
                corrected_line = re.sub(r'([A-Z]+)(\d)(?!/)', r'\1 \2', corrected_line)  # "MERANTI9" -> "MERANTI 9" but not "9B/KU"
                corrected_line = re.sub(r'(\d)([A-Z])(?!/)', r'\1 \2', corrected_line)    # "9B" -> "9 B" but not when part of unit pattern
                corrected_line = re.sub(r'\s+', ' ', corrected_line).strip()
                
                # Check for state and format it
                for state_key, state_val in state_name_map.items():
                    if state_key in corrected_line.upper():
                        corrected_line = re.sub(state_key, state_val, corrected_line, flags=re.IGNORECASE)
                
                # FINAL CHECK: Reject lines that are still mostly digits after corrections
                # This catches cases where OCR correction added spaces: "0 3 2 0 6 3 3"
                digit_count = sum(1 for c in corrected_line if c.isdigit())
                if digit_count >= 6 and digit_count >= len(corrected_line) * 0.7:
                    # This line is 70%+ digits with 6+ digit chars - it's likely an IC fragment
                    # Only allow if it looks like a proper postal code (5 digits + space + text)
                    if not re.match(r'^\d{5}\s+[A-Z]', corrected_line):
                        print(f"[FILTER] Skipping mostly-digit line after corrections: '{corrected_line}'")  # DEBUG
                        continue
                
                if corrected_line:
                    address_lines.append(corrected_line)
        
        # Join address lines with commas
        if address_lines:
            # Reorder address components to proper Malaysian address format:
            # Unit/House -> Street -> Area -> Locality -> Postcode+City -> State
            
            # Categorize address lines
            unit_numbers = []  # DG-12, A-01-25, LOT 123
            street_names = []  # LORONG HELANG 3, JALAN 17/56
            area_names = []    # TAMAN, DESA, PERMAI INDAH
            localities = []    # SUNGAI DUA, GELUGOR (without postcode)
            postcodes = []     # 11700 GELUGOR (with postcode)
            states = []        # PULAU PINANG, SELANGOR
            others = []        # Everything else
            
            state_list = ['PULAU PINANG', 'PINANG', 'SELANGOR', 'JOHOR', 'KEDAH', 'KELANTAN', 
                          'TERENGGANU', 'PAHANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
                          'MELAKA', 'NEGERI SEMBILAN', 'KUALA LUMPUR', 'PUTRAJAYA', 'LABUAN', 'PENANG']
            
            for line in address_lines:
                line_upper = line.upper().strip()
                
                # Check if it's a state
                if any(state in line_upper for state in state_list):
                    states.append(line)
                # Check if it's a postcode line (5 digits + text)
                elif re.match(r'^\d{5}\s', line_upper):
                    postcodes.append(line)
                # Check if it's a unit number (like DG-12, A-01-25, LOT 123)
                elif re.match(r'^[A-Z]{1,2}-\d', line_upper) or line_upper.startswith('LOT') or line_upper.startswith('NO'):
                    unit_numbers.append(line)
                # Check if it's a street name (LORONG, JALAN, LEBUH)
                elif any(kw in line_upper for kw in ['LORONG', 'JALAN', 'LEBUH', 'JLN']):
                    street_names.append(line)
                # Check if it's an area name (TAMAN, DESA, PERMAI, INDAH)
                elif any(kw in line_upper for kw in ['TAMAN', 'DESA', 'PERMAI', 'INDAH', 'BANDAR', 'FELDA']):
                    area_names.append(line)
                # Remaining are likely localities
                else:
                    localities.append(line)
            
            # Reconstruct address in proper order
            ordered_parts = []
            ordered_parts.extend(unit_numbers)
            ordered_parts.extend(street_names)
            ordered_parts.extend(area_names)
            ordered_parts.extend(localities)
            ordered_parts.extend(postcodes)
            ordered_parts.extend(states)
            
            # Remove duplicates while preserving order
            seen = set()
            final_parts = []
            for part in ordered_parts:
                part_upper = part.upper().strip()
                if part_upper not in seen:
                    seen.add(part_upper)
                    final_parts.append(part)
            
            address = ', '.join(final_parts)
            # Remove any back-of-IC patterns that might have snuck in (format: xxxxxx-xx-xxxx-xx-xx)
            address = re.sub(r',?\s*\d{6}-\d{2}-\d{4}-\d{2}-\d{2}.*$', '', address).strip()
        
        # Validate address using postcode database
        postcode_validation = None
        if address:
            postal_code_match = re.search(r'(\d{5})', address)
            if postal_code_match:
                postal_code = postal_code_match.group(1)
                # Check if postcode exists in database
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
        
        return jsonify({
            'success': True,
            'data': {
                'ic_number': ic_number,
                'name': name,
                'gender': gender,
                'religion': religion,
                'address': address,
                'postcode_validation': postcode_validation,
                'document_type': 'Malaysia Identity Card (MyKad)' if is_malaysia_ic else 'Unknown Document',
                'orientation_angle': int(best_angle) if 'best_angle' in locals() else 0,
                'raw_ocr_text': extracted_text
            }
        }), 200
    
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }), 500

@app.route('/api/ocr/batch', methods=['POST'])
def batch_ocr():
    """
    Process multiple OCR requests
    
    Request:
    {
        'files': [file1, file2, ...]
    }
    """
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        results = []
        
        for file in files:
            if file.filename == '':
                continue
            
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': 'Invalid file type'
                })
                continue
            
            file_data = file.read()
            
            try:
                if file_ext == '.pdf':
                    images = convert_from_bytes(file_data, poppler_path=POPPLER_PATH)
                    image = np.array(images[0])
                else:
                    image = Image.open(io.BytesIO(file_data))
                    image = np.array(image)
                
                extracted_text, angle = detect_orientation(image)
                
                if not extracted_text:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'No text detected'
                    })
                    continue
                
                ic_number = extract_ic_number(extracted_text)
                name = extract_name(extracted_text, ic_number)
                gender = extract_gender(extracted_text)
                religion = extract_religion(extracted_text)
                address = extract_address(extracted_text, ic_number, name)
                postcode_validation = validate_postcode(address)
                
                results.append({
                    'filename': filename,
                    'success': True,
                    'data': {
                        'ic_number': ic_number,
                        'name': name,
                        'gender': gender,
                        'religion': religion,
                        'address': address,
                        'postcode_validation': postcode_validation
                    }
                })
            except Exception as e:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total': len(files),
            'processed': len([r for r in results if r.get('success')]),
            'results': results
        }), 200
    
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/info', methods=['GET'])
def get_info():
    """Get API information"""
    return jsonify({
        'api_name': 'Malaysia IC OCR API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'POST /api/ocr': 'Process single IC image/PDF',
            'POST /api/ocr/batch': 'Process multiple IC images/PDFs',
            'GET /api/info': 'Get API information'
        },
        'supported_formats': ['JPG', 'PNG', 'PDF'],
        'max_file_size': '20MB',
        'postcode_db_loaded': len(postcode_state_map) > 0,
        'postcode_count': len(postcode_state_map)
    }), 200

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'File too large (max 20MB)'}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Malaysia IC OCR Flask API...")
    logger.info("Available endpoints:")
    logger.info("  GET  http://localhost:5000/api/health")
    logger.info("  GET  http://localhost:5000/api/info")
    logger.info("  POST http://localhost:5000/api/ocr")
    logger.info("  POST http://localhost:5000/api/ocr/batch")
    logger.info("\nTesting with Postman:")
    logger.info("  1. Import the endpoints above")
    logger.info("  2. Use multipart/form-data for file uploads")
    logger.info("  3. Set 'file' as the form field name")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
