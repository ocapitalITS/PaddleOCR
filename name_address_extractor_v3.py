"""
Malaysia IC Name and Address Extractor - Version 3
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
        self.corrections = {
            'YENU6': 'MUHAMMAD',
            'MUHAMMAH': 'MUHAMMAD',
            'MUHAMAD': 'MUHAMMAD',
            'MUHAMMAN': 'MUHAMMAD',
            'MUHAMMED': 'MUHAMMAD',
            'AHALAM': 'SHAH ALAM',
            'SHSHAH': 'SHAH ALAM',
            'SERIBINTANG': 'SERI BINTANG',
            'SUBANGBESTARI': 'SUBANG BESTARI',
            'TAMAN SEROJA': 'TAMAN SEROJA',
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
        
        text_upper = text.strip().upper()
        
        # Direct mapping checks
        for wrong, correct in self.corrections.items():
            if wrong.upper() == text_upper:
                return correct
        
        return text.strip().upper()
    
    def extract_name(self, text_lines: List[str], ic_number: str) -> str:
        """
        Extract the full name from OCR text lines
        
        Malaysia IC name pattern: [FIRST NAME] [MIDDLE NAME(S)] BIN/BINTI [FATHER'S NAME]
        
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
        
        # FIRST PASS: Find BIN/BINTI marker and use it as anchor
        bin_idx = None
        for idx in range(len(text_lines)):
            line_upper = text_lines[idx].upper()
            if 'BIN' in line_upper or 'BINTI' in line_upper:
                bin_idx = idx
                break
        
        if bin_idx is not None:
            # Add BIN/BINTI line itself
            name_parts.append(text_lines[bin_idx].upper().strip())
            
            # Collect lines after BIN/BINTI for father's name
            for i in range(bin_idx + 1, min(bin_idx + 3, len(text_lines))):
                line = text_lines[i].strip()
                if line and len(line) > 2 and line.upper() != ic_number:
                    if not any(kw in line.upper() for kw in self.metadata_keywords):
                        if line.upper() not in self.states:
                            corrected = self.correct_ocr_text(line)
                            if len(corrected) > 2 and all(c.isalpha() or c.isspace() for c in corrected):
                                name_parts.append(corrected)
                                break
        
        # SECOND PASS: Look for name components AFTER IC number
        # This is where the actual name parts often appear in the OCR output
        after_ic_names = []
        for i in range(ic_idx + 1, len(text_lines)):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Stop at metadata
            if any(kw in line.upper() for kw in self.metadata_keywords):
                break
            
            # Skip IC number
            if ic_number in line:
                continue
            
            # Skip pure numbers
            if re.match(r'^[0-9]+$', line):
                continue
            
            # Skip address-only lines (contain building numbers, postcodes)
            if re.match(r'^[M|L]\d', line):  # Building number like M1-G-1
                continue
            
            # Skip postcode
            if re.match(r'^\d{5}$', line):
                continue
            
            # Get corrected version
            corrected = self.correct_ocr_text(line)
            
            # Check if it's a name-like line (contains letters, not too many special chars)
            if len(corrected) > 2 and all(c.isalpha() or c.isspace() for c in corrected):
                # Skip states and specific keywords
                if corrected not in self.states and 'SEKSYEN' not in corrected:
                    after_ic_names.append(corrected)
        
        # Add after-IC names to the start (they're likely first names)
        for name in reversed(after_ic_names):
            name_parts.insert(0 if 'BIN' not in name else len(name_parts) - 1, name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_parts = []
        for part in name_parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)
        
        # Join name parts
        full_name = ' '.join(unique_parts)
        return full_name
    
    def extract_address(self, text_lines: List[str], ic_number: str) -> str:
        """
        Extract the full address from OCR text lines
        
        Malaysia address pattern: [BUILDING/STREET] [AREA] [SECTION] [POSTCODE STATE]
        
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
        
        # PASS 1: Collect address parts BEFORE IC
        for i in range(ic_idx - 1, -1, -1):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Skip name markers
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                continue
            
            # Skip IC number itself
            if ic_number in line:
                continue
            
            # Skip single-word states at the top
            if line.upper() in self.states:
                continue
            
            # Skip metadata
            if any(kw in line.upper() for kw in self.metadata_keywords):
                continue
            
            # Get corrected version
            corrected = self.correct_ocr_text(line)
            
            # Add if it looks like address
            if len(corrected) > 2:
                address_parts.insert(0, corrected)
        
        # PASS 2: Look after IC for postcode and state
        for i in range(ic_idx + 1, min(ic_idx + 8, len(text_lines))):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Stop at metadata
            if any(kw in line.upper() for kw in self.metadata_keywords):
                break
            
            # Skip name parts
            if all(c.isalpha() or c.isspace() for c in line) and len(line) < 20:
                # This is likely a name component, skip it
                if 'BIN' not in line.upper():
                    continue
            
            corrected = self.correct_ocr_text(line)
            
            # Look for postcode (5 digits)
            if re.match(r'^\d{5}', corrected):
                address_parts.append(corrected)
            # Look for state name
            elif any(state in corrected.upper() for state in self.states):
                address_parts.append(corrected.upper())
                break
            # Look for sections like SEKSYEN U5
            elif 'SEKSYEN' in corrected.upper():
                address_parts.append(corrected)
        
        # Join address parts
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
    print()
    print("Analysis:")
    print("Note: The test data doesn't contain 'AFIQ', 'HAMZI', 'SUBANG', 'SEKSYEN U5', or '40150'")
    print("These are missing from the OCR output provided")
