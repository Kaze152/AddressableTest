"""
Color Detector

Implements color and shape-based recognition for UI elements.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

from ..utils.logger import Logger
from ..utils.config import Config


class ColorSpace(Enum):
    """Color space enumeration"""
    BGR = "bgr"
    HSV = "hsv"
    LAB = "lab"
    RGB = "rgb"


class ShapeType(Enum):
    """Shape type enumeration"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    CONTOUR = "contour"


class ColorMatch:
    """Represents a color detection result"""
    
    def __init__(self, x: int, y: int, width: int, height: int, area: float, 
                 color_name: str = "", contour: Optional[np.ndarray] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.area = area
        self.color_name = color_name
        self.contour = contour
        self.center_x = x + width // 2
        self.center_y = y + height // 2
    
    def __repr__(self):
        return f"ColorMatch(center=({self.center_x}, {self.center_y}), area={self.area:.1f}, color='{self.color_name}')"


class ColorDetector:
    """Color and shape-based detection"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize color detector
        
        Args:
            config: Configuration dictionary for color detection
        """
        self.logger = Logger.get_logger("ColorDetector")
        self.config = Config()
        
        # Get configuration
        color_config = self.config.get_recognition_config('color_detection')
        if config:
            color_config.update(config)
        
        self.tolerance = color_config.get('tolerance', 30)
        self.blur_kernel_size = color_config.get('blur_kernel_size', 5)
        
        # Predefined color ranges in HSV
        self.color_ranges = {
            'red': [(0, 100, 100), (10, 255, 255), (160, 100, 100), (180, 255, 255)],
            'green': [(40, 100, 100), (80, 255, 255)],
            'blue': [(100, 100, 100), (130, 255, 255)],
            'yellow': [(20, 100, 100), (30, 255, 255)],
            'orange': [(10, 100, 100), (25, 255, 255)],
            'purple': [(130, 100, 100), (160, 255, 255)],
            'white': [(0, 0, 200), (180, 30, 255)],
            'black': [(0, 0, 0), (180, 255, 50)]
        }
        
        self.logger.info(f"Color detector initialized with tolerance={self.tolerance}")
    
    def detect_color(self, image: np.ndarray, color: str, 
                    min_area: float = 100.0) -> List[ColorMatch]:
        """
        Detect regions of a specific color
        
        Args:
            image: Input image in BGR format
            color: Color name (red, green, blue, yellow, orange, purple, white, black)
            min_area: Minimum area threshold for detection
            
        Returns:
            List[ColorMatch]: List of detected color regions
        """
        if color.lower() not in self.color_ranges:
            self.logger.error(f"Unknown color: {color}")
            return []
        
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Apply blur to reduce noise
            if self.blur_kernel_size > 0:
                hsv = cv2.GaussianBlur(hsv, (self.blur_kernel_size, self.blur_kernel_size), 0)
            
            # Get color range
            color_range = self.color_ranges[color.lower()]
            
            # Create mask
            if len(color_range) == 4:  # Red color has two ranges
                lower1, upper1, lower2, upper2 = color_range
                mask1 = cv2.inRange(hsv, np.array(lower1), np.array(upper1))
                mask2 = cv2.inRange(hsv, np.array(lower2), np.array(upper2))
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                lower, upper = color_range
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            matches = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area >= min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    match = ColorMatch(x, y, w, h, area, color, contour)
                    matches.append(match)
            
            # Sort by area (largest first)
            matches.sort(key=lambda x: x.area, reverse=True)
            
            self.logger.debug(f"Found {len(matches)} {color} color regions with area >= {min_area}")
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in color detection: {str(e)}")
            return []
    
    def detect_custom_color(self, image: np.ndarray, target_color: Tuple[int, int, int],
                           color_space: ColorSpace = ColorSpace.BGR, 
                           tolerance: Optional[int] = None,
                           min_area: float = 100.0) -> List[ColorMatch]:
        """
        Detect regions of a custom color
        
        Args:
            image: Input image
            target_color: Target color in the specified color space
            color_space: Color space of the target color
            tolerance: Color tolerance (uses default if None)
            min_area: Minimum area threshold
            
        Returns:
            List[ColorMatch]: List of detected color regions
        """
        if tolerance is None:
            tolerance = self.tolerance
        
        try:
            # Convert image to target color space
            if color_space == ColorSpace.HSV:
                converted_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            elif color_space == ColorSpace.LAB:
                converted_img = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            elif color_space == ColorSpace.RGB:
                converted_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:  # BGR
                converted_img = image.copy()
            
            # Apply blur to reduce noise
            if self.blur_kernel_size > 0:
                converted_img = cv2.GaussianBlur(converted_img, (self.blur_kernel_size, self.blur_kernel_size), 0)
            
            # Create color range
            lower = np.array([max(0, c - tolerance) for c in target_color])
            upper = np.array([min(255, c + tolerance) for c in target_color])
            
            # Create mask
            mask = cv2.inRange(converted_img, lower, upper)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            matches = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area >= min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    match = ColorMatch(x, y, w, h, area, f"custom_{target_color}", contour)
                    matches.append(match)
            
            # Sort by area (largest first)
            matches.sort(key=lambda x: x.area, reverse=True)
            
            self.logger.debug(f"Found {len(matches)} custom color regions with area >= {min_area}")
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in custom color detection: {str(e)}")
            return []
    
    def detect_shapes(self, image: np.ndarray, shape_type: ShapeType,
                     min_area: float = 100.0, max_area: float = float('inf')) -> List[ColorMatch]:
        """
        Detect geometric shapes in image
        
        Args:
            image: Input image
            shape_type: Type of shape to detect
            min_area: Minimum area threshold
            max_area: Maximum area threshold
            
        Returns:
            List[ColorMatch]: List of detected shapes
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            matches = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area <= area <= max_area:
                    
                    if shape_type == ShapeType.RECTANGLE:
                        if self._is_rectangle(contour):
                            x, y, w, h = cv2.boundingRect(contour)
                            match = ColorMatch(x, y, w, h, area, "rectangle", contour)
                            matches.append(match)
                    
                    elif shape_type == ShapeType.CIRCLE:
                        if self._is_circle(contour):
                            x, y, w, h = cv2.boundingRect(contour)
                            match = ColorMatch(x, y, w, h, area, "circle", contour)
                            matches.append(match)
                    
                    elif shape_type == ShapeType.TRIANGLE:
                        if self._is_triangle(contour):
                            x, y, w, h = cv2.boundingRect(contour)
                            match = ColorMatch(x, y, w, h, area, "triangle", contour)
                            matches.append(match)
                    
                    elif shape_type == ShapeType.CONTOUR:
                        x, y, w, h = cv2.boundingRect(contour)
                        match = ColorMatch(x, y, w, h, area, "contour", contour)
                        matches.append(match)
            
            # Sort by area (largest first)
            matches.sort(key=lambda x: x.area, reverse=True)
            
            self.logger.debug(f"Found {len(matches)} {shape_type.value} shapes")
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in shape detection: {str(e)}")
            return []
    
    def _is_rectangle(self, contour: np.ndarray) -> bool:
        """Check if contour is approximately rectangular"""
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        return len(approx) == 4
    
    def _is_circle(self, contour: np.ndarray) -> bool:
        """Check if contour is approximately circular"""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return False
        
        # Calculate circularity
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        return 0.7 <= circularity <= 1.3
    
    def _is_triangle(self, contour: np.ndarray) -> bool:
        """Check if contour is approximately triangular"""
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        return len(approx) == 3
    
    def detect_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """
        Detect dominant colors in image using K-means clustering
        
        Args:
            image: Input image
            k: Number of dominant colors to find
            
        Returns:
            List[Tuple[int, int, int]]: List of dominant colors in BGR format
        """
        try:
            # Reshape image to be a list of pixels
            data = image.reshape((-1, 3))
            data = np.float32(data)
            
            # Apply K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert centers to integers
            dominant_colors = [tuple(map(int, center)) for center in centers]
            
            self.logger.debug(f"Found {len(dominant_colors)} dominant colors")
            return dominant_colors
            
        except Exception as e:
            self.logger.error(f"Error in dominant color detection: {str(e)}")
            return []
    
    def get_pixel_color(self, image: np.ndarray, x: int, y: int, 
                       sample_size: int = 1) -> Tuple[int, int, int]:
        """
        Get color at specific coordinates
        
        Args:
            image: Input image
            x: X coordinate
            y: Y coordinate
            sample_size: Size of area to sample (1 for single pixel)
            
        Returns:
            Tuple[int, int, int]: Average color in BGR format
        """
        try:
            height, width = image.shape[:2]
            
            # Ensure coordinates are within bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            
            if sample_size == 1:
                # Single pixel
                color = image[y, x]
            else:
                # Sample area
                half_size = sample_size // 2
                x1 = max(0, x - half_size)
                y1 = max(0, y - half_size)
                x2 = min(width, x + half_size + 1)
                y2 = min(height, y + half_size + 1)
                
                sample_area = image[y1:y2, x1:x2]
                color = np.mean(sample_area, axis=(0, 1))
            
            return tuple(map(int, color))
            
        except Exception as e:
            self.logger.error(f"Error getting pixel color: {str(e)}")
            return (0, 0, 0)
    
    def add_custom_color_range(self, color_name: str, color_range: List):
        """
        Add custom color range
        
        Args:
            color_name: Name of the color
            color_range: Color range in HSV format
        """
        self.color_ranges[color_name.lower()] = color_range
        self.logger.info(f"Added custom color range for '{color_name}'")
    
    def draw_matches(self, image: np.ndarray, matches: List[ColorMatch],
                    color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """
        Draw color detection results on image
        
        Args:
            image: Input image
            matches: List of color matches
            color: Drawing color in BGR format
            thickness: Line thickness
            
        Returns:
            np.ndarray: Image with drawn results
        """
        result_img = image.copy()
        
        for match in matches:
            # Draw bounding rectangle
            cv2.rectangle(
                result_img,
                (match.x, match.y),
                (match.x + match.width, match.y + match.height),
                color,
                thickness
            )
            
            # Draw contour if available
            if match.contour is not None:
                cv2.drawContours(result_img, [match.contour], -1, color, thickness)
            
            # Draw center point
            cv2.circle(result_img, (match.center_x, match.center_y), 5, color, -1)
            
            # Draw label
            text = f"{match.color_name} ({match.area:.0f})"
            cv2.putText(
                result_img,
                text,
                (match.x, match.y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
        
        return result_img
    
    def save_debug_image(self, image: np.ndarray, matches: List[ColorMatch], 
                        output_path: str):
        """
        Save debug image with color detection visualization
        
        Args:
            image: Input image
            matches: List of color matches
            output_path: Path to save debug image
        """
        debug_img = self.draw_matches(image, matches)
        cv2.imwrite(output_path, debug_img)
        self.logger.debug(f"Color detection debug image saved: {output_path}")