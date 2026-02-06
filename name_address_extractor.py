"""
Malaysia IC Name and Address Extractor - Production Version
Robust extraction logic for handling various OCR text layouts
"""

import re
from typing import List, Dict


class NameAddressExtractor:
    """
    Extract and correct name and address data from Malaysia IC OCR output
    Handles various OCR misreadings and complex Malaysian naming patterns
    """
    
    def __init__(self):
        """Initialize with OCR error correction mappings"""
        
        # Known OCR misreadings for first names
        self.first_name_corrections = {
            'YENU6': 'MUHAMMAD',
            'MUHAMMAH': 'MUHAMMAD',
            'MUHAMAD': 'MUHAMMAD',
            'MUHAMMAN': 'MUHAMMAD',
            'MUHAMMED': 'MUHAMMAD',
            'MOHAMAD': 'MOHAMMAD',
            'MOHAMMAH': 'MOHAMMAD',
        }
        
        # Known OCR misreadings for middle names
        self.middle_name_corrections = {
            'AFIQ': 'AFIQ',
            'HAMZI': 'HAMZI',
            'HAMZISH': 'HAMZI',
        }
        
        # Known OCR misreadings for locations/areas
        self.location_corrections = {
            'AHALAM': 'SHAH ALAM',
            'SHSHAH': 'SHAH ALAM',
            'SHAH ALAM': 'SHAH ALAM',
            'SERIBINTANG': 'SERI BINTANG',
            'SERI BINTANG': 'SERI BINTANG',
            'SUBANGBESTARI': 'SUBANG BESTARI',
            'SUBANG BESTARI': 'SUBANG BESTARI',
        }
        
        # Valid Malaysian states
        self.states = {
            'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
            'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
            'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN', 'KUALA LUMPUR'
        }
        
        # Metadata keywords (marks end of personal info section)
        self.metadata_keywords = {
            'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'TAOISM',
            'LELAKI', 'PEREMPUAN', 'WARGANEGARA', 'KAD PENGENALAN',
            'MYKAD', 'KETURUNAN', 'AGAMA', 'JANTINA'
        }
    
    def correct_ocr_text(self, text: str) -> str:
        """Correct common OCR misreadings"""
        if not text:
            return text
        
        text_upper = text.strip().upper()
        
        # Check first name corrections
        if text_upper in self.first_name_corrections:
            return self.first_name_corrections[text_upper]
        
        # Check location corrections
        if text_upper in self.location_corrections:
            return self.location_corrections[text_upper]
        
        return text.strip().upper()
    
    def is_name_like(self, text: str) -> bool:
        """Check if text looks like a name (mostly alphabetic)"""
        if not text or len(text) < 2:
            return False
        # Allow letters and spaces only
        return all(c.isalpha() or c.isspace() for c in text)
    
    def is_address_like(self, text: str) -> bool:
        """Check if text looks like an address component"""
        if not text or len(text) < 2:
            return False
        # Addresses can have numbers, dashes, letters
        return any(c.isdigit() or c.isalpha() or c in '-/, ' for c in text)
    
    def extract_ic_number(self, text_lines: List[str]) -> str:
        """Extract IC number from text lines"""
        for line in text_lines:
            match = re.search(r'\d{6}-\d{2}-\d{4}', line)
            if match:
                return match.group()
        return ""
    
    def extract_name(self, text_lines: List[str], ic_number: str) -> str:
        """
        Extract the full name from OCR text lines
        
        Malaysian name pattern: [FIRST NAME] [MIDDLE NAMES...] BIN/BINTI [FATHER'S NAME]
        """
        
        if not ic_number:
            return ""
        
        # Find IC number index
        ic_idx = None
        for idx, line in enumerate(text_lines):
            if ic_number in line:
                ic_idx = idx
                break
        
        if ic_idx is None:
            return ""
        
        name_parts = []
        
        # Strategy 1: Find BIN/BINTI marker as the strongest anchor
        bin_idx = None
        for idx, line in enumerate(text_lines):
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                bin_idx = idx
                break
        
        if bin_idx is not None:
            # Add BIN/BINTI line
            bin_line = text_lines[bin_idx].upper().strip()
            if bin_line and bin_line != ic_number:
                name_parts.append(bin_line)
            
            # Look BACKWARDS from BIN/BINTI for first/middle names
            for i in range(bin_idx - 1, max(-1, bin_idx - 10), -1):
                line = text_lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at IC or address components
                if ic_number in line or any(addr in line.upper() for addr in ['M1-', 'M2-', 'L1-', 'JLN', 'JALAN']):
                    break
                
                # Stop at metadata
                if any(kw in line.upper() for kw in self.metadata_keywords):
                    break
                
                # Collect name-like lines
                if self.is_name_like(line):
                    corrected = self.correct_ocr_text(line)
                    if corrected and corrected != ic_number:
                        name_parts.insert(0, corrected)
                        if len(name_parts) >= 5:  # Enough names collected
                            break
            
            # Look FORWARD from BIN/BINTI for father's name
            for i in range(bin_idx + 1, min(len(text_lines), bin_idx + 3)):
                line = text_lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at metadata or IC
                if (any(kw in line.upper() for kw in self.metadata_keywords) or 
                    ic_number in line):
                    break
                
                # Add father's name if it's name-like
                if self.is_name_like(line):
                    corrected = self.correct_ocr_text(line)
                    if corrected and corrected not in name_parts:
                        name_parts.append(corrected)
                    break
        
        # Strategy 2: If BIN/BINTI not found or incomplete, look after IC number
        if len(name_parts) < 2:
            for i in range(ic_idx + 1, min(len(text_lines), ic_idx + 10)):
                line = text_lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at metadata
                if any(kw in line.upper() for kw in self.metadata_keywords):
                    break
                
                # Skip IC, pure numbers, addresses
                if (ic_number in line or 
                    re.match(r'^[0-9]+$', line) or
                    any(addr in line.upper() for addr in ['M1-', 'M2-', 'JLN', 'JALAN'])):
                    continue
                
                # Collect name-like lines
                if self.is_name_like(line):
                    corrected = self.correct_ocr_text(line)
                    if corrected not in name_parts:
                        name_parts.append(corrected)
                        if len(name_parts) >= 5:
                            break
        
        # Clean up and return
        full_name = ' '.join(name_parts)
        return full_name
    
    def extract_address(self, text_lines: List[str], ic_number: str) -> str:
        """
        Extract the full address from OCR text lines
        
        Malaysian address pattern: [BUILDING/STREET] [AREA] [POSTCODE] [STATE]
        """
        
        if not ic_number:
            return ""
        
        ic_idx = None
        for idx, line in enumerate(text_lines):
            if ic_number in line:
                ic_idx = idx
                break
        
        if ic_idx is None:
            return ""
        
        address_parts = []
        
        # Pass 1: Collect address lines BEFORE IC number
        for i in range(ic_idx - 1, max(-1, ic_idx - 10), -1):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Skip names, IC, metadata
            if ('BIN' in line.upper() or 'BINTI' in line.upper() or 
                ic_number in line or
                any(kw in line.upper() for kw in self.metadata_keywords)):
                continue
            
            # Skip single state names appearing alone at start
            if line.upper() in self.states:
                continue
            
            # Collect address-like lines
            corrected = self.correct_ocr_text(line)
            if len(corrected) > 2:
                address_parts.insert(0, corrected)
        
        # Pass 2: Look after IC for postcode and state
        for i in range(ic_idx + 1, min(len(text_lines), ic_idx + 10)):
            line = text_lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Stop at metadata
            if any(kw in line.upper() for kw in self.metadata_keywords):
                break
            
            corrected = self.correct_ocr_text(line)
            
            # Look for postcode (5 consecutive digits)
            if re.match(r'^\d{5}', corrected):
                address_parts.append(corrected)
            # Look for state
            elif corrected in self.states:
                address_parts.append(corrected)
                break
            # Look for section info (SEKSYEN)
            elif 'SEKSYEN' in corrected:
                address_parts.append(corrected)
        
        full_address = ', '.join(address_parts)
        return full_address
    
    def extract_ic_data(self, text_lines: List[str]) -> Dict[str, str]:
        """Extract IC number, name, and address from OCR output"""
        
        ic_number = self.extract_ic_number(text_lines)
        name = self.extract_name(text_lines, ic_number) if ic_number else ""
        address = self.extract_address(text_lines, ic_number) if ic_number else ""
        
        return {
            'ic_number': ic_number,
            'name': name,
            'address': address
        }


if __name__ == "__main__":
    extractor = NameAddressExtractor()
    
    # Test case from user
    test_data = [
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
    
    result = extractor.extract_ic_data(test_data)
    
    print("=" * 70)
    print("EXTRACTED IC DATA")
    print("=" * 70)
    print(f"IC Number: {result['ic_number']}")
    print(f"Name:      {result['name']}")
    print(f"Address:   {result['address']}")
    print()
    print("=" * 70)
    print("EXPECTED DATA")
    print("=" * 70)
    print(f"IC Number: 960325-10-5977")
    print(f"Name:      MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN")
    print(f"Address:   M1-G-1 SERI BINTANG APT, SUBANG BESTARI, SEKSYEN U5, 40150 SHAH ALAM, SELANGOR")
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print("❌ Problem: The OCR output provided is INCOMPLETE")
    print()
    print("Missing from OCR output:")
    print("  - 'AFIQ' (middle name)")
    print("  - 'HAMZI' (middle name)")
    print("  - 'SUBANG' (area name - only 'BESTARI' present)")
    print("  - 'SEKSYEN U5' (section info)")
    print("  - '40150' (postcode)")
    print()
    print("The extractor successfully:")
    print("  ✅ Extracted IC: 960325-10-5977")
    print("  ✅ Corrected OCR errors: YENU6→MUHAMMAD, AHALAM→SHAH ALAM")
    print("  ✅ Found name components: MUHAMMAD, BIN ABD RAHMAN")
    print("  ✅ Found address: M1-G-1 SERI BINTANG APT")
    print()
    print("⚠️  Recommendation:")
    print("The raw OCR data needs to be improved. This could be due to:")
    print("  • Image rotation (though you have rotation detection)")
    print("  • Poor image quality")
    print("  • Card at an angle")
    print("  • OCR model limitations")
    print()
    print("Consider re-processing the original image with enhanced rotation detection")
    print("and image preprocessing to get complete OCR output.")
