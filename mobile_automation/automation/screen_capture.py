"""
Screen Capture Utility

Provides screen capture functionality with various options and formats.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from pathlib import Path
import time
from datetime import datetime

from ..device.device_controller import DeviceController
from ..utils.logger import Logger
from ..utils.config import Config


class ScreenCapture:
    """Screen capture utility for mobile devices"""
    
    def __init__(self, device: DeviceController, config: Optional[dict] = None):
        """
        Initialize screen capture
        
        Args:
            device: Device controller instance
            config: Configuration dictionary
        """
        self.device = device
        self.logger = Logger.get_logger("ScreenCapture")
        self.config = Config()
        
        # Get configuration
        auto_config = self.config.get_automation_config()
        if config:
            auto_config.update(config)
        
        self.screenshot_before_action = auto_config.get('screenshot_before_action', True)
        self.screenshot_after_action = auto_config.get('screenshot_after_action', False)
        self.save_screenshots = auto_config.get('save_screenshots', False)
        self.screenshot_dir = auto_config.get('screenshot_dir', 'screenshots')
        
        # Create screenshot directory
        if self.save_screenshots:
            Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Screen capture initialized")
    
    def capture(self, save_file: Optional[str] = None) -> np.ndarray:
        """
        Capture screen from device
        
        Args:
            save_file: Optional file path to save screenshot
            
        Returns:
            np.ndarray: Screenshot image in BGR format
        """
        if not self.device.is_device_connected():
            raise RuntimeError("Device not connected")
        
        try:
            # Capture screenshot
            screenshot = self.device.screenshot()
            
            # Save screenshot if requested
            if save_file:
                self._save_screenshot(screenshot, save_file)
            elif self.save_screenshots:
                # Auto-save with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"screenshot_{timestamp}.png"
                save_path = Path(self.screenshot_dir) / filename
                self._save_screenshot(screenshot, str(save_path))
            
            self.logger.debug(f"Screen captured: {screenshot.shape}")
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Error capturing screen: {str(e)}")
            raise
    
    def _save_screenshot(self, image: np.ndarray, file_path: str):
        """Save screenshot to file"""
        try:
            cv2.imwrite(file_path, image)
            self.logger.debug(f"Screenshot saved: {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving screenshot to {file_path}: {str(e)}")
    
    def capture_region(self, x: int, y: int, width: int, height: int,
                      save_file: Optional[str] = None) -> np.ndarray:
        """
        Capture a specific region of the screen
        
        Args:
            x: Region x coordinate
            y: Region y coordinate
            width: Region width
            height: Region height
            save_file: Optional file path to save screenshot
            
        Returns:
            np.ndarray: Region screenshot in BGR format
        """
        # Capture full screen
        full_screenshot = self.capture()
        
        # Extract region
        region = full_screenshot[y:y+height, x:x+width]
        
        # Save region if requested
        if save_file:
            self._save_screenshot(region, save_file)
        
        self.logger.debug(f"Region captured: ({x}, {y}, {width}, {height})")
        return region
    
    def capture_with_delay(self, delay: float, save_file: Optional[str] = None) -> np.ndarray:
        """
        Capture screen after a delay
        
        Args:
            delay: Delay in seconds before capture
            save_file: Optional file path to save screenshot
            
        Returns:
            np.ndarray: Screenshot image in BGR format
        """
        self.logger.debug(f"Waiting {delay}s before capture")
        time.sleep(delay)
        return self.capture(save_file)
    
    def capture_multiple(self, count: int, interval: float = 1.0,
                        save_dir: Optional[str] = None) -> list:
        """
        Capture multiple screenshots with intervals
        
        Args:
            count: Number of screenshots to capture
            interval: Interval between captures in seconds
            save_dir: Directory to save screenshots (optional)
            
        Returns:
            list: List of screenshot images
        """
        screenshots = []
        
        if save_dir:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        for i in range(count):
            # Capture screenshot
            screenshot = self.capture()
            screenshots.append(screenshot)
            
            # Save if directory provided
            if save_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"capture_{i+1:03d}_{timestamp}.png"
                save_path = Path(save_dir) / filename
                self._save_screenshot(screenshot, str(save_path))
            
            # Wait for interval (except for last capture)
            if i < count - 1:
                time.sleep(interval)
        
        self.logger.info(f"Captured {count} screenshots with {interval}s interval")
        return screenshots
    
    def compare_screenshots(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Compare two screenshots and return similarity score
        
        Args:
            img1: First screenshot
            img2: Second screenshot
            
        Returns:
            float: Similarity score (0.0 to 1.0, higher is more similar)
        """
        try:
            # Ensure images have same dimensions
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate structural similarity
            from skimage.metrics import structural_similarity as ssim
            similarity = ssim(gray1, gray2)
            
            self.logger.debug(f"Screenshot similarity: {similarity:.3f}")
            return similarity
            
        except ImportError:
            # Fallback to simple correlation if scikit-image not available
            try:
                # Calculate normalized cross correlation
                result = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)
                similarity = np.max(result)
                
                self.logger.debug(f"Screenshot similarity (fallback): {similarity:.3f}")
                return similarity
                
            except Exception as e:
                self.logger.error(f"Error comparing screenshots: {str(e)}")
                return 0.0
        except Exception as e:
            self.logger.error(f"Error comparing screenshots: {str(e)}")
            return 0.0
    
    def wait_for_screen_change(self, timeout: float = 10.0, threshold: float = 0.95,
                              check_interval: float = 0.5) -> bool:
        """
        Wait for screen to change
        
        Args:
            timeout: Maximum time to wait in seconds
            threshold: Similarity threshold (screen changed if similarity < threshold)
            check_interval: Interval between checks in seconds
            
        Returns:
            bool: True if screen changed, False if timeout
        """
        start_time = time.time()
        initial_screenshot = self.capture()
        
        while time.time() - start_time < timeout:
            time.sleep(check_interval)
            current_screenshot = self.capture()
            
            similarity = self.compare_screenshots(initial_screenshot, current_screenshot)
            
            if similarity < threshold:
                self.logger.debug(f"Screen changed detected (similarity: {similarity:.3f})")
                return True
        
        self.logger.debug(f"Screen change timeout after {timeout}s")
        return False
    
    def wait_for_screen_stable(self, timeout: float = 10.0, threshold: float = 0.98,
                              check_interval: float = 0.5, stable_duration: float = 1.0) -> bool:
        """
        Wait for screen to become stable (no changes)
        
        Args:
            timeout: Maximum time to wait in seconds
            threshold: Similarity threshold (stable if similarity >= threshold)
            check_interval: Interval between checks in seconds
            stable_duration: Duration screen must be stable in seconds
            
        Returns:
            bool: True if screen became stable, False if timeout
        """
        start_time = time.time()
        stable_start = None
        previous_screenshot = self.capture()
        
        while time.time() - start_time < timeout:
            time.sleep(check_interval)
            current_screenshot = self.capture()
            
            similarity = self.compare_screenshots(previous_screenshot, current_screenshot)
            
            if similarity >= threshold:
                # Screen is stable
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= stable_duration:
                    self.logger.debug(f"Screen stable for {stable_duration}s")
                    return True
            else:
                # Screen changed, reset stable timer
                stable_start = None
                previous_screenshot = current_screenshot
        
        self.logger.debug(f"Screen stability timeout after {timeout}s")
        return False
    
    def create_video_from_screenshots(self, screenshot_dir: str, output_path: str,
                                    fps: int = 10, duration: Optional[float] = None):
        """
        Create video from saved screenshots
        
        Args:
            screenshot_dir: Directory containing screenshots
            output_path: Path for output video file
            fps: Frames per second
            duration: Optional duration limit in seconds
        """
        try:
            import glob
            
            # Get all PNG files in directory
            screenshot_files = sorted(glob.glob(str(Path(screenshot_dir) / "*.png")))
            
            if not screenshot_files:
                self.logger.error(f"No screenshots found in {screenshot_dir}")
                return
            
            # Limit by duration if specified
            if duration:
                max_frames = int(fps * duration)
                screenshot_files = screenshot_files[:max_frames]
            
            # Read first image to get dimensions
            first_img = cv2.imread(screenshot_files[0])
            height, width, layers = first_img.shape
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Add frames to video
            for screenshot_file in screenshot_files:
                img = cv2.imread(screenshot_file)
                video_writer.write(img)
            
            video_writer.release()
            
            self.logger.info(f"Video created: {output_path} ({len(screenshot_files)} frames, {fps} fps)")
            
        except Exception as e:
            self.logger.error(f"Error creating video: {str(e)}")
    
    def get_screen_info(self) -> dict:
        """
        Get information about the current screen
        
        Returns:
            dict: Screen information
        """
        try:
            screenshot = self.capture()
            height, width = screenshot.shape[:2]
            
            # Calculate average brightness
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)
            
            # Calculate color distribution
            colors = screenshot.reshape(-1, 3)
            avg_color = np.mean(colors, axis=0)
            
            info = {
                'width': width,
                'height': height,
                'channels': screenshot.shape[2] if len(screenshot.shape) > 2 else 1,
                'average_brightness': float(avg_brightness),
                'average_color_bgr': [float(c) for c in avg_color],
                'total_pixels': width * height
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting screen info: {str(e)}")
            return {}
    
    def enable_auto_save(self, directory: str = "screenshots"):
        """Enable automatic screenshot saving"""
        self.save_screenshots = True
        self.screenshot_dir = directory
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Auto-save enabled: {directory}")
    
    def disable_auto_save(self):
        """Disable automatic screenshot saving"""
        self.save_screenshots = False
        self.logger.info("Auto-save disabled")