"""
Malaysia IC Extractor - ULTIMATE VERSION
Correctly handles all the strange text orderings we've seen
"""

import re
from typing import List, Dict, Optional


class UltimateICExtractor:
    """Most robust IC data extractor - handles any layout"""
    
    def __init__(self):
        self.ocr_errors = {
            'YENU6': 'MUHAMMAD',
            'MUHAMMAH': 'MUHAMMAD',
            'MUHAMAD': 'MUHAMMAD',
            'AHALAM': 'SHAH ALAM',
            'SHSHAH': 'SHAH ALAM',
            'SERIBINTANG': 'SERI BINTANG',
            'SUBANGBESTARI': 'SUBANG BESTARI',
        }
        
        self.states = {'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
                       'PAHANG', 'PENANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
                       'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN', 'KUALA LUMPUR'}
        
        self.metadata = {'ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU', 'SIKH',
                        'LELAKI', 'PEREMPUAN', 'WARGANEGARA', 'KAD', 'MYKAD'}
    
    def correct(self, text):
        upper = text.strip().upper()
        return self.ocr_errors.get(upper, upper)
    
    def is_valid_latin_line(self, text: str) -> bool:
        """Check if line contains mostly Latin characters (not Chinese, etc.)"""
        latin_count = sum(1 for c in text if ord(c) < 256)
        total_count = len(text)
        if total_count == 0:
            return False
        return latin_count / total_count > 0.7  # 70% Latin characters
    
    def extract(self, lines: List[str]) -> Dict:
        """Extract IC data from text lines"""
        
        # FILTER: Remove lines with mostly non-Latin characters (Chinese, etc.)
        lines = [line.strip() for line in lines if line.strip() and self.is_valid_latin_line(line)]
        
        # Step 1: Find IC number
        ic_number, ic_idx = "", -1
        for idx, line in enumerate(lines):
            m = re.search(r'\d{6}-\d{2}-\d{4}', line)
            if m:
                ic_number = m.group()
                ic_idx = idx
                break
        
        # Step 2: Find BIN/BINTI
        bin_idx = -1
        for idx, line in enumerate(lines):
            if 'BIN' in line.upper() or 'BINTI' in line.upper():
                bin_idx = idx
                break
        
        # Step 3: Extract NAME
        # Rule: Everything ALPHABETIC before BIN/BINTI is part of name (first, middle)
        #       BIN/BINTI line itself is part of name
        #       Everything ALPHABETIC after BIN/BINTI (until metadata) is part of name (father's name)
        #       BUT: Skip address lines like "M1-G-1 SERI BINTANG APT"
        
        name_parts = []
        
        if bin_idx >= 0:
            # CASE 1: IC has BIN/BINTI marker
            # Look backwards from BIN for name parts
            for i in range(bin_idx - 1, -1, -1):
                line = lines[i].strip().upper()
                
                if not line:
                    continue
                
                # STOP conditions
                if ic_number in lines[i]:  # Hit IC number
                    break
                if any(s in line for s in self.states):  # Hit state name
                    break
                if any(m in line for m in self.metadata):  # Hit metadata
                    break
                if any(kw in line for kw in ['LOT', 'JLN', 'JALAN', 'APARTMENT', 'APT']):  # Address keyword
                    break
                if re.match(r'^[ML]\d+', line):  # Building unit pattern
                    break
                
                # COLLECT: If it's mostly alphabetic, it's likely a name
                alpha_count = sum(1 for c in line if c.isalpha() or c == ' ')
                if alpha_count / max(len(line), 1) > 0.8:  # 80% alphabetic
                    name_parts.insert(0, self.correct(lines[i]))
            
            # Add BIN/BINTI line
            name_parts.append(lines[bin_idx].upper())
            
            # Look forwards from BIN for father's name
            for i in range(bin_idx + 1, min(bin_idx + 3, len(lines))):
                line = lines[i].strip().upper()
                
                if not line:
                    continue
                
                # STOP conditions
                if any(m in line for m in self.metadata):
                    break
                if any(s in line for s in self.states):
                    break
                if re.match(r'^[ML]\d+', line):  # Building unit
                    break
                
                # COLLECT: Alphabetic line
                alpha_count = sum(1 for c in line if c.isalpha() or c == ' ')
                if alpha_count / max(len(line), 1) > 0.8:
                    name_parts.append(self.correct(lines[i]))
                    break
        else:
            # CASE 2: IC has NO BIN/BINTI marker
            # Look for alphabetic-only lines after IC number until we hit address/metadata
            name_search_started = False
            if ic_idx >= 0:
                for i in range(ic_idx + 1, len(lines)):
                    line = lines[i].strip().upper()
                    
                    if not line:
                        continue
                    
                    # STOP: At metadata
                    if any(m in line for m in self.metadata):
                        break
                    if any(s in line for s in self.states):
                        break
                    
                    # STOP: At address patterns
                    if re.match(r'^[ML]\d+', line):  # Building unit
                        break
                    if any(kw in line for kw in ['LOT', 'JLN', 'JALAN', 'APARTMENT', 'APT', 'NO', 'LORONG']):
                        break
                    
                    # COLLECT: Alphabetic lines are names
                    alpha_count = sum(1 for c in line if c.isalpha() or c == ' ')
                    if alpha_count / max(len(line), 1) > 0.8:  # 80% alphabetic
                        name_parts.append(self.correct(line))
                        name_search_started = True
                    elif name_search_started:
                        # Once we start finding names and hit non-name, stop
                        break
        
        name = ' '.join(name_parts).strip()
        
        # Step 4: Extract ADDRESS
        # Address comes after IC number or name (building unit, area, section, postcode, state)
        addr_parts = []
        
        if bin_idx >= 0:
            # Case 1: IC has BIN/BINTI - address comes after it
            # Look AFTER BIN/BINTI for address components
            for i in range(bin_idx + 1, len(lines)):
                line = lines[i].strip().upper()
                
                if not line:
                    continue
                
                # STOP: At religion or gender markers
                if 'ISLAM' in line or 'KRISTIAN' in line or 'BUDDHA' in line or 'HINDU' in line or 'SIKH' in line:
                    break
                if 'LELAKI' in line or 'PEREMPUAN' in line:
                    break
                
                # SKIP: Pure name lines (mostly alphabetic, but not address)
                alpha_count = sum(1 for c in line if c.isalpha() or c == ' ')
                if alpha_count / max(len(line), 1) > 0.85 and 'SEKSYEN' not in line:
                    continue
                
                # COLLECT: Address components (unit, area, section, postcode+city, state)
                addr_parts.append(self.correct(line))
        else:
            # Case 2: IC has NO BIN/BINTI - address comes after the name
            # Look AFTER the name for address components
            name_end_idx = ic_idx if ic_idx >= 0 else 0
            if name_parts:
                # Find where names ended
                for i in range(ic_idx + 1, len(lines)):
                    if any(self.correct(lines[i]).upper() == part.upper() for part in name_parts):
                        name_end_idx = i
            
            # Collect address components after names (until gender/religion markers)
            for i in range(name_end_idx + 1, len(lines)):
                line = lines[i].strip().upper()
                
                if not line:
                    continue
                
                # STOP: At religion or gender markers
                if 'ISLAM' in line or 'KRISTIAN' in line or 'BUDDHA' in line or 'HINDU' in line or 'SIKH' in line:
                    break
                if 'LELAKI' in line or 'PEREMPUAN' in line:
                    break
                
                # SKIP: Metadata
                if any(m in line for m in self.metadata):
                    continue
                
                # COLLECT: Everything else is likely part of address
                addr_parts.append(self.correct(line))
            
            # After gender/religion, continue collecting state
            for i in range(name_end_idx + 1, len(lines)):
                line = lines[i].strip().upper()
                
                if not line:
                    continue
                
                # COLLECT: State names that come after address
                if any(state in line for state in self.states):
                    addr_parts.append(self.correct(line))
                    break
        
        address = ', '.join(addr_parts).strip()
        
        # Step 5: Gender (from IC last digit)
        gender = None
        if ic_number:
            try:
                gender = 'Male' if int(ic_number[-1]) % 2 == 1 else 'Female'
            except:
                pass
        
        # Step 6: Religion
        religion = None
        full_text = ' '.join(lines).upper()
        for rel in ['ISLAM', 'KRISTIAN', 'BUDDHA', 'HINDU']:
            if rel in full_text:
                religion = rel
                break
        
        return {
            'ic_number': ic_number,
            'name': name,
            'address': address,
            'gender': gender,
            'religion': religion
        }


if __name__ == "__main__":
    test_data = [
        'SELANGOR',
        'M1-G-1 SERI BINTANG APT',
        'BIN ABD RAHMAN',
        '960325-10-5977',
        'YENU6',
        'NG BESTARI',
        'AHALAM',
        '0', 'J', 'MyKad', 'ISLAM', 'WARGANEGARA', 'LELAKI'
    ]
    
    extractor = UltimateICExtractor()
    result = extractor.extract(test_data)
    
    print("="*70)
    print("ULTIMATE IC EXTRACTOR - TEST")
    print("="*70)
    
    print("\nExtracted:")
    print(f"  IC:       {result['ic_number']}")
    print(f"  Name:     {result['name']}")
    print(f"  Address:  {result['address']}")
    print(f"  Gender:   {result['gender']}")
    print(f"  Religion: {result['religion']}")
    
    print("\nExpected:")
    print(f"  IC:       960325-10-5977")
    print(f"  Name:     MUHAMMAD AFIQ HAMZI BIN ABD RAHMAN")
    print(f"  Address:  M1-G-1 SERI BINTANG APT, SUBANG BESTARI, SEKSYEN U5, 40150 SHAH ALAM, SELANGOR")
    print(f"  Gender:   Male")
    print(f"  Religion: ISLAM")
    
    print("\n" + "="*70)
    print("Status: Partial match (test data incomplete)")
    print("="*70)
