"""
OCR Recognizer

Implements PaddleOCR-based text recognition for UI elements.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import re

try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("paddleocr is required for OCR functionality. Install with: pip install paddleocr")

from ..utils.logger import Logger
from ..utils.config import Config


class OCRResult:
    """Represents an OCR recognition result"""
    
    def __init__(self, text: str, bbox: List[List[int]], confidence: float):
        """
        Initialize OCR result
        
        Args:
            text: Recognized text
            bbox: Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            confidence: Recognition confidence score
        """
        self.text = text
        self.bbox = bbox
        self.confidence = confidence
        
        # Calculate center point and rectangle
        self._calculate_bounds()
    
    def _calculate_bounds(self):
        """Calculate center point and bounding rectangle"""
        x_coords = [point[0] for point in self.bbox]
        y_coords = [point[1] for point in self.bbox]
        
        self.x = min(x_coords)
        self.y = min(y_coords)
        self.width = max(x_coords) - self.x
        self.height = max(y_coords) - self.y
        self.center_x = self.x + self.width // 2
        self.center_y = self.y + self.height // 2
    
    def __repr__(self):
        return f"OCRResult(text='{self.text}', center=({self.center_x}, {self.center_y}), confidence={self.confidence:.3f})"


class OCRRecognizer:
    """PaddleOCR-based text recognition"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize OCR recognizer
        
        Args:
            config: Configuration dictionary for OCR
        """
        self.logger = Logger.get_logger("OCRRecognizer")
        self.config = Config()
        
        # Get configuration
        ocr_config = self.config.get_recognition_config('ocr')
        if config:
            ocr_config.update(config)
        
        self.language = ocr_config.get('language', 'ch')
        self.use_gpu = ocr_config.get('use_gpu', False)
        self.confidence_threshold = ocr_config.get('confidence_threshold', 0.7)
        self.enable_mkldnn = ocr_config.get('enable_mkldnn', True)
        
        # Initialize PaddleOCR
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.language,
                use_gpu=self.use_gpu,
                enable_mkldnn=self.enable_mkldnn,
                show_log=False
            )
            self.logger.info(f"OCR initialized with language={self.language}, GPU={self.use_gpu}")
        except Exception as e:
            self.logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
            raise
    
    def recognize_text(self, image: np.ndarray, 
                      confidence_threshold: Optional[float] = None) -> List[OCRResult]:
        """
        Recognize text in image
        
        Args:
            image: Input image in BGR format
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[OCRResult]: List of recognized text results
        """
        if confidence_threshold is None:
            confidence_threshold = self.confidence_threshold
        
        try:
            # Perform OCR
            results = self.ocr.ocr(image, cls=True)
            
            ocr_results = []
            
            if results and results[0]:
                for line in results[0]:
                    if line:
                        bbox = line[0]
                        text_info = line[1]
                        text = text_info[0]
                        confidence = text_info[1]
                        
                        # Filter by confidence threshold
                        if confidence >= confidence_threshold:
                            ocr_result = OCRResult(text, bbox, confidence)
                            ocr_results.append(ocr_result)
            
            self.logger.debug(f"OCR found {len(ocr_results)} text results with confidence >= {confidence_threshold}")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"Error in OCR recognition: {str(e)}")
            return []
    
    def find_text(self, image: np.ndarray, target_text: str, 
                  exact_match: bool = False, ignore_case: bool = True,
                  confidence_threshold: Optional[float] = None) -> List[OCRResult]:
        """
        Find specific text in image
        
        Args:
            image: Input image in BGR format
            target_text: Text to search for
            exact_match: Whether to use exact matching
            ignore_case: Whether to ignore case differences
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[OCRResult]: List of matching text results
        """
        all_results = self.recognize_text(image, confidence_threshold)
        matching_results = []
        
        search_text = target_text.lower() if ignore_case else target_text
        
        for result in all_results:
            result_text = result.text.lower() if ignore_case else result.text
            
            if exact_match:
                if result_text == search_text:
                    matching_results.append(result)
            else:
                if search_text in result_text:
                    matching_results.append(result)
        
        self.logger.debug(f"Found {len(matching_results)} matches for text '{target_text}'")
        return matching_results
    
    def find_text_pattern(self, image: np.ndarray, pattern: str,
                         confidence_threshold: Optional[float] = None) -> List[OCRResult]:
        """
        Find text matching a regular expression pattern
        
        Args:
            image: Input image in BGR format
            pattern: Regular expression pattern
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[OCRResult]: List of matching text results
        """
        all_results = self.recognize_text(image, confidence_threshold)
        matching_results = []
        
        try:
            regex = re.compile(pattern)
            
            for result in all_results:
                if regex.search(result.text):
                    matching_results.append(result)
                    
        except re.error as e:
            self.logger.error(f"Invalid regex pattern '{pattern}': {str(e)}")
            return []
        
        self.logger.debug(f"Found {len(matching_results)} matches for pattern '{pattern}'")
        return matching_results
    
    def find_numbers(self, image: np.ndarray, 
                    confidence_threshold: Optional[float] = None) -> List[OCRResult]:
        """
        Find numeric text in image
        
        Args:
            image: Input image in BGR format
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[OCRResult]: List of numeric text results
        """
        return self.find_text_pattern(image, r'\d+', confidence_threshold)
    
    def find_phone_numbers(self, image: np.ndarray,
                          confidence_threshold: Optional[float] = None) -> List[OCRResult]:
        """
        Find phone numbers in image
        
        Args:
            image: Input image in BGR format
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[OCRResult]: List of phone number results
        """
        # Pattern for various phone number formats
        phone_pattern = r'1[3-9]\d{9}|(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
        return self.find_text_pattern(image, phone_pattern, confidence_threshold)
    
    def preprocess_image(self, image: np.ndarray, enhance_contrast: bool = True,
                        denoise: bool = True, resize_factor: float = 1.0) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: Input image
            enhance_contrast: Whether to enhance contrast
            denoise: Whether to apply denoising
            resize_factor: Scale factor for resizing
            
        Returns:
            np.ndarray: Preprocessed image
        """
        processed_img = image.copy()
        
        # Resize image
        if resize_factor != 1.0:
            new_width = int(processed_img.shape[1] * resize_factor)
            new_height = int(processed_img.shape[0] * resize_factor)
            processed_img = cv2.resize(processed_img, (new_width, new_height))
        
        # Convert to grayscale
        if len(processed_img.shape) == 3:
            processed_img = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        if enhance_contrast:
            processed_img = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(processed_img)
        
        # Denoise
        if denoise:
            processed_img = cv2.fastNlMeansDenoising(processed_img)
        
        # Convert back to BGR for PaddleOCR
        processed_img = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
        
        return processed_img
    
    def recognize_in_region(self, image: np.ndarray, x: int, y: int, width: int, height: int,
                           confidence_threshold: Optional[float] = None) -> List[OCRResult]:
        """
        Recognize text in a specific region of the image
        
        Args:
            image: Input image
            x: Region x coordinate
            y: Region y coordinate
            width: Region width
            height: Region height
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[OCRResult]: List of recognized text results in the region
        """
        # Extract region
        region = image[y:y+height, x:x+width]
        
        # Recognize text in region
        results = self.recognize_text(region, confidence_threshold)
        
        # Adjust coordinates to original image
        for result in results:
            result.x += x
            result.y += y
            result.center_x += x
            result.center_y += y
            
            # Adjust bbox coordinates
            for point in result.bbox:
                point[0] += x
                point[1] += y
        
        return results
    
    def draw_results(self, image: np.ndarray, results: List[OCRResult],
                    color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """
        Draw OCR results on image
        
        Args:
            image: Input image
            results: List of OCR results
            color: Drawing color in BGR format
            thickness: Line thickness
            
        Returns:
            np.ndarray: Image with drawn results
        """
        result_img = image.copy()
        
        for result in results:
            # Draw bounding box
            bbox_points = np.array(result.bbox, dtype=np.int32)
            cv2.polylines(result_img, [bbox_points], True, color, thickness)
            
            # Draw center point
            cv2.circle(result_img, (result.center_x, result.center_y), 5, color, -1)
            
            # Draw text
            text = f"{result.text} ({result.confidence:.2f})"
            cv2.putText(
                result_img,
                text,
                (result.x, result.y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
        
        return result_img
    
    def save_debug_image(self, image: np.ndarray, results: List[OCRResult], 
                        output_path: str):
        """
        Save debug image with OCR visualization
        
        Args:
            image: Input image
            results: List of OCR results
            output_path: Path to save debug image
        """
        debug_img = self.draw_results(image, results)
        cv2.imwrite(output_path, debug_img)
        self.logger.debug(f"OCR debug image saved: {output_path}")
    
    def get_text_statistics(self, results: List[OCRResult]) -> Dict[str, Any]:
        """
        Get statistics about OCR results
        
        Args:
            results: List of OCR results
            
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        if not results:
            return {
                'total_texts': 0,
                'average_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'total_characters': 0
            }
        
        confidences = [result.confidence for result in results]
        total_chars = sum(len(result.text) for result in results)
        
        return {
            'total_texts': len(results),
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'total_characters': total_chars,
            'texts': [result.text for result in results]
        }