"""
Template Matcher

Implements OpenCV-based template matching for UI element recognition.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
from pathlib import Path

from ..utils.logger import Logger
from ..utils.config import Config


class MatchResult:
    """Represents a template matching result"""
    
    def __init__(self, x: int, y: int, width: int, height: int, confidence: float, template_name: str = ""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.template_name = template_name
        self.center_x = x + width // 2
        self.center_y = y + height // 2
    
    def __repr__(self):
        return f"MatchResult(center=({self.center_x}, {self.center_y}), confidence={self.confidence:.3f}, template='{self.template_name}')"


class TemplateMatchers:
    """OpenCV template matching implementation"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize template matcher
        
        Args:
            config: Configuration dictionary for template matching
        """
        self.logger = Logger.get_logger("TemplateMatchers")
        self.config = Config()
        
        # Get configuration
        tm_config = self.config.get_recognition_config('template_matching')
        if config:
            tm_config.update(config)
        
        self.threshold = tm_config.get('threshold', 0.8)
        self.method = getattr(cv2, tm_config.get('method', 'TM_CCOEFF_NORMED'))
        self.multi_scale = tm_config.get('multi_scale', True)
        self.scale_range = tm_config.get('scale_range', [0.8, 1.2])
        self.scale_step = tm_config.get('scale_step', 0.1)
        
        self.logger.info(f"Template matcher initialized with threshold={self.threshold}")
    
    def load_template(self, template_path: str) -> np.ndarray:
        """
        Load template image from file
        
        Args:
            template_path: Path to template image file
            
        Returns:
            np.ndarray: Template image in BGR format
        """
        template_file = Path(template_path)
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        template = cv2.imread(str(template_file))
        if template is None:
            raise ValueError(f"Could not load template image: {template_path}")
        
        self.logger.debug(f"Loaded template: {template_path}, shape: {template.shape}")
        return template
    
    def match_template(self, screen: np.ndarray, template: Union[str, np.ndarray], 
                      threshold: Optional[float] = None, template_name: str = "") -> List[MatchResult]:
        """
        Find template matches in screen image
        
        Args:
            screen: Screenshot image in BGR format
            template: Template image (np.ndarray) or path to template file (str)
            threshold: Confidence threshold (uses default if None)
            template_name: Name identifier for the template
            
        Returns:
            List[MatchResult]: List of matching results sorted by confidence
        """
        if threshold is None:
            threshold = self.threshold
        
        # Load template if path provided
        if isinstance(template, str):
            template_img = self.load_template(template)
            if not template_name:
                template_name = Path(template).stem
        else:
            template_img = template
        
        if screen is None or template_img is None:
            return []
        
        matches = []
        
        if self.multi_scale:
            # Multi-scale template matching
            matches = self._multi_scale_match(screen, template_img, threshold, template_name)
        else:
            # Single-scale template matching
            matches = self._single_scale_match(screen, template_img, threshold, template_name)
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.debug(f"Found {len(matches)} matches for template '{template_name}' with threshold {threshold}")
        return matches
    
    def _single_scale_match(self, screen: np.ndarray, template: np.ndarray, 
                           threshold: float, template_name: str) -> List[MatchResult]:
        """Perform single-scale template matching"""
        template_height, template_width = template.shape[:2]
        screen_height, screen_width = screen.shape[:2]
        
        # Check if template is larger than screen
        if template_height > screen_height or template_width > screen_width:
            self.logger.warning(f"Template {template_name} is larger than screen")
            return []
        
        try:
            # Perform template matching
            result = cv2.matchTemplate(screen, template, self.method)
            
            # Find locations where matching exceeds threshold
            locations = np.where(result >= threshold)
            
            matches = []
            for pt in zip(*locations[::-1]):  # Switch x and y coordinates
                confidence = result[pt[1], pt[0]]
                match = MatchResult(
                    x=pt[0],
                    y=pt[1],
                    width=template_width,
                    height=template_height,
                    confidence=float(confidence),
                    template_name=template_name
                )
                matches.append(match)
            
            # Remove overlapping matches (Non-Maximum Suppression)
            matches = self._non_max_suppression(matches)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in template matching: {str(e)}")
            return []
    
    def _multi_scale_match(self, screen: np.ndarray, template: np.ndarray, 
                          threshold: float, template_name: str) -> List[MatchResult]:
        """Perform multi-scale template matching"""
        all_matches = []
        
        # Generate scale factors
        scale_min, scale_max = self.scale_range
        scales = np.arange(scale_min, scale_max + self.scale_step, self.scale_step)
        
        for scale in scales:
            # Resize template
            new_width = int(template.shape[1] * scale)
            new_height = int(template.shape[0] * scale)
            
            if new_width <= 0 or new_height <= 0:
                continue
                
            scaled_template = cv2.resize(template, (new_width, new_height))
            
            # Perform matching with scaled template
            matches = self._single_scale_match(screen, scaled_template, threshold, f"{template_name}_scale_{scale:.2f}")
            
            # Adjust match results for scale
            for match in matches:
                match.template_name = template_name
                
            all_matches.extend(matches)
        
        # Remove overlapping matches across all scales
        all_matches = self._non_max_suppression(all_matches)
        
        return all_matches
    
    def _non_max_suppression(self, matches: List[MatchResult], overlap_threshold: float = 0.3) -> List[MatchResult]:
        """
        Remove overlapping matches using Non-Maximum Suppression
        
        Args:
            matches: List of match results
            overlap_threshold: Overlap threshold for suppression
            
        Returns:
            List[MatchResult]: Filtered matches
        """
        if not matches:
            return []
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        filtered_matches = []
        
        for match in matches:
            # Check if this match overlaps significantly with any already selected match
            is_overlapping = False
            
            for selected_match in filtered_matches:
                overlap = self._calculate_overlap(match, selected_match)
                if overlap > overlap_threshold:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered_matches.append(match)
        
        return filtered_matches
    
    def _calculate_overlap(self, match1: MatchResult, match2: MatchResult) -> float:
        """Calculate overlap ratio between two matches"""
        # Calculate intersection
        x1 = max(match1.x, match2.x)
        y1 = max(match1.y, match2.y)
        x2 = min(match1.x + match1.width, match2.x + match2.width)
        y2 = min(match1.y + match1.height, match2.y + match2.height)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection_area = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        area1 = match1.width * match1.height
        area2 = match2.width * match2.height
        union_area = area1 + area2 - intersection_area
        
        if union_area == 0:
            return 0.0
        
        return intersection_area / union_area
    
    def find_best_match(self, screen: np.ndarray, template: Union[str, np.ndarray], 
                       threshold: Optional[float] = None, template_name: str = "") -> Optional[MatchResult]:
        """
        Find the best (highest confidence) template match
        
        Args:
            screen: Screenshot image in BGR format
            template: Template image or path to template file
            threshold: Confidence threshold
            template_name: Name identifier for the template
            
        Returns:
            MatchResult or None: Best match result if found
        """
        matches = self.match_template(screen, template, threshold, template_name)
        return matches[0] if matches else None
    
    def draw_matches(self, screen: np.ndarray, matches: List[MatchResult], 
                    color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """
        Draw bounding boxes around matches
        
        Args:
            screen: Screenshot image
            matches: List of match results
            color: Rectangle color in BGR format
            thickness: Rectangle line thickness
            
        Returns:
            np.ndarray: Image with drawn matches
        """
        result_img = screen.copy()
        
        for match in matches:
            # Draw rectangle
            cv2.rectangle(
                result_img,
                (match.x, match.y),
                (match.x + match.width, match.y + match.height),
                color,
                thickness
            )
            
            # Draw center point
            cv2.circle(result_img, (match.center_x, match.center_y), 5, color, -1)
            
            # Draw confidence text
            text = f"{match.confidence:.2f}"
            if match.template_name:
                text = f"{match.template_name}: {text}"
            
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
    
    def save_debug_image(self, screen: np.ndarray, matches: List[MatchResult], 
                        output_path: str, template_name: str = ""):
        """
        Save debug image with match visualization
        
        Args:
            screen: Screenshot image
            matches: List of match results
            output_path: Path to save debug image
            template_name: Template name for filename
        """
        debug_img = self.draw_matches(screen, matches)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if template_name:
            output_file = output_file.parent / f"{template_name}_debug.png"
        
        cv2.imwrite(str(output_file), debug_img)
        self.logger.debug(f"Debug image saved: {output_file}")