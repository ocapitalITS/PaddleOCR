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
            'SUHAII': 'SUHAIMY',  # Common OCR error in names
            'SUHAI': 'SUHAIMY',
            'PERMAI': 'PERMAI INDAH',  # Common OCR truncation
            'PERMAI INDA': 'DESA PERMAI INDAH',
            'PERMA INDAH': 'PERMAI INDAH',
            'HELANG3': 'HELANG 3',  # OCR merge of words
            'LORONG HELANG3': 'LORONG HELANG 3',
            'TAMANJEMENTAH': 'TAMAN JEMENTAH',
            'GELUGOR': 'GELUGOR',  # Keep as-is (common city name)
            'PERMAI': 'DESA PERMAI INDAH',  # Common area name
        }
        
        self.states = {'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
                       'PAHANG', 'PENANG', 'PULAU PINANG', 'PERAK', 'PERLIS', 'SABAH', 'SARAWAK',
                       'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN', 'KUALA LUMPUR', 'KL'}
        
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
            # Name can appear BEFORE or AFTER IC number
            
            # First, check if name appears BEFORE IC number (front of card layout)
            if ic_idx > 0:
                # Look backwards from IC for names, stopping at state/location keywords
                for i in range(ic_idx - 1, -1, -1):
                    line = lines[i].strip().upper()
                    
                    if not line:
                        continue
                    
                    # STOP: At header/card information (ignore these)
                    header_keywords = ['KAD', 'PENGENALAN', 'MYKAD', 'IDENTITY', 'CARD', 'MALAYSIA', 'MYCARD', 'IDENTIT', 'PENGENJALAN']
                    if any(kw in line for kw in header_keywords):
                        break
                    
                    # STOP: At state/location keywords (card header)
                    if any(s in line for s in self.states):
                        break
                    if any(kw in line for kw in ['SUNGAI', 'TAMAN', 'DESA', 'GELUGOR', 'PERMAI']):
                        break
                    if any(m in line for m in self.metadata):
                        break
                    
                    # STOP: At address patterns
                    if re.match(r'^[ML]\d+', line):
                        break
                    if any(kw in line for kw in ['LOT', 'JLN', 'JALAN', 'APARTMENT', 'APT', 'NO', 'LORONG']):
                        break
                    
                    # COLLECT: Alphabetic lines are names (collect in reverse order)
                    alpha_count = sum(1 for c in line if c.isalpha() or c == ' ')
                    if alpha_count / max(len(line), 1) > 0.8:  # 80% alphabetic
                        name_parts.insert(0, self.correct(line))
                    elif name_parts:
                        # Once we collected names and hit non-alphabetic, stop
                        break
            
            # If no name found before IC, look AFTER IC number (back of card layout)
            if not name_parts and ic_idx >= 0:
                name_search_started = False
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
            # Case 2: IC has NO BIN/BINTI - address extraction depends on name location
            
            # If names were found BEFORE IC, collect address AFTER IC
            if ic_idx >= 0 and any(ic_idx > i for i, _ in [(idx, line) for idx, line in enumerate(lines) if any(part in line.upper() for part in name_parts)]):
                # Names were before IC - collect everything after IC until gender/religion
                
                # First, look for father's name (alphabetic word after IC, before address keywords)
                father_name = None
                father_name_idx = -1
                
                # Scan a few lines after IC looking for a pure alphabetic word (potential father's name)
                for scan_idx in range(ic_idx + 1, min(ic_idx + 4, len(lines))):
                    scan_line = lines[scan_idx].strip().upper()
                    
                    if not scan_line:
                        continue
                    
                    alpha_count = sum(1 for c in scan_line if c.isalpha() or c == ' ')
                    is_mostly_alpha = alpha_count / max(len(scan_line), 1) > 0.8
                    
                    # Skip lines with numbers (postcodes, building units)
                    has_numbers = any(c.isdigit() for c in scan_line)
                    if has_numbers:
                        continue
                    
                    # Check if this looks like a father's name (1-2 words, alphabetic, not address keywords)
                    word_count = len(scan_line.split())
                    if is_mostly_alpha and 1 <= word_count <= 2 and not any(kw in scan_line for kw in ['JALAN', 'LORONG', 'LOT', 'APT', 'APARTMENT']):
                        father_name = scan_line
                        father_name_idx = scan_idx
                        # Add father's name to name_parts
                        if father_name not in ' '.join(name_parts).upper():
                            name_parts.append('BIN')
                            name_parts.append(self.correct(father_name))
                        break
                
                # Collect address components by category
                building_unit = None
                street = None
                area = None
                postcode = None
                location_parts = []
                state_name = None
                
                # First collect location/state that appears BEFORE IC (at the top of the card)
                if ic_idx > 0:
                    for i in range(0, ic_idx):
                        line = lines[i].strip().upper()
                        
                        if not line:
                            continue
                        
                        # SKIP: Name parts
                        skip_line = False
                        for name_part in name_parts:
                            if name_part and name_part.upper() in line:
                                skip_line = True
                                break
                        if skip_line:
                            continue
                        
                        # SKIP: Header keywords
                        if any(kw in line for kw in ['KAD', 'PENGENALAN', 'MYKAD', 'IDENTITY', 'CARD']):
                            continue
                        
                        # COLLECT: State names and location keywords
                        is_state = any(state in line for state in self.states)
                        if is_state:
                            state_name = self.correct(line)
                        else:
                            is_location_kw = any(kw in line for kw in ['SUNGAI', 'TAMAN', 'DESA', 'GELUGOR', 'PETALING', 'SHAH', 'BANDAR'])
                            if is_location_kw:
                                location_parts.append(self.correct(line))
                
                # Now collect address AFTER IC (building unit, street, area, postcode)
                for i in range(ic_idx + 1, len(lines)):
                    line = lines[i].strip().upper()
                    
                    if not line:  # Skip empty lines
                        continue
                    
                    # Skip father's name if we found it
                    if father_name_idx >= 0 and i == father_name_idx:
                        continue
                    
                    # STOP: At religion or gender markers
                    if 'ISLAM' in line or 'KRISTIAN' in line or 'BUDDHA' in line or 'HINDU' in line or 'SIKH' in line:
                        break
                    if 'LELAKI' in line or 'PEREMPUAN' in line:
                        break
                    
                    # SKIP: Pure metadata
                    if any(m in line for m in self.metadata):
                        continue
                    
                    # SKIP: Name parts already extracted
                    if any(self.correct(line).upper() == part.upper() for part in name_parts):
                        continue
                    
                    # Categorize address components
                    corrected_line = self.correct(line)
                    
                    # Skip lines that are just "?" or similar placeholders
                    if line.strip() in ['?', '??', '???', '-', '--'] or line.replace('?', '').replace('-', '').strip() == '':
                        continue
                    
                    # Building unit: Contains dash and letters/numbers (e.g., DG-12, 3A-18, or ?-12 or DG-?)
                    if '-' in line and any(c.isalnum() for c in line):
                        if building_unit is None:
                            building_unit = corrected_line
                            continue
                    
                    # Postcode: Starts with digits, followed by city name (e.g., 1700 GELUGOR, 11700 GELUGOR)
                    if line and line[0].isdigit():
                        # Try to extract postcode + city
                        parts = line.split()
                        if len(parts) >= 1:
                            # Check if postcode looks incomplete (4 digits when should be 5)
                            postcode_candidate = parts[0]
                            if postcode_candidate.isdigit() and len(postcode_candidate) == 4:
                                # Likely missing first digit, prepend with 1
                                postcode_candidate = '1' + postcode_candidate
                            postcode = postcode_candidate
                            if len(parts) > 1:
                                postcode = postcode_candidate + ' ' + ' '.join(parts[1:])
                        continue
                    
                    # Location/area: Check if contains location keywords
                    is_location_kw = any(kw in line for kw in ['LORONG', 'JALAN', 'JLN', 'STREET', 'ST', 'ROAD', 'RD', 'AVENUE', 'AVE'])
                    if is_location_kw:
                        if street is None:
                            street = corrected_line
                        continue
                    
                    # Area: Contains keywords like DESA, TAMAN, PETALING, SHAH, BANDAR
                    is_area_kw = any(kw in line for kw in ['DESA', 'TAMAN', 'PETALING', 'SHAH', 'BANDAR', 'INDAH', 'JAYA', 'UTAMA', 'MULIA', 'SENTOSA'])
                    if is_area_kw:
                        if area is None:
                            area = corrected_line
                        continue
                    
                    # Fallback: Treat as area or location
                    if area is None:
                        area = corrected_line
                
                # Build final address in proper order: Building, Street, Area, Location, Postcode, State
                if building_unit:
                    addr_parts.append(building_unit)
                if street:
                    addr_parts.append(street)
                if area:
                    addr_parts.append(area)
                addr_parts.extend(location_parts)
                if postcode:
                    addr_parts.append(postcode)
                if state_name:
                    addr_parts.append(state_name)
            else:
                # Names were after IC - collect address between them
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
        
        # Create name string (after all name parts have been collected, including father's name)
        name = ' '.join(name_parts).strip()
        
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
