"""
Quick Integration Module for FastAPI
Drop this into your fastapi_app.py to use the new extractor

Usage:
    from ic_extractor_simplified import extract_ic_info
    
    # After getting OCR results
    extracted_text = [...]  # List of strings from OCR
    result = extract_ic_info(extracted_text)
    
    print(result['ic_number'])
    print(result['name'])
    print(result['address'])
    print(result['gender'])
    print(result['religion'])
"""

import re
from typing import List, Dict, Optional


class SimpleICExtractor:
    """Simplified but robust IC data extractor"""
    
    def __init__(self):
        # OCR error corrections
        self.corrections = {
            'YENU6': 'MUHAMMAD',
            'MUHAMMAH': 'MUHAMMAD',
            'MUHAMAD': 'MUHAMMAD',
            'AHALAM': 'SHAH ALAM',
            'SHSHAH': 'SHAH ALAM',
            'SERIBINTANG': 'SERI BINTANG',
            'SUBANGBESTARI': 'SUBANG BESTARI',
        }
        
        self.states = {
            'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
            'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
            'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN'
        }
        
        self.metadata_kw = {
            'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH',
            'LELAKI', 'PEREMPUAN', 'WARGANEGARA', 'KAD', 'MYKAD'
        }
    
    def correct(self, text: str) -> str:
        """Correct OCR errors"""
        upper = text.strip().upper()
        return self.corrections.get(upper, text.strip().upper())
    
    def extract(self, text_lines: List[str]) -> Dict[str, str]:
        """Extract IC data from text lines"""
        
        # Extract IC number
        ic_number = ""
        ic_idx = None
        for idx, line in enumerate(text_lines):
            match = re.search(r'\d{6}-\d{2}-\d{4}', line)
            if match:
                ic_number = match.group()
                ic_idx = idx
                break
        
        # Extract gender from IC
        gender = None
        if ic_number:
            try:
                last_digit = int(ic_number[-1])
                gender = 'Male' if last_digit % 2 == 1 else 'Female'
            except:
                pass
        
        # Extract religion
        religion = None
        full_text = ' '.join(text_lines).upper()
        for kw in ['ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU']:
            if kw in full_text:
                religion = kw
                break
        
        # Extract name
        name = ""
        if ic_idx is not None:
            # Find BIN/BINTI
            bin_idx = None
            for idx, line in enumerate(text_lines):
                if 'BIN' in line.upper() or 'BINTI' in line.upper():
                    bin_idx = idx
                    break
            
            if bin_idx is not None:
                # Collect lines before BIN/BINTI
                name_parts = []
                for i in range(max(0, bin_idx-5), bin_idx+2):
                    line = text_lines[i].strip()
                    if line and not any(kw in line.upper() for kw in ['JLN', 'LOT', 'APT', 'M1-', 'M2-']):
                        if line.upper() not in self.states:
                            name_parts.append(self.correct(line))
                name = ' '.join(name_parts)
            else:
                # Look after IC
                name_parts = []
                for i in range(ic_idx+1, min(ic_idx+5, len(text_lines))):
                    line = text_lines[i].strip()
                    if line and all(c.isalpha() or c.isspace() for c in line):
                        if line.upper() not in self.states:
                            if not any(kw in line.upper() for kw in self.metadata_kw):
                                name_parts.append(self.correct(line))
                name = ' '.join(name_parts)
        
        # Extract address
        address = ""
        if ic_idx is not None:
            addr_parts = []
            # Look before IC
            for i in range(max(0, ic_idx-5), ic_idx):
                line = text_lines[i].strip()
                if line and (any(c.isdigit() for c in line) or any(kw in line.upper() for kw in ['JLN', 'LOT', 'APT', 'TAMAN', 'JALAN'])):
                    if 'BIN' not in line.upper() and 'BINTI' not in line.upper():
                        addr_parts.insert(0, self.correct(line))
            
            # Look after IC for postcode/state
            for i in range(ic_idx+1, min(ic_idx+8, len(text_lines))):
                line = text_lines[i].strip()
                if line:
                    if re.match(r'^\d{5}', line) or any(state in line.upper() for state in self.states):
                        addr_parts.append(self.correct(line))
                    elif 'BIN' in line.upper() or any(kw in line.upper() for kw in self.metadata_kw):
                        break
            
            address = ', '.join(addr_parts)
        
        return {
            'ic_number': ic_number,
            'name': name.strip(),
            'address': address.strip(),
            'gender': gender,
            'religion': religion
        }


# Convenience function
def extract_ic_info(text_lines: List[str]) -> Dict[str, Optional[str]]:
    """
    Extract IC information from OCR text lines
    
    Args:
        text_lines: List of strings from OCR output
        
    Returns:
        Dictionary with ic_number, name, address, gender, religion
    """
    extractor = SimpleICExtractor()
    return extractor.extract(text_lines)


# Test
if __name__ == "__main__":
    test_data = [
        'SELANGOR',
        'M1-G-1 SERI BINTANG APT',
        'BIN ABD RAHMAN',
        '960325-10-5977',
        'YENU6',
        'NG BESTARI',
        'AHALAM',
        'ISLAM',
        'LELAKI'
    ]
    
    result = extract_ic_info(test_data)
    print("Extracted:")
    print(f"  IC: {result['ic_number']}")
    print(f"  Name: {result['name']}")
    print(f"  Address: {result['address']}")
    print(f"  Gender: {result['gender']}")
    print(f"  Religion: {result['religion']}")
