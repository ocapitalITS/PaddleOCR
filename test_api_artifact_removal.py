"""Test the artifact removal feature in the API"""
import requests
import json
import time

# Wait for server to be ready
time.sleep(10)

# Test images that have known issues
test_images = [
    ('IC/ic_front-3.jpg', 'ic_front-3.jpg'),
]

for image_path, name in test_images:
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                'http://localhost:8000/api/ocr',
                files=files,
                timeout=300  # 5 minutes timeout
            )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            if 'data' in result:
                data = result['data']
                print(f"\nExtracted Data:")
                print(f"  Name: {data.get('name')}")
                print(f"  Gender: {data.get('gender')}")
                print(f"  IC Number: {data.get('ic_number')}")
                print(f"  Religion: {data.get('religion')}")
                print(f"  Nationality: {data.get('nationality')}")
                print(f"  State: {data.get('state')}")
                
                # Check if FAETAY or other artifacts are present
                name_field = data.get('name', '')
                artifacts_to_check = ['FAETAY', 'ROTI', 'ACAR', 'TARIK', 'NASI', 'RICING', 'GORENG']
                
                print(f"\nArtifact Check:")
                for artifact in artifacts_to_check:
                    if artifact in name_field:
                        print(f"  ❌ Found artifact '{artifact}' in name field!")
                    
                if not any(artifact in name_field for artifact in artifacts_to_check):
                    print(f"  ✓ No known artifacts found in name field")
            else:
                print(f"Error: No data in response")
                print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result}")
    
    except Exception as e:
        print(f"Error during test: {e}")

print("\n" + "="*60)
print("Testing completed!")
