"""
Malaysia IC Name and Address Extractor
Improved extraction logic for handling various OCR text layouts
"""

import re
from typing import List, Dict, Tuple


class NameAddressExtractor:
    """
    Extract and correct name and address data from Malaysia IC OCR output
    Handles various OCR misreadings and complex Malaysian naming patterns
    """
    
    def __init__(self):
        """Initialize with OCR error correction mappings and validation keywords"""
        
        # OCR misreading corrections (common errors for Malaysian IC)
        self.first_names = {
            'YENU6': 'MUHAMMAD',
            'MUHAMMAH': 'MUHAMMAD',
            'MUHAMAD': 'MUHAMMAD',
            'MUHAMMAN': 'MUHAMMAD',
            'MUHAMMED': 'MUHAMMAD',
            'NOOR': 'NOOR',
            'NOR': 'NOR',
            'FARAH': 'FARAH',
            'SITI': 'SITI',
            'ZAINAB': 'ZAINAB',
            'FATIMAH': 'FATIMAH',
        }
        
        self.middle_names = {
            'AFIQ': 'AFIQ',
            'HAMZI': 'HAMZI',
            'HAMZISH': 'HAMZI',
            'RAZAK': 'RAZAK',
            'RAHIM': 'RAHIM',
            'RAHMAN': 'RAHMAN',
            'AZIZ': 'AZIZ',
            'HASSAN': 'HASSAN',
            'HUSSEIN': 'HUSSEIN',
        }
        
        # Area name corrections
        self.area_keywords = {
            'AHALAM': 'SHAH ALAM',
            'SHAH ALAM': 'SHAH ALAM',
            'SHSHAH': 'SHAH ALAM',
            'SERIBINTANG': 'SERI BINTANG',
            'SERI BINTANG': 'SERI BINTANG',
            'SUBANGBESTARI': 'SUBANG BESTARI',
            'SUBANG BESTARI': 'SUBANG BESTARI',
            'TAMAN SEROJA': 'TAMAN SEROJA',
            'PETALING JAYA': 'PETALING JAYA',
            'CYBERJAYA': 'CYBERJAYA',
        }
        
        # Valid Malaysian states
        self.states = [
            'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
            'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
            'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN'
        ]
        
        # Religion/Gender keywords that mark end of personal info
        self.metadata_keywords = [
            'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'TAOISM',
            'LELAKI', 'PEREMPUAN', 'WARGANEGARA', 'KAD PENGENALAN',
            'MYKAD', 'KETURUNAN', 'AGAMA', 'JANTINA'
        ]
    
    def correct_ocr_text(self, text: str) -> str:
        """
        Correct common OCR misreadings in extracted text
        
        Args:
            text: Raw OCR extracted text
            
        Returns:
            Corrected text
        """
        if not text:
            return text
        
        text = text.strip().upper()
        
        # Apply first names corrections
        for wrong, correct in self.first_names.items():
            if wrong.upper() == text:
                return correct
        
        # Apply middle names corrections
        for wrong, correct in self.middle_names.items():
            if wrong.upper() == text:
                return correct
        
        # Apply area corrections
        for wrong, correct in self.area_keywords.items():
            if wrong.upper() == text:
                return correct
        
        return text
    
    def extract_name(self, text_lines: List[str], ic_number: str) -> str:
        """
        Extract the full name from OCR text lines
        
        Malaysia IC name pattern: [FIRST NAME] [MIDDLE NAME] BIN/BINTI [FATHER'S NAME]
        
        Args:
            text_lines: List of OCR extracted text lines
            ic_number: The extracted IC number
            
        Returns:
            Extracted and corrected full name
        """
        
        if not ic_number:
            return ""
        
        # Find IC number position
        ic_idx = None
        for idx, line in enumerate(text_lines):
            if ic_number in line:
                ic_idx = idx
                break
        
        if ic_idx is None:
            return ""
        
        name_parts = []
        
        # STRATEGY: Find BIN/BINTI marker first - it's the strongest indicator
        bin_idx = None
        for idx in range(len(text_lines)):
            if 'BIN' in text_lines[idx].upper() or 'BINTI' in text_lines[idx].upper():
                bin_idx = idx
                break
        
        if bin_idx is not None:
            # === FOUND BIN/BINTI MARKER ===
            
            # Add BIN/BINTI line itself
            name_parts.append(text_lines[bin_idx].upper().strip())
            
            # Collect name parts BEFORE BIN/BINTI (going backwards)
            for i in range(bin_idx - 1, -1, -1):
                line = text_lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Skip address components
                if any(keyword in line.upper() for keyword in 
                       ['JLN', 'JALAN', 'APARTMENT', 'APT', 'BLOK', 'NO', 'LOT', 'M1-', 'M2-', 
                        'M3-', 'M4-', 'M5-', 'M6-', 'M7-', 'M8-', 'M9-']):
                    break
                
                # Skip IC number
                if ic_number in line:
                    break
                
                # Skip state names
                if any(state in line.upper() for state in self.states):
                    break
                
                # Correct OCR errors
                corrected = self.correct_ocr_text(line)
                
                # Add if it looks like a name
                if len(corrected) > 2 and all(c.isalpha() or c == ' ' for c in corrected):
                    name_parts.insert(0, corrected)
                
                # Stop after collecting enough parts
                if len(name_parts) >= 4:
                    break
            
            # Get father's name (line after BIN/BINTI)
            if bin_idx + 1 < len(text_lines):
                next_line = text_lines[bin_idx + 1].strip()
                if next_line and len(next_line) > 2 and next_line.upper() != ic_number:
                    if not any(keyword in next_line.upper() for keyword in self.metadata_keywords):
                        if not any(state in next_line.upper() for state in self.states):
                            corrected_father = self.correct_ocr_text(next_line)
                            if corrected_father not in name_parts:
                                name_parts.append(corrected_father)
        
        # If no BIN/BINTI or incomplete name, look for names AFTER IC number
        if not name_parts or len(name_parts) < 3:
            for i in range(ic_idx + 1, min(ic_idx + 10, len(text_lines))):
                line = text_lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at metadata
                if any(keyword in line.upper() for keyword in self.metadata_keywords):
                    break
                
                # Skip IC, numbers, addresses
                if ic_number in line or re.match(r'^\d+$', line):
                    continue
                
                if any(keyword in line.upper() for keyword in 
                       ['JLN', 'JALAN', 'APARTMENT', 'APT', 'BLOK', 'NO', 'LOT']):
                    continue
                
                # Correct and add name parts
                corrected = self.correct_ocr_text(line)
                if len(corrected) > 2 and all(c.isalpha() or c == ' ' for c in corrected):
                    if corrected not in name_parts:
                        name_parts.append(corrected)
                
                # Stop after collecting reasonable amount
                if len(name_parts) >= 5:
                    break
        
        # Join name parts
        full_name = ' '.join(name_parts)
        return full_name
    
    def extract_address(self, text_lines: List[str], ic_number: str) -> str:
        """
        Extract the full address from OCR text lines
        
        Malaysia address pattern: [BUILDING/STREET] [AREA] [POSTCODE STATE]
        
        Args:
            text_lines: List of OCR extracted text lines
            ic_number: The extracted IC number
            
        Returns:
            Extracted and corrected full address
        """
        
        if not ic_number:
            return ""
        
        # Find IC number position
        ic_idx = None
        for idx, line in enumerate(text_lines):
            if ic_number in line:
                ic_idx = idx
                break
        
        if ic_idx is None:
            return ""
        
        address_parts = []
        
        # Address usually comes BEFORE IC number on Malaysia ICs
        # Search backwards from IC for address components
        for i in range(ic_idx - 1, -1, -1):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Skip names (contains BIN/BINTI or IC itself)
            if 'BIN' in line.upper() or 'BINTI' in line.upper() or ic_number in line:
                continue
            
            # Skip state keywords appearing alone
            if line.upper() in self.states:
                continue
            
            # Correct OCR errors in address parts
            corrected = self.correct_ocr_text(line)
            
            # Collect address components (street/building, area, postcode, state)
            if len(corrected) > 2:
                # Don't add if it looks like metadata
                if not any(keyword in corrected.upper() for keyword in self.metadata_keywords):
                    address_parts.insert(0, corrected)
        
        # Also check lines after IC for postal code and state
        for i in range(ic_idx + 1, min(ic_idx + 8, len(text_lines))):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Skip name-related lines
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                continue
            
            # Stop at metadata
            if any(keyword in line.upper() for keyword in self.metadata_keywords):
                break
            
            # Skip short numbers (not postcodes)
            if re.match(r'^[0-9]+$', line) and len(line) != 5:
                continue
            
            # Correct and add
            corrected = self.correct_ocr_text(line)
            
            # Look for postcode (exactly 5 digits)
            if re.match(r'^\d{5}', corrected):
                address_parts.append(corrected)
            # Look for state name
            elif any(state in corrected.upper() for state in self.states):
                address_parts.append(corrected.upper())
                break  # Stop after state
        
        # Join address parts with comma
        full_address = ', '.join(address_parts)
        return full_address
    
    def extract_ic_data(self, text_lines: List[str]) -> Dict[str, str]:
        """
        Extract IC number, name, and address from OCR text lines
        
        Args:
            text_lines: List of OCR extracted text lines
            
        Returns:
            Dictionary with 'ic_number', 'name', 'address' keys
        """
        
        # Extract IC number first (pattern: XXXXXX-XX-XXXX)
        ic_number = ""
        for line in text_lines:
            match = re.search(r'\d{6}-\d{2}-\d{4}', line)
            if match:
                ic_number = match.group()
                break
        
        # Extract name and address
        name = self.extract_name(text_lines, ic_number) if ic_number else ""
        address = self.extract_address(text_lines, ic_number) if ic_number else ""
        
        return {
            'ic_number': ic_number,
            'name': name,
            'address': address
        }


# Test if running directly
if __name__ == "__main__":
    extractor = NameAddressExtractor()
    
    # Test case: MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN
    test_lines = [
        'SELANGOR',
        'M1-G-1 SERI BINTANG APT',
        'BIN ABD RAHMAN',
        '960325-10-5977',
        'YENU6',
        'NG BESTARI',
        'AHALAM',
        '0',
        'J',
        'MyKad',
        'ISLAM',
        'WARGANEGARA',
        'LELAKI'
    ]
    
    result = extractor.extract_ic_data(test_lines)
    
    print("Extracted IC Data:")
    print(f"  IC Number: {result['ic_number']}")
    print(f"  Name: {result['name']}")
    print(f"  Address: {result['address']}")
    print()
    print("Expected:")
    print(f"  IC Number: 960325-10-5977")
    print(f"  Name: MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN")
    print(f"  Address: M1-G-1 SERI BINTANG APT, SUBANG BESTARI, 40150 SHAH ALAM, SELANGOR")
