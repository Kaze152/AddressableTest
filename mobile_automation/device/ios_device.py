"""
iOS Device Controller

Implements device control for iOS devices using tidevice.
"""

import time
import numpy as np
from typing import Tuple, Optional
from PIL import Image
import cv2

try:
    import tidevice
except ImportError:
    raise ImportError("tidevice is required for iOS device control. Install with: pip install tidevice")

from .device_controller import DeviceController
from ..utils.logger import Logger


class IOSDevice(DeviceController):
    """iOS device controller using tidevice"""
    
    def __init__(self, device_id: Optional[str] = None):
        """
        Initialize iOS device controller
        
        Args:
            device_id: iOS device UDID (optional, will use first available device if None)
        """
        super().__init__(device_id)
        self.device = None
        self.logger = Logger.get_logger("IOSDevice")
        self._screen_size = None
    
    def connect(self) -> bool:
        """
        Connect to iOS device via tidevice
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.device_id:
                self.device = tidevice.Device(self.device_id)
            else:
                # Use first available device
                devices = tidevice.Device.list()
                if not devices:
                    self.logger.error("No iOS devices found")
                    return False
                self.device = tidevice.Device(devices[0])
                self.device_id = devices[0]
            
            # Test connection by getting device info
            device_info = self.device.info
            self.logger.info(f"Connected to iOS device: {device_info.get('DeviceName', 'Unknown')}")
            self.logger.info(f"iOS Version: {device_info.get('ProductVersion', 'Unknown')}")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to iOS device: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from iOS device"""
        if self.device and self.is_connected:
            try:
                # tidevice doesn't require explicit disconnection
                self.is_connected = False
                self.logger.info("Disconnected from iOS device")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {str(e)}")
    
    def screenshot(self) -> np.ndarray:
        """
        Take a screenshot using tidevice
        
        Returns:
            np.ndarray: Screenshot image in BGR format
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            # Take screenshot
            screenshot_data = self.device.screenshot()
            
            # Convert to PIL Image
            image = Image.open(screenshot_data)
            
            # Convert to numpy array (RGB)
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV compatibility
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            self.logger.debug(f"Screenshot captured: {img_array.shape}")
            return img_array
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            raise
    
    def click(self, x: int, y: int):
        """
        Perform a tap at specified coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            self.device.click(x, y)
            self.logger.debug(f"Clicked at ({x}, {y})")
            time.sleep(0.1)  # Small delay after click
            
        except Exception as e:
            self.logger.error(f"Error clicking at ({x}, {y}): {str(e)}")
            raise
    
    def long_press(self, x: int, y: int, duration: float = 1.0):
        """
        Perform a long press at specified coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            # tidevice doesn't have direct long press, simulate with swipe
            self.device.swipe(x, y, x, y, duration)
            self.logger.debug(f"Long pressed at ({x}, {y}) for {duration}s")
            
        except Exception as e:
            self.logger.error(f"Error long pressing at ({x}, {y}): {str(e)}")
            raise
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5):
        """
        Perform a swipe gesture
        
        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate
            duration: Swipe duration in seconds
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            self.device.swipe(start_x, start_y, end_x, end_y, duration)
            self.logger.debug(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
        except Exception as e:
            self.logger.error(f"Error swiping: {str(e)}")
            raise
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the screen size of the iOS device
        
        Returns:
            Tuple[int, int]: (width, height) of the screen
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        if self._screen_size:
            return self._screen_size
        
        try:
            # Get screen size from device info
            device_info = self.device.info
            width = device_info.get('ScreenWidth')
            height = device_info.get('ScreenHeight')
            
            if width and height:
                self._screen_size = (width, height)
                self.logger.info(f"Screen size: {width}x{height}")
                return self._screen_size
            else:
                # Fallback: use screenshot dimensions
                screenshot = self.screenshot()
                height, width = screenshot.shape[:2]
                self._screen_size = (width, height)
                return self._screen_size
                
        except Exception as e:
            self.logger.error(f"Error getting screen size: {str(e)}")
            # Fallback: use screenshot dimensions
            try:
                screenshot = self.screenshot()
                height, width = screenshot.shape[:2]
                self._screen_size = (width, height)
                return self._screen_size
            except:
                raise RuntimeError("Cannot determine screen size")
    
    def input_text(self, text: str):
        """
        Input text to the device (limited support on iOS)
        
        Args:
            text: Text to input
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            # tidevice has limited text input support
            # This may not work for all apps due to iOS restrictions
            self.logger.warning("Text input on iOS has limited support")
            
        except Exception as e:
            self.logger.error(f"Error inputting text: {str(e)}")
            raise
    
    def home_button(self):
        """Press the home button"""
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            self.device.home()
            self.logger.debug("Pressed home button")
            
        except Exception as e:
            self.logger.error(f"Error pressing home button: {str(e)}")
            raise