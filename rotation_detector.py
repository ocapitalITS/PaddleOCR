"""
Enhanced Rotation Detection Module for Malaysia IC OCR
Provides intelligent image rotation detection using multiple techniques:
- Hough Line detection for card edges
- Contour analysis for rectangular shapes
- Text orientation detection
- Confidence-based rotation selection
"""

import cv2
import numpy as np
import math
from typing import Tuple, Dict, List, Optional


class EnhancedRotationDetector:
    """
    Advanced rotation detection for Malaysia IC cards using multiple techniques
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the rotation detector
        
        Args:
            debug: Enable debug output for visualization
        """
        self.debug = debug
    
    def detect_rotation_angle(self, image: np.ndarray) -> Dict:
        """
        Detect the rotation angle of the image using multiple techniques
        
        Args:
            image: Input image as numpy array (BGR or RGB)
            
        Returns:
            Dictionary with:
            - 'angle': Detected rotation angle in degrees (0, 90, 180, 270)
            - 'confidence': Confidence score (0-100)
            - 'method': Which detection method was most reliable
            - 'details': Detailed scores from each method
        """
        
        if len(image.shape) == 2:
            img_gray = image
        else:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Run multiple detection methods
        results = {
            'hough_lines': self._detect_by_hough_lines(image, img_gray),
            'contours': self._detect_by_contours(image, img_gray),
            'edge_distribution': self._detect_by_edge_distribution(img_gray),
            'text_orientation': self._detect_by_text_orientation(image, img_gray),
        }
        
        # Compile results
        return self._combine_detection_results(results)
    
    def _detect_by_hough_lines(self, image: np.ndarray, img_gray: np.ndarray) -> Dict:
        """
        Detect rotation using Hough line transform
        IC cards have strong horizontal/vertical edges
        """
        try:
            # Apply edge detection
            edges = cv2.Canny(img_gray, 50, 150)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
            
            if lines is None or len(lines) < 3:
                return {'confidence': 0, 'angle': 0, 'reason': 'insufficient_lines'}
            
            # Extract angles from lines
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle_deg = np.degrees(theta)
                # Normalize to 0-180
                if angle_deg > 90:
                    angle_deg = 180 - angle_deg
                angles.append(angle_deg)
            
            # Find dominant angle clusters
            angles = np.array(angles)
            
            # Look for angles close to 0 (horizontal) and 90 (vertical)
            horizontal_lines = np.sum((angles < 10) | (angles > 80))
            vertical_lines = np.sum((angles >= 40) & (angles <= 50)) + np.sum((angles > 85) & (angles < 95))
            
            # Calculate rotation angle based on line distribution
            median_angle = np.median(angles)
            
            # Determine which standard angle (0, 90, 180, 270) is closest
            angle_map = {
                0: np.sum((angles < 15) | (angles > 75)),  # Score for 0° rotation
                90: np.sum((angles >= 40) & (angles <= 50)),  # Score for 90° rotation
            }
            
            best_angle = max(angle_map, key=angle_map.get)
            confidence = min(100, (angle_map[best_angle] / len(angles)) * 100)
            
            return {
                'confidence': confidence,
                'angle': best_angle,
                'median_angle': float(median_angle),
                'line_count': len(lines),
                'reason': 'hough_lines'
            }
            
        except Exception as e:
            return {'confidence': 0, 'angle': 0, 'error': str(e)}
    
    def _detect_by_contours(self, image: np.ndarray, img_gray: np.ndarray) -> Dict:
        """
        Detect rotation by finding card contour and its orientation
        """
        try:
            # Threshold to get binary image
            _, binary = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) == 0:
                return {'confidence': 0, 'angle': 0, 'reason': 'no_contours'}
            
            # Find largest contour (likely the card)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # Minimum area check - card should be reasonably large
            if area < (image.shape[0] * image.shape[1] * 0.1):
                return {'confidence': 0, 'angle': 0, 'reason': 'contour_too_small'}
            
            # Fit rectangle to contour
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]  # Angle in degrees
            
            # Normalize angle: PaddleOCR works best with 0, 90, 180, 270
            # minAreaRect returns angle in range (-90, 0]
            if angle < -45:
                detected_angle = 270
                angle_confidence = abs(angle + 90) / 45
            else:
                detected_angle = 0
                angle_confidence = abs(angle) / 45
            
            # Aspect ratio check - IC card is typically wider than tall
            width, height = rect[1]
            aspect_ratio = width / height if height > 0 else 0
            
            # Aspect ratio confidence (IC cards typically 1.5-1.8 ratio)
            if 1.2 < aspect_ratio < 2.0:
                aspect_confidence = 90
            else:
                aspect_confidence = 50
            
            overall_confidence = (angle_confidence * 0.6 + 0.4 * aspect_confidence)
            
            return {
                'confidence': min(100, overall_confidence * 100),
                'angle': detected_angle,
                'rect_angle': float(angle),
                'aspect_ratio': aspect_ratio,
                'area': area,
                'reason': 'contour_analysis'
            }
            
        except Exception as e:
            return {'confidence': 0, 'angle': 0, 'error': str(e)}
    
    def _detect_by_edge_distribution(self, img_gray: np.ndarray) -> Dict:
        """
        Detect rotation by analyzing edge distribution patterns
        """
        try:
            # Apply Sobel edge detection
            sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Calculate magnitude
            magnitude = np.sqrt(sobelx**2 + sobely**2)
            
            # Calculate edge direction
            direction = np.arctan2(sobely, sobelx)
            
            # Analyze edge direction distribution in quadrants
            h, w = img_gray.shape
            
            # Count edges in different directions for each quadrant
            directions_deg = np.degrees(direction) % 180
            
            # Look for dominant horizontal edges (0-20 or 160-180 degrees)
            horizontal_edges = np.sum((directions_deg < 20) | (directions_deg > 160))
            
            # Look for dominant vertical edges (70-90 degrees)
            vertical_edges = np.sum((directions_deg >= 70) & (directions_deg <= 90))
            
            # Normalized scores
            total_edges = np.sum(magnitude > 50)  # Count significant edges
            
            if total_edges == 0:
                return {'confidence': 0, 'angle': 0, 'reason': 'no_edges'}
            
            h_score = horizontal_edges / total_edges if total_edges > 0 else 0
            v_score = vertical_edges / total_edges if total_edges > 0 else 0
            
            # Determine angle
            if h_score > v_score and h_score > 0.3:
                detected_angle = 0
                confidence = min(100, h_score * 100)
            elif v_score > h_score and v_score > 0.3:
                detected_angle = 90
                confidence = min(100, v_score * 100)
            else:
                detected_angle = 0
                confidence = 30
            
            return {
                'confidence': confidence,
                'angle': detected_angle,
                'h_score': float(h_score),
                'v_score': float(v_score),
                'reason': 'edge_distribution'
            }
            
        except Exception as e:
            return {'confidence': 0, 'angle': 0, 'error': str(e)}
    
    def _detect_by_text_orientation(self, image: np.ndarray, img_gray: np.ndarray) -> Dict:
        """
        Detect rotation by analyzing text orientation (horizontal vs vertical lines of text)
        """
        try:
            # Apply morphological operations to enhance text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            morph = cv2.morphologyEx(img_gray, cv2.MORPH_CLOSE, kernel)
            
            # Use Canny edge detection
            edges = cv2.Canny(morph, 30, 100)
            
            # Apply Hough line transform with different parameters for text detection
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 50)
            
            if lines is None or len(lines) < 2:
                return {'confidence': 0, 'angle': 0, 'reason': 'insufficient_text_lines'}
            
            # Analyze line angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle_deg = np.degrees(theta)
                if angle_deg > 90:
                    angle_deg = 180 - angle_deg
                angles.append(angle_deg)
            
            angles = np.array(angles)
            
            # Create histogram of angles
            hist_horizontal = np.sum((angles < 15) | (angles > 75))  # ~0°
            hist_vertical = np.sum((angles >= 40) & (angles <= 50))  # ~45° (for rotated 90°)
            hist_other = np.sum((angles >= 20) & (angles < 40) | (angles > 50) & (angles <= 75))
            
            # Dominant angle detection
            if hist_horizontal > hist_vertical and hist_horizontal > hist_other:
                detected_angle = 0
                confidence = (hist_horizontal / len(angles)) * 100
            elif hist_vertical > hist_horizontal and hist_vertical > hist_other:
                detected_angle = 90
                confidence = (hist_vertical / len(angles)) * 100
            else:
                # Try to detect 180 or 270 degree rotation
                detected_angle = 0
                confidence = 40
            
            return {
                'confidence': min(100, confidence),
                'angle': detected_angle,
                'hist_h': hist_horizontal,
                'hist_v': hist_vertical,
                'line_count': len(lines),
                'reason': 'text_orientation'
            }
            
        except Exception as e:
            return {'confidence': 0, 'angle': 0, 'error': str(e)}
    
    def _combine_detection_results(self, results: Dict) -> Dict:
        """
        Combine results from all detection methods using weighted voting
        """
        
        # Weight for each method (higher = more important)
        weights = {
            'hough_lines': 0.25,
            'contours': 0.35,
            'edge_distribution': 0.15,
            'text_orientation': 0.25,
        }
        
        # Collect votes
        angle_votes = {0: 0, 90: 0, 180: 0, 270: 0}
        total_confidence = 0
        best_method = None
        highest_confidence = 0
        
        for method_name, weight in weights.items():
            result = results[method_name]
            
            if result['confidence'] > 0:
                angle = result.get('angle', 0)
                confidence = result.get('confidence', 0)
                
                # Add weighted vote
                angle_votes[angle] += weight * (confidence / 100)
                total_confidence += weight
                
                # Track best method
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_method = method_name
        
        # Determine final angle
        if total_confidence > 0:
            final_angle = max(angle_votes, key=angle_votes.get)
            final_confidence = (angle_votes[final_angle] / total_confidence) * 100
        else:
            final_angle = 0
            final_confidence = 0
        
        return {
            'angle': final_angle,
            'confidence': min(100, final_confidence),
            'method': best_method,
            'details': results,
            'all_votes': angle_votes,
        }
    
    def correct_image_rotation(self, image: np.ndarray, angle: int) -> np.ndarray:
        """
        Rotate image to correct orientation
        
        Args:
            image: Input image
            angle: Angle to rotate (should be 0, 90, 180, or 270)
            
        Returns:
            Rotated image
        """
        angle = angle % 360  # Normalize angle
        
        if angle == 0:
            return image
        elif angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            # For arbitrary angles, use affine transformation
            h, w = image.shape[:2]
            center = (w / 2, h / 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, rotation_matrix, (w, h))
            return rotated


def quick_rotation_estimate(image: np.ndarray) -> int:
    """
    Quick estimation of rotation angle without full analysis
    Useful for preprocessing before detailed detection
    
    Args:
        image: Input image
        
    Returns:
        Estimated rotation angle (0, 90, 180, or 270)
    """
    
    if len(image.shape) == 2:
        img_gray = image
    else:
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Quick contour analysis
    try:
        _, binary = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            if angle < -45:
                return 270
            else:
                return 0
    except:
        pass
    
    return 0
