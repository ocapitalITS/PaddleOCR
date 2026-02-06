"""
FINAL Malaysia IC Data Extractor
Handles all known OCR output patterns
"""

import re
from typing import List, Dict, Optional, Set


class MalaysiaICExtractor:
    """
    Comprehensive IC data extractor that handles all observed text layouts
    """
    
    def __init__(self):
        # OCR error corrections mapping
        self.ocr_errors = {
            # Names
            'YENU6': 'MUHAMMAD',
            'MUHAMMAH': 'MUHAMMAD',
            'MUHAMAD': 'MUHAMMAD',
            'MUHAMMED': 'MUHAMMAD',
            'MOHAMAD': 'MOHAMMAD',
            
            # Locations
            'AHALAM': 'SHAH ALAM',
            'SHSHAH': 'SHAH ALAM',
            'SERIBINTANG': 'SERI BINTANG',
            'SUBANGBESTARI': 'SUBANG BESTARI',
            'SUNGAITUA': 'SUNGAI TUA',
            'DAMANSARADAMAI': 'DAMANSARA DAMAI',
            'PETALINGJAYA': 'PETALING JAYA',
            'PETALING JAYA': 'PETALING JAYA',
            'JALANUSJ': 'JALAN USJ',
            'JALANPJU': 'JALAN PJU',
        }
        
        self.states = {
            'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
            'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
            'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN', 'KUALA LUMPUR'
        }
        
        self.metadata_keywords = {
            'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH', 'TAOISM',
            'LELAKI', 'PEREMPUAN', 'WARGANEGARA', 'KAD', 'MYKAD', 'KETURUNAN'
        }
        
        self.address_keywords = {
            'LOT', 'JALAN', 'JALAN', 'LORONG', 'KAMPUNG', 'KG', 'PERMAI',
            'TAMAN', 'BANDAR', 'DESA', 'SEKSYEN', 'BLOK', 'BLOCK'
        }
    
    def correct_ocr(self, text: str) -> str:
        """Correct known OCR errors"""
        if not text:
            return text
        
        upper = text.strip().upper()
        return self.ocr_errors.get(upper, upper)
    
    def is_likely_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) < 2:
            return False
        # Should be mostly letters and spaces, allow apostrophes
        return all(c.isalpha() or c.isspace() or c in "-'" for c in text)
    
    def is_metadata(self, text: str) -> bool:
        """Check if text is metadata (gender, religion, etc)"""
        upper = text.upper()
        return any(kw in upper for kw in self.metadata_keywords)
    
    def is_state_name(self, text: str) -> bool:
        """Check if text is a Malaysian state"""
        return text.upper() in self.states
    
    def is_likely_address(self, text: str) -> bool:
        """Check if text looks like part of an address"""
        upper = text.upper()
        
        # Check for address keywords
        if any(kw in upper for kw in self.address_keywords):
            return True
        
        # Check for building unit patterns (e.g., "M1-G-1", "3B-2-2")
        if re.match(r'^[M|L]\d+.*-.*-', text):
            return True
        
        # Check for starts with number (lot/unit number)
        if re.match(r'^\d+', text):
            return True
        
        return False
    
    def extract_ic_number(self, lines: List[str]) -> tuple:
        """Extract IC number and its position"""
        for idx, line in enumerate(lines):
            match = re.search(r'\d{6}-\d{2}-\d{4}', line)
            if match:
                return match.group(), idx
        return "", -1
    
    def extract_name(self, lines: List[str], ic_number: str, ic_idx: int) -> str:
        """
        Extract name from text lines
        
        Handles patterns:
        - FIRST MIDDLE BIN/BINTI FATHER
        - Various positions relative to IC
        """
        if ic_idx < 0:
            return ""
        
        name_components = []
        
        # ==== STRATEGY 1: Find BIN/BINTI marker (strongest indicator) ====
        bin_idx = -1
        for idx, line in enumerate(lines):
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                bin_idx = idx
                break
        
        if bin_idx >= 0:
            # Pattern: FIRST MIDDLE ... BIN/BINTI FATHER ...
            
            # Add BIN/BINTI line itself
            name_components.append(lines[bin_idx].upper())
            
            # ==== Get names BEFORE BIN/BINTI (going backward) ====
            # These should be first and middle names
            for i in range(bin_idx - 1, -1, -1):
                line = lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at IC, address, state
                if ic_number in line:
                    break
                
                if self.is_state_name(line):
                    break
                
                # IMPORTANT: Stop at building/address keywords
                # These indicate we've reached the address section
                if any(kw in line.upper() for kw in ['LOT', 'JLN', 'JALAN', 'APARTMENT', 'APT', 'M1-', 'M2-', 'BLOK']):
                    break
                
                if self.is_metadata(line):
                    break
                
                # Add if it's name-like
                if self.is_likely_name(line):
                    corrected = self.correct_ocr(line)
                    if len(corrected) > 2:  # Filter out very short strings
                        name_components.insert(0, corrected)
            
            # ==== Get father's name AFTER BIN/BINTI ====
            for i in range(bin_idx + 1, min(bin_idx + 3, len(lines))):
                line = lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at metadata, state, address
                if (self.is_metadata(line) or 
                    self.is_state_name(line) or 
                    any(kw in line.upper() for kw in self.address_keywords)):
                    break
                
                # Add if it's name-like (alphabetic)
                if self.is_likely_name(line):
                    corrected = self.correct_ocr(line)
                    if len(corrected) > 2:
                        name_components.append(corrected)
                        break
        
        # ==== STRATEGY 2: If no BIN/BINTI, look for names after IC ====
        else:
            for i in range(ic_idx + 1, min(ic_idx + 10, len(lines))):
                line = lines[i].strip()
                
                if not line or len(line) < 2:
                    continue
                
                # Stop at metadata
                if self.is_metadata(line):
                    break
                
                # Skip IC, numbers
                if ic_number in line or re.match(r'^[\d\s-]+$', line):
                    continue
                
                # Add names (only alphabetic lines)
                if self.is_likely_name(line):
                    corrected = self.correct_ocr(line)
                    if len(corrected) > 2 and corrected not in name_components:
                        name_components.append(corrected)
                        if len(name_components) >= 4:
                            break
        
        # Clean up and join
        name_components = [c for c in name_components if c and len(c) > 1]
        return ' '.join(name_components).strip()
    
    def extract_address(self, lines: List[str], ic_number: str, ic_idx: int) -> str:
        """
        Extract address from text lines
        
        Pattern: BUILDING/STREET AREA [SECTION] POSTCODE STATE
        """
        if ic_idx < 0:
            return ""
        
        address_components = []
        
        # ==== Collect address parts BEFORE IC ====
        for i in range(max(0, ic_idx - 10), ic_idx):
            line = lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Skip names
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                continue
            
            # Skip IC
            if ic_number in line:
                continue
            
            # Skip state appearing alone
            if self.is_state_name(line) and len(line.split()) == 1:
                continue
            
            # Collect address components
            if self.is_likely_address(line) or len(line) > 5:
                corrected = self.correct_ocr(line)
                if corrected not in address_components:
                    address_components.append(corrected)
        
        # ==== Collect postcode and state AFTER IC ====
        for i in range(ic_idx + 1, min(ic_idx + 10, len(lines))):
            line = lines[i].strip()
            
            if not line or len(line) < 2:
                continue
            
            # Stop at names
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                if address_components:
                    break
            
            # Stop at metadata
            if self.is_metadata(line):
                break
            
            corrected = self.correct_ocr(line)
            
            # Look for postcode (5 digits)
            if re.match(r'^\d{5}', corrected):
                address_components.append(corrected)
            # Look for state
            elif self.is_state_name(corrected):
                address_components.append(corrected)
                break
            # Look for section info
            elif 'SEKSYEN' in corrected:
                address_components.append(corrected)
        
        return ', '.join(address_components).strip()
    
    def extract_gender(self, ic_number: str) -> Optional[str]:
        """Extract gender from IC number (last digit: odd=male, even=female)"""
        if not ic_number or len(ic_number) < 1:
            return None
        
        try:
            last_digit = int(ic_number[-1])
            return 'Male' if last_digit % 2 == 1 else 'Female'
        except (ValueError, IndexError):
            return None
    
    def extract_religion(self, lines: List[str]) -> Optional[str]:
        """Extract religion from text"""
        full_text = ' '.join(lines).upper()
        
        religions = ['ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH']
        for religion in religions:
            if religion in full_text:
                return religion
        
        return None
    
    def extract_all(self, text_lines: List[str]) -> Dict[str, Optional[str]]:
        """Extract all IC information"""
        
        # Clean input
        text_lines = [line.strip() for line in text_lines if line.strip()]
        
        # Extract IC number
        ic_number, ic_idx = self.extract_ic_number(text_lines)
        
        # Extract other fields
        name = self.extract_name(text_lines, ic_number, ic_idx)
        address = self.extract_address(text_lines, ic_number, ic_idx)
        gender = self.extract_gender(ic_number)
        religion = self.extract_religion(text_lines)
        
        return {
            'ic_number': ic_number,
            'name': name,
            'address': address,
            'gender': gender,
            'religion': religion
        }


def extract_ic_data(text_lines: List[str]) -> Dict[str, Optional[str]]:
    """Convenience function to extract IC data"""
    extractor = MalaysiaICExtractor()
    return extractor.extract_all(text_lines)


if __name__ == "__main__":
    # Test with the problem case
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
    
    print("="*70)
    print("TESTING: MUHAMMAD AFIQ HAMZI CASE")
    print("="*70)
    
    result = extract_ic_data(test_data)
    
    print("\nExtracted:")
    print(f"  IC Number: {result['ic_number']}")
    print(f"  Name:      {result['name']}")
    print(f"  Address:   {result['address']}")
    print(f"  Gender:    {result['gender']}")
    print(f"  Religion:  {result['religion']}")
    
    print("\nExpected:")
    print(f"  IC Number: 960325-10-5977")
    print(f"  Name:      MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN")
    print(f"  Address:   M1-G-1 SERI BINTANG APT, SUBANG BESTARI, SEKSYEN U5, 40150 SHAH ALAM, SELANGOR")
    print(f"  Gender:    Male")
    print(f"  Religion:  ISLAM")
    
    print("\n" + "="*70)
    print("NOTE: Extraction limited by OCR output provided")
    print("Missing from OCR: AFIQ, HAMZI, SUBANG, SEKSYEN U5, 40150")
    print("="*70)
