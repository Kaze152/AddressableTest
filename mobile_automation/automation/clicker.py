"""
Auto Clicker

Implements automated clicking functionality with various recognition methods.
"""

import time
import numpy as np
from typing import Optional, Union, List, Tuple, Dict, Any
from enum import Enum

from ..device.device_controller import DeviceController
from ..recognition.template_matcher import TemplateMatchers, MatchResult
from ..recognition.color_detector import ColorDetector, ColorMatch
from ..automation.screen_capture import ScreenCapture
from ..utils.logger import Logger
from ..utils.config import Config

# Optional OCR import
try:
    from ..recognition.ocr_recognizer import OCRRecognizer, OCRResult
    OCR_AVAILABLE = True
except ImportError:
    OCRRecognizer = None
    OCRResult = None
    OCR_AVAILABLE = False


class ClickType(Enum):
    """Click type enumeration"""
    TAP = "tap"
    LONG_PRESS = "long_press"
    DOUBLE_TAP = "double_tap"
    SWIPE = "swipe"


class ActionResult:
    """Represents the result of an automated action"""
    
    def __init__(self, success: bool, message: str, click_position: Optional[Tuple[int, int]] = None,
                 screenshot_before: Optional[np.ndarray] = None, screenshot_after: Optional[np.ndarray] = None):
        self.success = success
        self.message = message
        self.click_position = click_position
        self.screenshot_before = screenshot_before
        self.screenshot_after = screenshot_after
        self.timestamp = time.time()
    
    def __repr__(self):
        return f"ActionResult(success={self.success}, position={self.click_position}, message='{self.message}')"


class AutoClicker:
    """Automated clicking with multiple recognition methods"""
    
    def __init__(self, device: DeviceController, config: Optional[dict] = None):
        """
        Initialize auto clicker
        
        Args:
            device: Device controller instance
            config: Configuration dictionary
        """
        self.device = device
        self.logger = Logger.get_logger("AutoClicker")
        self.config = Config()
        
        # Get configuration
        auto_config = self.config.get_automation_config()
        if config:
            auto_config.update(config)
        
        self.retry_attempts = auto_config.get('retry_attempts', 3)
        self.retry_delay = auto_config.get('retry_delay', 1.0)
        self.action_delay = auto_config.get('action_delay', 0.5)
        self.screenshot_before_action = auto_config.get('screenshot_before_action', True)
        self.screenshot_after_action = auto_config.get('screenshot_after_action', False)
        
        # Initialize recognition modules
        self.template_matcher = TemplateMatchers()
        self.ocr_recognizer = OCRRecognizer() if OCR_AVAILABLE else None
        self.color_detector = ColorDetector()
        self.screen_capture = ScreenCapture(device)
        
        if not OCR_AVAILABLE:
            self.logger.warning("OCR functionality not available (paddleocr not installed)")
        
        self.logger.info("Auto clicker initialized")
    
    def click_template(self, template: Union[str, np.ndarray], click_type: ClickType = ClickType.TAP,
                      threshold: Optional[float] = None, template_name: str = "",
                      offset: Tuple[int, int] = (0, 0), duration: float = 1.0) -> ActionResult:
        """
        Click on template match
        
        Args:
            template: Template image or path to template file
            click_type: Type of click action
            threshold: Confidence threshold for matching
            template_name: Name identifier for the template
            offset: Offset from match center (x, y)
            duration: Duration for long press or swipe
            
        Returns:
            ActionResult: Result of the action
        """
        self.logger.info(f"Attempting to click template: {template_name}")
        
        screenshot_before = None
        screenshot_after = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Take screenshot before action
                screenshot_before = self.screen_capture.capture() if self.screenshot_before_action else None
                
                # Find template match
                matches = self.template_matcher.match_template(
                    screenshot_before or self.screen_capture.capture(), 
                    template, 
                    threshold, 
                    template_name
                )
                
                if not matches:
                    if attempt < self.retry_attempts - 1:
                        self.logger.warning(f"Template not found, retrying in {self.retry_delay}s (attempt {attempt + 1})")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return ActionResult(
                            False, 
                            f"Template '{template_name}' not found after {self.retry_attempts} attempts",
                            screenshot_before=screenshot_before
                        )
                
                # Use best match
                best_match = matches[0]
                click_x = best_match.center_x + offset[0]
                click_y = best_match.center_y + offset[1]
                
                # Perform click action
                success = self._perform_click_action(click_type, click_x, click_y, duration)
                
                # Take screenshot after action
                if self.screenshot_after_action:
                    time.sleep(0.5)  # Wait for UI to update
                    screenshot_after = self.screen_capture.capture()
                
                if success:
                    self.logger.info(f"Successfully clicked template '{template_name}' at ({click_x}, {click_y})")
                    return ActionResult(
                        True,
                        f"Template '{template_name}' clicked successfully",
                        (click_x, click_y),
                        screenshot_before,
                        screenshot_after
                    )
                else:
                    return ActionResult(
                        False,
                        f"Failed to perform click action on template '{template_name}'",
                        (click_x, click_y),
                        screenshot_before,
                        screenshot_after
                    )
                
            except Exception as e:
                self.logger.error(f"Error in template click attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    return ActionResult(
                        False,
                        f"Template click failed with error: {str(e)}",
                        screenshot_before=screenshot_before
                    )
    
    def click_text(self, text: str, click_type: ClickType = ClickType.TAP,
                   exact_match: bool = False, ignore_case: bool = True,
                   confidence_threshold: Optional[float] = None,
                   offset: Tuple[int, int] = (0, 0), duration: float = 1.0) -> ActionResult:
        """
        Click on text found by OCR
        
        Args:
            text: Text to search for
            click_type: Type of click action
            exact_match: Whether to use exact matching
            ignore_case: Whether to ignore case differences
            confidence_threshold: Minimum OCR confidence threshold
            offset: Offset from text center (x, y)
            duration: Duration for long press or swipe
            
        Returns:
            ActionResult: Result of the action
        """
        if not OCR_AVAILABLE or self.ocr_recognizer is None:
            return ActionResult(
                False,
                "OCR functionality not available. Install paddleocr to use text recognition."
            )
        
        self.logger.info(f"Attempting to click text: '{text}'")
        
        screenshot_before = None
        screenshot_after = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Take screenshot before action
                screenshot_before = self.screen_capture.capture() if self.screenshot_before_action else None
                
                # Find text
                text_results = self.ocr_recognizer.find_text(
                    screenshot_before or self.screen_capture.capture(),
                    text,
                    exact_match,
                    ignore_case,
                    confidence_threshold
                )
                
                if not text_results:
                    if attempt < self.retry_attempts - 1:
                        self.logger.warning(f"Text '{text}' not found, retrying in {self.retry_delay}s (attempt {attempt + 1})")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return ActionResult(
                            False,
                            f"Text '{text}' not found after {self.retry_attempts} attempts",
                            screenshot_before=screenshot_before
                        )
                
                # Use first match (highest confidence)
                text_match = text_results[0]
                click_x = text_match.center_x + offset[0]
                click_y = text_match.center_y + offset[1]
                
                # Perform click action
                success = self._perform_click_action(click_type, click_x, click_y, duration)
                
                # Take screenshot after action
                if self.screenshot_after_action:
                    time.sleep(0.5)  # Wait for UI to update
                    screenshot_after = self.screen_capture.capture()
                
                if success:
                    self.logger.info(f"Successfully clicked text '{text}' at ({click_x}, {click_y})")
                    return ActionResult(
                        True,
                        f"Text '{text}' clicked successfully",
                        (click_x, click_y),
                        screenshot_before,
                        screenshot_after
                    )
                else:
                    return ActionResult(
                        False,
                        f"Failed to perform click action on text '{text}'",
                        (click_x, click_y),
                        screenshot_before,
                        screenshot_after
                    )
                
            except Exception as e:
                self.logger.error(f"Error in text click attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    return ActionResult(
                        False,
                        f"Text click failed with error: {str(e)}",
                        screenshot_before=screenshot_before
                    )
    
    def click_color(self, color: str, click_type: ClickType = ClickType.TAP,
                   min_area: float = 100.0, offset: Tuple[int, int] = (0, 0),
                   duration: float = 1.0) -> ActionResult:
        """
        Click on color region
        
        Args:
            color: Color name to search for
            click_type: Type of click action
            min_area: Minimum area threshold for color detection
            offset: Offset from color center (x, y)
            duration: Duration for long press or swipe
            
        Returns:
            ActionResult: Result of the action
        """
        self.logger.info(f"Attempting to click color: '{color}'")
        
        screenshot_before = None
        screenshot_after = None
        
        for attempt in range(self.retry_attempts):
            try:
                # Take screenshot before action
                screenshot_before = self.screen_capture.capture() if self.screenshot_before_action else None
                
                # Find color regions
                color_matches = self.color_detector.detect_color(
                    screenshot_before or self.screen_capture.capture(),
                    color,
                    min_area
                )
                
                if not color_matches:
                    if attempt < self.retry_attempts - 1:
                        self.logger.warning(f"Color '{color}' not found, retrying in {self.retry_delay}s (attempt {attempt + 1})")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return ActionResult(
                            False,
                            f"Color '{color}' not found after {self.retry_attempts} attempts",
                            screenshot_before=screenshot_before
                        )
                
                # Use largest color region
                color_match = color_matches[0]
                click_x = color_match.center_x + offset[0]
                click_y = color_match.center_y + offset[1]
                
                # Perform click action
                success = self._perform_click_action(click_type, click_x, click_y, duration)
                
                # Take screenshot after action
                if self.screenshot_after_action:
                    time.sleep(0.5)  # Wait for UI to update
                    screenshot_after = self.screen_capture.capture()
                
                if success:
                    self.logger.info(f"Successfully clicked color '{color}' at ({click_x}, {click_y})")
                    return ActionResult(
                        True,
                        f"Color '{color}' clicked successfully",
                        (click_x, click_y),
                        screenshot_before,
                        screenshot_after
                    )
                else:
                    return ActionResult(
                        False,
                        f"Failed to perform click action on color '{color}'",
                        (click_x, click_y),
                        screenshot_before,
                        screenshot_after
                    )
                
            except Exception as e:
                self.logger.error(f"Error in color click attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    return ActionResult(
                        False,
                        f"Color click failed with error: {str(e)}",
                        screenshot_before=screenshot_before
                    )
    
    def click_coordinates(self, x: int, y: int, click_type: ClickType = ClickType.TAP,
                         duration: float = 1.0) -> ActionResult:
        """
        Click at specific coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            click_type: Type of click action
            duration: Duration for long press or swipe
            
        Returns:
            ActionResult: Result of the action
        """
        self.logger.info(f"Attempting to click coordinates: ({x}, {y})")
        
        screenshot_before = None
        screenshot_after = None
        
        try:
            # Take screenshot before action
            screenshot_before = self.screen_capture.capture() if self.screenshot_before_action else None
            
            # Perform click action
            success = self._perform_click_action(click_type, x, y, duration)
            
            # Take screenshot after action
            if self.screenshot_after_action:
                time.sleep(0.5)  # Wait for UI to update
                screenshot_after = self.screen_capture.capture()
            
            if success:
                self.logger.info(f"Successfully clicked coordinates ({x}, {y})")
                return ActionResult(
                    True,
                    f"Coordinates ({x}, {y}) clicked successfully",
                    (x, y),
                    screenshot_before,
                    screenshot_after
                )
            else:
                return ActionResult(
                    False,
                    f"Failed to perform click action at coordinates ({x}, {y})",
                    (x, y),
                    screenshot_before,
                    screenshot_after
                )
            
        except Exception as e:
            self.logger.error(f"Error clicking coordinates: {str(e)}")
            return ActionResult(
                False,
                f"Coordinate click failed with error: {str(e)}",
                (x, y),
                screenshot_before
            )
    
    def _perform_click_action(self, click_type: ClickType, x: int, y: int, duration: float = 1.0) -> bool:
        """
        Perform the actual click action on device
        
        Args:
            click_type: Type of click action
            x: X coordinate
            y: Y coordinate
            duration: Duration for long press or swipe
            
        Returns:
            bool: True if action was performed successfully
        """
        try:
            if click_type == ClickType.TAP:
                self.device.click(x, y)
            elif click_type == ClickType.LONG_PRESS:
                self.device.long_press(x, y, duration)
            elif click_type == ClickType.DOUBLE_TAP:
                self.device.click(x, y)
                time.sleep(0.1)
                self.device.click(x, y)
            elif click_type == ClickType.SWIPE:
                # For swipe, we need start and end coordinates
                # This is a simple implementation, more complex swipe logic can be added
                self.device.swipe(x, y, x, y, duration)
            
            # Wait after action
            time.sleep(self.action_delay)
            return True
            
        except Exception as e:
            self.logger.error(f"Error performing {click_type.value} action: {str(e)}")
            return False
    
    def swipe_to_find_template(self, template: Union[str, np.ndarray], 
                              swipe_direction: str = "down", max_swipes: int = 5,
                              swipe_distance: int = 500, template_name: str = "") -> ActionResult:
        """
        Swipe to find template
        
        Args:
            template: Template image or path to template file
            swipe_direction: Direction to swipe ("up", "down", "left", "right")
            max_swipes: Maximum number of swipes
            swipe_distance: Distance to swipe in pixels
            template_name: Name identifier for the template
            
        Returns:
            ActionResult: Result of the action
        """
        self.logger.info(f"Swiping to find template: {template_name}")
        
        screen_width, screen_height = self.device.get_screen_size()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        for swipe_count in range(max_swipes):
            # Check if template is visible
            screenshot = self.screen_capture.capture()
            matches = self.template_matcher.match_template(screenshot, template, template_name=template_name)
            
            if matches:
                # Found template, click on it
                best_match = matches[0]
                return self.click_coordinates(best_match.center_x, best_match.center_y)
            
            # Perform swipe
            if swipe_direction.lower() == "down":
                start_y = center_y - swipe_distance // 2
                end_y = center_y + swipe_distance // 2
                self.device.swipe(center_x, start_y, center_x, end_y)
            elif swipe_direction.lower() == "up":
                start_y = center_y + swipe_distance // 2
                end_y = center_y - swipe_distance // 2
                self.device.swipe(center_x, start_y, center_x, end_y)
            elif swipe_direction.lower() == "right":
                start_x = center_x - swipe_distance // 2
                end_x = center_x + swipe_distance // 2
                self.device.swipe(start_x, center_y, end_x, center_y)
            elif swipe_direction.lower() == "left":
                start_x = center_x + swipe_distance // 2
                end_x = center_x - swipe_distance // 2
                self.device.swipe(start_x, center_y, end_x, center_y)
            
            time.sleep(1)  # Wait for animation
        
        return ActionResult(
            False,
            f"Template '{template_name}' not found after {max_swipes} swipes"
        )
    
    def wait_and_click_template(self, template: Union[str, np.ndarray], 
                               timeout: float = 10.0, check_interval: float = 1.0,
                               template_name: str = "") -> ActionResult:
        """
        Wait for template to appear and click it
        
        Args:
            template: Template image or path to template file
            timeout: Maximum time to wait in seconds
            check_interval: Interval between checks in seconds
            template_name: Name identifier for the template
            
        Returns:
            ActionResult: Result of the action
        """
        self.logger.info(f"Waiting for template to appear: {template_name}")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            screenshot = self.screen_capture.capture()
            matches = self.template_matcher.match_template(screenshot, template, template_name=template_name)
            
            if matches:
                best_match = matches[0]
                return self.click_coordinates(best_match.center_x, best_match.center_y)
            
            time.sleep(check_interval)
        
        return ActionResult(
            False,
            f"Template '{template_name}' did not appear within {timeout} seconds"
        )
    
    def execute_action_sequence(self, actions: List[Dict[str, Any]]) -> List[ActionResult]:
        """
        Execute a sequence of actions
        
        Args:
            actions: List of action dictionaries
            
        Returns:
            List[ActionResult]: Results of all actions
        """
        self.logger.info(f"Executing action sequence with {len(actions)} actions")
        
        results = []
        
        for i, action in enumerate(actions):
            self.logger.info(f"Executing action {i + 1}/{len(actions)}: {action.get('type', 'unknown')}")
            
            action_type = action.get('type')
            
            if action_type == 'click_template':
                result = self.click_template(
                    action['template'],
                    ClickType(action.get('click_type', 'tap')),
                    action.get('threshold'),
                    action.get('template_name', ''),
                    action.get('offset', (0, 0)),
                    action.get('duration', 1.0)
                )
            elif action_type == 'click_text':
                result = self.click_text(
                    action['text'],
                    ClickType(action.get('click_type', 'tap')),
                    action.get('exact_match', False),
                    action.get('ignore_case', True),
                    action.get('confidence_threshold'),
                    action.get('offset', (0, 0)),
                    action.get('duration', 1.0)
                )
            elif action_type == 'click_color':
                result = self.click_color(
                    action['color'],
                    ClickType(action.get('click_type', 'tap')),
                    action.get('min_area', 100.0),
                    action.get('offset', (0, 0)),
                    action.get('duration', 1.0)
                )
            elif action_type == 'click_coordinates':
                result = self.click_coordinates(
                    action['x'],
                    action['y'],
                    ClickType(action.get('click_type', 'tap')),
                    action.get('duration', 1.0)
                )
            elif action_type == 'wait':
                time.sleep(action.get('duration', 1.0))
                result = ActionResult(True, f"Waited {action.get('duration', 1.0)} seconds")
            else:
                result = ActionResult(False, f"Unknown action type: {action_type}")
            
            results.append(result)
            
            # Stop sequence if action failed and stop_on_failure is True
            if not result.success and action.get('stop_on_failure', False):
                self.logger.warning(f"Action sequence stopped due to failure: {result.message}")
                break
            
            # Wait between actions
            delay = action.get('delay_after', 0)
            if delay > 0:
                time.sleep(delay)
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Action sequence completed: {success_count}/{len(results)} successful")
        
        return results