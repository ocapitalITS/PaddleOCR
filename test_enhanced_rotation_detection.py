"""
Test Enhanced Rotation Detection Module
Tests multiple detection techniques and accuracy improvements
"""

import cv2
import numpy as np
from pathlib import Path
from rotation_detector import EnhancedRotationDetector, quick_rotation_estimate
import os


def test_rotation_detector_basic():
    """Test basic rotation detection functionality"""
    print("=" * 60)
    print("TEST 1: Basic Rotation Detector Initialization")
    print("=" * 60)
    
    detector = EnhancedRotationDetector(debug=True)
    print("✅ Rotation detector initialized successfully")
    return detector


def test_synthetic_image_rotations(detector):
    """Test rotation detection with synthetic images"""
    print("\n" + "=" * 60)
    print("TEST 2: Synthetic Image Rotation Detection")
    print("=" * 60)
    
    # Create synthetic image with horizontal/vertical lines (like a card)
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw a rectangular "card" with borders
    cv2.rectangle(img, (50, 100), (750, 500), (0, 0, 0), 3)
    cv2.rectangle(img, (60, 110), (740, 490), (100, 100, 100), 1)
    
    # Add horizontal text-like lines
    for y in range(150, 450, 50):
        cv2.line(img, (80, y), (720, y), (0, 0, 0), 2)
    
    # Test different rotations
    test_cases = [
        (0, "Normal (0°)"),
        (90, "Rotated 90°"),
        (180, "Rotated 180°"),
        (270, "Rotated 270°"),
    ]
    
    for angle, description in test_cases:
        print(f"\nTesting: {description}")
        
        # Rotate image
        if angle == 0:
            rotated_img = img.copy()
        elif angle == 90:
            rotated_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            rotated_img = cv2.rotate(img, cv2.ROTATE_180)
        else:  # 270
            rotated_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # Detect rotation
        result = detector.detect_rotation_angle(rotated_img)
        detected_angle = result['angle']
        confidence = result['confidence']
        method = result.get('method', 'unknown')
        
        # Check if detection is correct
        is_correct = (detected_angle == angle)
        status = "✅" if is_correct else "❌"
        
        print(f"  {status} Expected: {angle}°, Detected: {detected_angle}° | "
              f"Confidence: {confidence:.1f}% | Method: {method}")
        
        # Print method details
        if result.get('details'):
            for method_name, method_result in result['details'].items():
                if method_result.get('confidence', 0) > 0:
                    print(f"    - {method_name}: {method_result['angle']}° "
                          f"(conf: {method_result['confidence']:.1f}%)")


def test_quick_estimation(detector):
    """Test quick rotation estimation"""
    print("\n" + "=" * 60)
    print("TEST 3: Quick Rotation Estimation")
    print("=" * 60)
    
    # Create test image
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 100), (750, 500), (0, 0, 0), 3)
    
    rotated_180 = cv2.rotate(img, cv2.ROTATE_180)
    
    estimated = quick_rotation_estimate(rotated_180)
    print(f"\n✅ Quick estimate for 180° rotated image: {estimated}°")
    print(f"   Expected: 180° (or close match)")


def test_real_ic_images(detector):
    """Test with real IC images if available"""
    print("\n" + "=" * 60)
    print("TEST 4: Real IC Image Testing")
    print("=" * 60)
    
    ic_dir = Path("IC")
    if not ic_dir.exists():
        print("⚠️  IC directory not found. Skipping real image tests.")
        return
    
    ic_files = list(ic_dir.glob("*.png")) + list(ic_dir.glob("*.jpg"))
    
    if not ic_files:
        print("⚠️  No IC images found in IC directory.")
        return
    
    print(f"\nFound {len(ic_files)} IC images. Testing first 3...")
    
    for idx, img_path in enumerate(ic_files[:3]):
        print(f"\n  Testing: {img_path.name}")
        
        try:
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"    ❌ Could not load image")
                continue
            
            result = detector.detect_rotation_angle(img)
            detected_angle = result['angle']
            confidence = result['confidence']
            method = result.get('method', 'unknown')
            
            print(f"    ✅ Detected: {detected_angle}° | "
                  f"Confidence: {confidence:.1f}% | Method: {method}")
            
            # Show vote distribution
            if result.get('all_votes'):
                votes = result['all_votes']
                print(f"    Votes: 0°={votes[0]:.2f}, 90°={votes[90]:.2f}, "
                      f"180°={votes[180]:.2f}, 270°={votes[270]:.2f}")
        
        except Exception as e:
            print(f"    ❌ Error processing image: {e}")


def test_edge_cases(detector):
    """Test edge cases and error handling"""
    print("\n" + "=" * 60)
    print("TEST 5: Edge Cases and Error Handling")
    print("=" * 60)
    
    # Test 1: Very small image
    print("\n  Testing very small image...")
    small_img = np.ones((50, 50, 3), dtype=np.uint8) * 255
    try:
        result = detector.detect_rotation_angle(small_img)
        print(f"    ✅ Small image handled: {result['angle']}° (confidence: {result['confidence']:.1f}%)")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 2: Grayscale image
    print("\n  Testing grayscale image...")
    gray_img = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    try:
        result = detector.detect_rotation_angle(gray_img)
        print(f"    ✅ Grayscale image handled: {result['angle']}° (confidence: {result['confidence']:.1f}%)")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 3: Blank/uniform image
    print("\n  Testing blank/uniform image...")
    blank_img = np.ones((400, 400, 3), dtype=np.uint8) * 128
    try:
        result = detector.detect_rotation_angle(blank_img)
        print(f"    ✅ Blank image handled: {result['angle']}° (confidence: {result['confidence']:.1f}%)")
    except Exception as e:
        print(f"    ❌ Error: {e}")


def test_confidence_levels(detector):
    """Test confidence scoring system"""
    print("\n" + "=" * 60)
    print("TEST 6: Confidence Scoring System")
    print("=" * 60)
    
    # Create images with varying clarity
    print("\n  Testing confidence levels with different image qualities...")
    
    # Clear image
    clear_img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.rectangle(clear_img, (50, 100), (750, 500), (0, 0, 0), 5)
    cv2.line(clear_img, (100, 150), (700, 150), (0, 0, 0), 3)
    cv2.line(clear_img, (100, 200), (700, 200), (0, 0, 0), 3)
    
    result_clear = detector.detect_rotation_angle(clear_img)
    print(f"  Clear image confidence: {result_clear['confidence']:.1f}%")
    
    # Blurry image
    blurry_img = cv2.GaussianBlur(clear_img, (7, 7), 0)
    result_blurry = detector.detect_rotation_angle(blurry_img)
    print(f"  Blurry image confidence: {result_blurry['confidence']:.1f}%")
    
    # Noisy image
    noise = np.random.randint(0, 50, clear_img.shape, dtype=np.uint8)
    noisy_img = cv2.add(clear_img, noise)
    result_noisy = detector.detect_rotation_angle(noisy_img)
    print(f"  Noisy image confidence: {result_noisy['confidence']:.1f}%")
    
    if result_clear['confidence'] >= result_blurry['confidence']:
        print("  ✅ Confidence correctly reflects image quality")
    else:
        print("  ⚠️  Confidence scoring may need adjustment")


def test_performance():
    """Test performance of rotation detection"""
    print("\n" + "=" * 60)
    print("TEST 7: Performance Testing")
    print("=" * 60)
    
    import time
    
    detector = EnhancedRotationDetector()
    
    # Create test image
    img = np.ones((800, 600, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 100), (750, 500), (0, 0, 0), 3)
    
    # Time the detection
    print("\n  Testing detection speed...")
    start_time = time.time()
    
    for _ in range(5):
        result = detector.detect_rotation_angle(img)
    
    elapsed = time.time() - start_time
    avg_time = elapsed / 5
    
    print(f"  ✅ Average detection time: {avg_time*1000:.2f}ms per image")
    print(f"  Total time for 5 images: {elapsed:.2f}s")
    
    if avg_time < 0.5:
        print("  ✅ Performance is good for real-time processing")
    else:
        print("  ⚠️  Performance could be improved for real-time processing")


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " ENHANCED ROTATION DETECTION - TEST SUITE ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # Run tests
        detector = test_rotation_detector_basic()
        test_synthetic_image_rotations(detector)
        test_quick_estimation(detector)
        test_real_ic_images(detector)
        test_edge_cases(detector)
        test_confidence_levels(detector)
        test_performance()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
