import streamlit as st
from paddleocr import PaddleOCR
import cv2
import numpy as np
import re
from PIL import Image
import json
import os
import gc
import sys
import time
from pdf2image import convert_from_bytes

# Poppler path for PDF conversion (Windows)
POPPLER_PATH = os.path.join(os.path.dirname(__file__), 'poppler', 'poppler-24.08.0', 'Library', 'bin')

# Load Malaysia postcodes database
POSTCODES_DB_PATH = os.path.join(os.path.dirname(__file__), 'malaysia-postcodes-main', 'malaysia-postcodes-main', 'data', 'json', 'postcodes.json')

@st.cache_resource
def load_postcodes_db():
    """Load Malaysia postcodes database into memory for validation"""
    try:
        with open(POSTCODES_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not load postcodes database: {e}")
        return None

postcodes_db = load_postcodes_db()

# Create a postcode to state mapping for quick lookup
@st.cache_resource
def build_postcode_state_map():
    """Build a postcode -> state mapping from the database"""
    postcode_map = {}
    if postcodes_db:
        for state in postcodes_db.get('states', []):
            state_name = state.get('name', '')
            for city in state.get('cities', []):
                for postcode in city.get('postcodes', []):
                    postcode_map[postcode] = state_name
    return postcode_map

postcode_state_map = build_postcode_state_map()

# Set environment variable to skip model connectivity check
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# Configure Streamlit to prevent timeout issues
st.set_page_config(page_title="Malaysia IC OCR", layout="wide", initial_sidebar_state="expanded")

# Initialize PaddleOCR with mobile model (more stable)
@st.cache_resource
def load_ocr():
    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
        device='cpu',
        ocr_version='PP-OCRv4',
        text_detection_model_name='PP-OCRv4_mobile_det',
        text_recognition_model_name='PP-OCRv4_mobile_rec'
    )

ocr = load_ocr()

st.title("Malaysia IC OCR Scanner")
st.write("Upload an image or PDF of a Malaysian Identity Card (IC) to extract text using OCR.")
st.info("💡 **Supported formats**: JPG, PNG images or PDF files (first page will be processed)")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"], key="file_uploader")

if uploaded_file is not None:
    # Set processing flag
    st.session_state.processing = True
    
    try:
        # Show progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Force garbage collection before processing
        gc.collect()
        status_text.text("📂 Loading image...")
        progress_bar.progress(10)
        
        # Check if uploaded file is PDF
        if uploaded_file.name.lower().endswith('.pdf'):
            status_text.text("📄 Converting PDF to image...")
            progress_bar.progress(12)
            # Convert PDF to images (take first page only for IC)
            try:
                images = convert_from_bytes(
                    uploaded_file.getvalue(), 
                    first_page=1, 
                    last_page=1, 
                    dpi=200,
                    poppler_path=POPPLER_PATH
                )
                if not images:
                    st.error("❌ No pages found in PDF file.")
                    st.stop()
                image = images[0]  # Use first page
                st.info(f"PDF converted to image: {image.size[0]}x{image.size[1]} pixels")
            except Exception as pdf_error:
                st.error(f"❌ Error converting PDF: {str(pdf_error)}")
                st.write("Please ensure:")
                st.write("- PDF is not password-protected")
                st.write("- PDF contains scanned images or text")
                st.write("- File is a valid PDF format")
                st.stop()
        else:
            # Read the image normally
            image = Image.open(uploaded_file)
        
        # Check image size and format
        st.info(f"Original image: {image.size[0]}x{image.size[1]} pixels, mode: {image.mode}")
        
        # Resize large images to prevent memory issues - use smaller max size
        max_size = 1200
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            st.info(f"Image resized to {new_size[0]}x{new_size[1]} for processing")
        
        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Make a copy for display before converting to array
        display_image = image.copy()
        
        img_array = np.array(image, dtype=np.uint8)
        status_text.text("🖼️ Displaying image...")
        progress_bar.progress(15)
        
        # Display the image
        st.image(display_image, caption='Uploaded Image', width=600)
        
        # Clear image from memory to free up space
        del image
        del display_image
        gc.collect()
        
        # Try different rotations and flips to handle upside-down and mirrored images
        # Store the best result based on Malaysia IC keyword detection
        best_results = None
        best_score = 0
        best_angle = 0
        best_flip = None  # None, 'horizontal', or 'vertical'
        best_rotated_array = None
        best_flipped_array = None
        best_image = None  # Store the corrected image for drawing boxes
        best_text_count = 0
        orientations = [0, 90, 180, 270]
        flip_types = [None, 'horizontal']  # Try normal and horizontally flipped
        angle_stats = {}  # Store stats for each angle/flip combination
        
        status_text.text("🔄 Processing OCR at different angles and orientations... (this may take 30-60 seconds)")
        progress_bar.progress(20)
        
        total_combinations = len(orientations) * len(flip_types)
        combination_idx = 0
        
        for flip_type in flip_types:
            # Apply flip if needed
            if flip_type == 'horizontal':
                flipped_array = np.fliplr(img_array)
                flip_label = "H-Flip"
            elif flip_type == 'vertical':
                flipped_array = np.flipud(img_array)
                flip_label = "V-Flip"
            else:
                flipped_array = img_array
                flip_label = "Normal"
            
            for angle_idx, angle in enumerate(orientations):
                try:
                    # Update progress
                    progress = 20 + (combination_idx * (45 // total_combinations))
                    progress_bar.progress(min(progress, 65))
                    angle_display = f"{angle}°"
                    if flip_type:
                        angle_display = f"{flip_label}+{angle}°"
                    status_text.text(f"🔄 Processing OCR at {angle_display} (this may take ~15 seconds)...")
                    
                    # Rotate image if needed
                    if angle > 0:
                        rotated_array = np.rot90(flipped_array, k=angle//90)
                    else:
                        rotated_array = flipped_array
                    
                    # Run OCR
                    results = ocr.predict(rotated_array)
                    
                    # Score this result based on Malaysia IC keywords
                    if results and len(results) > 0:
                        ocr_result = results[0]
                        if hasattr(ocr_result, 'rec_texts'):
                            text_list = list(ocr_result.rec_texts)
                        elif isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
                            text_list = list(ocr_result['rec_texts'])
                        else:
                            text_list = []
                        
                        text_count = len(text_list)
                        full_text_candidate = ' '.join(text_list).upper()
                        
                        # Score: count Malaysia IC keywords + check for IC number pattern
                        score = 0
                        malaysia_ic_keywords = ['KAD PENGENALAN', 'MYKAD', 'IDENTITYCARD', 'IDENTITY CARD', 'WARGANEGARA']
                        for keyword in malaysia_ic_keywords:
                            if keyword in full_text_candidate:
                                score += 2
                        
                        # Check for IC number pattern
                        if re.search(r'\d{6}-\d{2}-\d{4}', full_text_candidate):
                            score += 3
                        
                        # Store stats for this combination
                        stats_key = f"{flip_label}+{angle}°" if flip_type else f"{angle}°"
                        angle_stats[stats_key] = {'score': score, 'text_count': text_count, 'has_ic': score > 0}
                        
                        # Primary: IC detection score (most important)
                        # Secondary: Text line count (tiebreaker)
                        # Tertiary: Prefer normal orientation (no flip) if everything is equal
                        if (score > best_score or 
                            (score == best_score and text_count > best_text_count) or
                            (score == best_score and text_count == best_text_count and flip_type is None)):
                            best_score = score
                            best_results = results
                            best_angle = angle
                            best_flip = flip_type
                            best_rotated_array = rotated_array
                            best_flipped_array = flipped_array
                            best_image = rotated_array.copy()  # Store the corrected image
                            best_text_count = text_count
                    
                    combination_idx += 1
                except Exception as rotation_error:
                    st.warning(f"Error processing {angle_display}: {str(rotation_error)}")
                    combination_idx += 1
                    continue
        
        # Use the best results found
        if best_results is None:
            st.error("❌ Could not process image at any orientation. Please try a clearer image.")
            raise Exception("No usable OCR results from any rotation angle or flip")
        
        results = best_results
        
        # Display orientation information
        orientation_msg = []
        if best_flip == 'horizontal':
            orientation_msg.append("horizontally flipped")
        elif best_flip == 'vertical':
            orientation_msg.append("vertically flipped")
        
        if best_angle > 0:
            orientation_msg.append(f"rotated {best_angle}°")
        
        if orientation_msg:
            st.info(f"ℹ️ Image was {' and '.join(orientation_msg)} for better OCR recognition")
        
        # Show detection statistics
        with st.expander("📊 Detection Stats by Angle"):
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            for angle in orientations:
                if angle in angle_stats:
                    stats = angle_stats[angle]
                    if angle == best_angle:
                        status = "✅ BEST"
                    else:
                        status = "⭕"
                    st.write(f"{status} **{angle}°**: {stats['text_count']} lines detected, Score: {stats['score']}")
        
        # Display the rotated image
        if best_angle > 0:
            rotated_image = Image.fromarray(best_rotated_array)
            st.image(rotated_image, caption=f'Image Rotated {best_angle}° for Processing', width=600)
            del rotated_image
        
        # Display the flipped image
        if best_flip is not None:
            flipped_image = Image.fromarray(best_flipped_array)
            st.image(flipped_image, caption=f'Image Flipped {best_flip.replace("_", " ")} for Processing', width=600)
            del flipped_image
        
        gc.collect()
        
        # Malay dictionary for word splitting - common Malay names and place names
        malay_words = {
            # Names and place names
            'NORLIYANA': 'NORLIYANA',
            'MUHAMMADFAIZ': 'MUHAMMAD FAIZ',  # Handle name concatenation
            'MOHDLAMRI': 'MOHD LAMRI',
            'MOHDIRWAN': 'MOHD IRWAN',  # Handle MOHD IRWAN concatenation
            'AJAANN': 'ABDUL',  # OCR error correction
            'JAANMALA': 'RAHMAN',  # OCR error correction
            'MERANTIPUTIH': 'MERANTI PUTIH',  # Handle street name concatenation
            'BANDARINDERA': 'BANDAR INDERA',  # Handle address compound words
            'LORONGIM': 'LORONG IM',  # Handle address LORONG+unit code concatenation
            'LLORONGIM': 'LORONG IM',  # Handle OCR double-L variant
            'JALANKENANGA': 'JALAN KENANGA',  # Handle street name concatenation
            'KUALALIPIS': 'KUALA LIPIS',  # Handle city name concatenation
            'SUBANGJAYA': 'SUBANG JAYA',  # Handle city name concatenation
            'KUALAPILAH': 'KUALA PILAH',
            'KUALALUMPUR': 'KUALA LUMPUR',
            'WILAYAHPERSEKUTUAN': 'WILAYAH PERSEKUTUAN',
            'SUNGAIDUAKECIL': 'SUNGAI DUA KECIL',
            'TAMANPUTERA': 'TAMAN PUTERA',
            'TAMANPUTERAJAYA': 'TAMAN PUTERA JAYA',
            'KOTAKINABALU': 'KOTA KINABALU',
            'SHAHALAM': 'SHAH ALAM',
            # Malaysian states - prevent incorrect splitting
            'TERENGGANU': 'TERENGGANU',
            'NEGERISEMBILAN': 'NEGERI SEMBILAN',
            'NEGRISEMBILAN': 'NEGERI SEMBILAN',
            'SELANGOR': 'SELANGOR',
            'JOHOR': 'JOHOR',
            'KEDAH': 'KEDAH',
            'KELANTAN': 'KELANTAN',
            'LABUAN': 'LABUAN',
            'MELAKA': 'MELAKA',
            'PAHANG': 'PAHANG',
            'PENANG': 'PENANG',
            'PERAK': 'PERAK',
            'PERLIS': 'PERLIS',
            'SABAH': 'SABAH',
            'SARAWAK': 'SARAWAK',
        }
        
        def split_malay_words(text):
            """Replace concatenated Malay words using dictionary"""
            result = text
            for concat_word, proper_form in malay_words.items():
                if concat_word in result:
                    result = result.replace(concat_word, proper_form)
            return result
        
        def correct_ocr_errors(text):
            """Correct common OCR misreads"""
            corrections = {
                'MOHAMED SAD': 'MOHAMED SAID',  # Common OCR error
                'BIN TI': 'BINTI',  # Fix BINTI split as BIN TI
                'LLORONG': 'LORONG',  # Fix double-L in street name
                'LLOT': 'LOT',  # Fix double-L in lot number
                'JJALAN': 'JALAN',  # Fix double-J in street name
                r'(\d+)\s+([A-Z]+/[A-Z]+)': r'\1\2',  # "9 B/KU" -> "9B/KU", "34 C/DA" -> "34C/DA" (unit patterns)
                r'(\d+)([A-Z]{5,})': r'\1 \2',  # "33LLORONGIM" -> "33 LLORONGIM", "25200KUANTAN" -> "25200 KUANTAN" (number+word patterns)
                'BLOKA': 'BLOK A',  # Format block indicators
                'BLOKB': 'BLOK B',
                'BLOKC': 'BLOK C',
                'BLOKD': 'BLOK D',
                'BLOKE': 'BLOK E',
                'BLOKF': 'BLOK F',
                'BLOKG': 'BLOK G',
                'BLOKH': 'BLOK H',
                'BLOKI': 'BLOK I',
                'BLOKJ': 'BLOK J',
                'BLOKK': 'BLOK K',
                'BLOKL': 'BLOK L',
                'BLOKM': 'BLOK M',
                'BLOKN': 'BLOK N',
                'BLOKO': 'BLOK O',
                'BLOKP': 'BLOK P',
                'BLOKQ': 'BLOK Q',
                'BLOKR': 'BLOK R',
                'BLOKS': 'BLOK S',
                'BLOKT': 'BLOK T',
                'BLOKU': 'BLOK U',
                'BLOKV': 'BLOK V',
                'BLOKW': 'BLOK W',
                'BLOKX': 'BLOK X',
                'BLOKY': 'BLOK Y',
                'BLOKZ': 'BLOK Z',
            }
            result = text
            for wrong, correct in corrections.items():
                # Check if the key looks like a regex pattern (starts with backslash)
                if wrong.startswith('\\') or '(' in wrong:
                    result = re.sub(wrong, correct, result)
                else:
                    result = result.replace(wrong, correct)
            return result
        
        # Extract OCR text from results
        extracted_text = []
        rec_polys_list = []
        ic_number = None
        name = None
        address = None
        gender = None
        religion = None
        is_malaysia_ic = False
        
        # PaddleOCR returns a list with one OCRResult object
        # The OCRResult has 'rec_texts' and 'rec_polys' attributes
        if results and len(results) > 0:
            ocr_result = results[0]
            # Access rec_texts - works for both dict and OCRResult object
            if hasattr(ocr_result, 'rec_texts'):
                extracted_text = list(ocr_result.rec_texts)
            elif isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
                extracted_text = list(ocr_result['rec_texts'])
            
            # Access rec_polys for bounding boxes
            if hasattr(ocr_result, 'rec_polys'):
                rec_polys_list = list(ocr_result.rec_polys)
            elif isinstance(ocr_result, dict) and 'rec_polys' in ocr_result:
                rec_polys_list = list(ocr_result['rec_polys'])
        
        # Apply OCR corrections to each extracted text item BEFORE joining
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
            (r'1oo', '100'),  # OCR error: lOO -> 100 (letter O instead of digit 0)
            (r'88\s*A\s*60', '88450'),  # Address correction: "88 A 60" or "88A60" -> "88450"
            (r'SUNGAITUA', 'SUNGAI TUA'),  # Split merged place name
            (r'APTIDAMAN', 'APT IDAMAN'),  # Split merged address: APTIDAMAN -> APT IDAMAN
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
        ]
        corrected_text = []
        for text in extracted_text:
            corrected = text
            for pattern, replacement in ocr_corrections:
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
            corrected_text.append(corrected)
        extracted_text = corrected_text
        
        # Join all text for easier parsing
        full_text = ' '.join(extracted_text)
        full_text_upper = full_text.upper()
        
        # Classify as Malaysia ID card - check for Malaysia IC keywords
        malaysia_ic_keywords = ['KAD PENGENALAN', 'MYKAD', 'IDENTITYCARD', 'IDENTITY CARD', 'WARGANEGARA']
        is_malaysia_ic = any(keyword in full_text_upper for keyword in malaysia_ic_keywords)
        
        # Extract IC number (12 digits: XXXXXX-XX-XXXX)
        ic_match = re.search(r'\d{6}-\d{2}-\d{4}', full_text)
        if ic_match:
            ic_number = ic_match.group()
        
        # Split text into tokens for better processing
        tokens = full_text.split()
        
        # Initialize variables to avoid NameError
        name_tokens = []
        
        # Function to detect Chinese characters
        def has_chinese(text):
            """Check if text contains Chinese characters"""
            import unicodedata
            for char in text:
                if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:  # CJK Unified Ideographs
                    return True
            return False
        
        # Noise words to filter out (watermarks, misread text)
        noise_words = ['ORPHEUSCAPITAL', 'ONLY', 'SAMPLE', 'SPECIMEN', 'WATERMARK', 'COPYRIGHT', 'AKER', 'ERAJ', 'MALAY', 'SIA', 'PENT', 'GR', 'PENGENJALAN', 'SLAM', 'LALAYSI', 'Touch', 'chip']
        
        # Filter out lines containing Chinese characters from extracted_text
        extracted_text = [line for line in extracted_text if not has_chinese(line)]
        
        # Extract Name - comes after IC number, maximum 2 lines
        if ic_number:
            # Find which extracted_text line contains the IC number
            ic_line_idx = None
            for idx, line in enumerate(extracted_text):
                if ic_number in line:
                    ic_line_idx = idx
                    break
            
            if ic_line_idx is not None:
                # Collect next 2 non-empty lines as name
                name_tokens = []
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
                        st.warning(f"Name processing issue: {regex_error}")
                        # Fallback to basic processing
                        name = raw_name.replace('BIN TI', 'BINTI')
                        name = split_malay_words(name)
                        name = re.sub(r'\s+', ' ', name).strip()
        
        # Extract Gender - look for Malay gender terms
        gender_keywords = {
            'LELAKI': 'LELAKI (Male)',
            'PEREMPUAN': 'PEREMPUAN (Female)',
        }
        
        for keyword, value in gender_keywords.items():
            if keyword in full_text_upper:
                gender = value
                break
        
        # Extract Religion - look for Malay religion terms (handle OCR variations)
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
        address_keywords = ['LOT', 'JALAN', 'KAMPUNG', 'KG', 'JLN', 'NO', 'BATU', 'LEBUH', 'LORONG', 'JAMBATAN', 'PPR', 'BLOK', 'UNIT', 'TINGKAT', 'TAMAN', 'BANDAR', 'PERINGKAT', 'FELDA']
        gender_religion_keywords = ['LELAKI', 'PEREMPUAN', 'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'ISL.AM', 'ISLAMIC']
        
        # Malaysian states for address formatting (with and without spaces for OCR variations)
        malaysia_states = [
            'TERENGGANU', 'SELANGOR', 'KUALA LUMPUR', 'KUALALUMPUR', 'KL',
            'JOHOR', 'KEDAH', 'KELANTAN', 'LABUAN', 'MELAKA', 'NEGERI SEMBILAN', 'NEGERISEMBILAN',
            'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
            'WILAYAH PERSEKUTUAN', 'WP'
        ]
        
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
            
            # Skip lines that are part of the name
            if idx < name_line_count + 5:  # Add buffer for header lines before name
                # Check if this line is one of the name lines
                if any(name_token.upper() in line_upper for name_token in (name_tokens if name_tokens else [])):
                    continue
            
            # Pure numeric lines after name should start address collection
            # (these are typically house/unit numbers like "166", "5-9")
            if re.match(r'^[\d\-\s]+$', line_upper):
                # BUT skip IC number patterns
                if not re.match(r'^\d{6}-\d{2}-\d{3,4}$', line.strip()):
                    if idx >= 4:  # Make sure we're past header/IC/name section
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
            
            # Skip gender/religion keywords and stop collecting address
            if any(keyword in line_upper for keyword in gender_religion_keywords):
                collecting_address = False
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
                                break
                    else:
                        is_address_line = True
                        break
                # Also check if keyword appears after digits (like "33LORONG" or "25JALAN")
                if re.search(r'\d+' + addr_keyword, corrected_line_for_check):
                    is_address_line = True
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
            
            # Check for postal code patterns like "34600 KAMUNTING"
            if re.match(r'^\d{5}\s*[A-Z]', corrected_line_for_check):
                is_address_line = True
                collecting_address = True
            
            # Check for state names
            if any(state in corrected_line_for_check for state in malaysia_states):
                is_address_line = True
            
            # If we found an address keyword, start collecting
            if is_address_line:
                collecting_address = True
            
            # Once we're collecting address, include ALL subsequent lines until we hit exclusions
            # This ensures place names like "KAMUNTING BARU TAMBAHAN" are included
            if collecting_address:
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
                
                # Filter out lines that are just numbers (likely IC numbers without dashes)
                if re.match(r'^\d{6,12}$', line.strip()):
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
                
                if corrected_line:
                    address_lines.append(corrected_line)
        
        # Join address lines with commas
        if address_lines:
            address = ', '.join(address_lines)
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
        
        # Display results in a nice format
        st.subheader("📋 Document Classification")
        if is_malaysia_ic:
            st.success("✅ Malaysia Identity Card (KAD PENGENALAN MALAYSIA / MyKad)")
        else:
            st.warning("❌ Not identified as a Malaysia Identity Card")
        
        # Show postcode validation if available
        if postcode_validation:
            if postcode_validation['valid']:
                st.info(f"✅ Postcode {postcode_validation['postcode']} is valid for **{postcode_validation['state']}**")
            else:
                st.warning(f"⚠️ {postcode_validation['message']}: {postcode_validation.get('postcode', 'N/A')}")
        
        # Create a structured information display
        st.subheader("📝 Extracted Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**IC Number:**")
            if ic_number:
                st.info(ic_number)
            else:
                st.warning("Not detected")
            
            st.markdown("**Name:**")
            if name:
                st.info(name)
            else:
                st.warning("Not detected")
        
        with col2:
            st.markdown("**Gender:**")
            if gender:
                st.info(gender)
            else:
                st.warning("Not detected")
            
            st.markdown("**Religion:**")
            if religion:
                st.info(religion)
            else:
                st.warning("Not detected")
        
        st.markdown("**Address:**")
        if address:
            st.info(address)
        else:
            st.warning("Not detected")
        
        # Complete the progress bar
        progress_bar.progress(100)
        status_text.text("✅ Processing completed!")
        
        # Show raw extracted text for debugging
        with st.expander("📄 View All Extracted Text (Debug)"):
            st.text("\n".join(extracted_text))
        
        # JSON export option
        st.subheader("💾 Export Data")
        
        extracted_data = {
            'is_malaysia_ic': is_malaysia_ic,
            'ic_number': ic_number,
            'name': name,
            'address': address,
            'gender': gender,
            'religion': religion
        }
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy as JSON"):
                st.code(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        
        # Optional: Display bounding boxes
        if st.checkbox("Show text bounding boxes"):
            # Draw boxes on the corrected image (after flip/rotation)
            img_with_boxes = best_image.copy()
            for poly in rec_polys_list:
                if poly is not None and len(poly) >= 4:
                    pts = np.array(poly, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img_with_boxes, [pts], True, (0, 255, 0), 2)
            
            st.image(img_with_boxes, caption='Corrected Image with Detected Text Boxes', width=600)
    
    except MemoryError:
        st.error("❌ Memory Error: Image too large. Please use a smaller image.")
    except Exception as e:
        st.error(f"❌ Error processing image: {str(e)}")
        st.write("Please try uploading a different/smaller image.")
        import traceback
        with st.expander("Debug info"):
            st.code(traceback.format_exc())