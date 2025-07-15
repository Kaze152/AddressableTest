"""
Android Device Controller

Implements device control for Android devices using ADB.
"""

import time
import numpy as np
from typing import Tuple, Optional, List
from PIL import Image
import io
import cv2

try:
    from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
except ImportError:
    raise ImportError("adb-shell is required for Android device control. Install with: pip install adb-shell")

from .device_controller import DeviceController
from ..utils.logger import Logger


class AndroidDevice(DeviceController):
    """Android device controller using ADB"""
    
    def __init__(self, device_id: Optional[str] = None, host: Optional[str] = None, port: int = 5555):
        """
        Initialize Android device controller
        
        Args:
            device_id: ADB device ID for USB connection
            host: IP address for TCP connection
            port: Port for TCP connection (default: 5555)
        """
        super().__init__(device_id)
        self.host = host
        self.port = port
        self.device = None
        self.logger = Logger.get_logger("AndroidDevice")
        self._screen_size = None
    
    def connect(self) -> bool:
        """
        Connect to Android device via ADB
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.host:
                # TCP connection
                self.device = AdbDeviceTcp(self.host, self.port, default_timeout_s=9.0)
                self.logger.info(f"Connecting to Android device via TCP: {self.host}:{self.port}")
            else:
                # USB connection
                from adb_shell.adb_device_async import AdbDeviceUsb
                self.device = AdbDeviceUsb()
                self.logger.info("Connecting to Android device via USB")
            
            # Attempt to connect
            if self.device.connect(rsa_keys=[PythonRSASigner.generate_key()]):
                self.is_connected = True
                self.logger.info("Successfully connected to Android device")
                
                # Get device info
                device_info = self.device.shell("getprop ro.product.model").strip()
                self.logger.info(f"Device model: {device_info}")
                
                return True
            else:
                self.logger.error("Failed to connect to Android device")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to Android device: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from Android device"""
        if self.device and self.is_connected:
            try:
                self.device.close()
                self.is_connected = False
                self.logger.info("Disconnected from Android device")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {str(e)}")
    
    def screenshot(self) -> np.ndarray:
        """
        Take a screenshot using ADB screencap
        
        Returns:
            np.ndarray: Screenshot image in BGR format
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            # Take screenshot using screencap
            screenshot_data = self.device.shell("screencap -p", decode=False)
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(screenshot_data))
            
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
            cmd = f"input tap {x} {y}"
            result = self.device.shell(cmd)
            self.logger.debug(f"Clicked at ({x}, {y})")
            time.sleep(0.1)  # Small delay after click
            
        except Exception as e:
            self.logger.error(f"Error clicking at ({x}, {y}): {str(e)}")
            raise
    
    def long_press(self, x: int, y: int, duration: float = 1.0):
        """
        Perform a long press using swipe with same start/end coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            duration_ms = int(duration * 1000)
            cmd = f"input swipe {x} {y} {x} {y} {duration_ms}"
            result = self.device.shell(cmd)
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
            duration_ms = int(duration * 1000)
            cmd = f"input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}"
            result = self.device.shell(cmd)
            self.logger.debug(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
        except Exception as e:
            self.logger.error(f"Error swiping: {str(e)}")
            raise
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the screen size of the Android device
        
        Returns:
            Tuple[int, int]: (width, height) of the screen
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        if self._screen_size:
            return self._screen_size
        
        try:
            # Get screen size using wm size command
            result = self.device.shell("wm size").strip()
            # Example output: "Physical size: 1080x1920"
            if ":" in result:
                size_str = result.split(":")[-1].strip()
                width, height = map(int, size_str.split("x"))
                self._screen_size = (width, height)
                self.logger.info(f"Screen size: {width}x{height}")
                return self._screen_size
            else:
                raise RuntimeError(f"Unexpected wm size output: {result}")
                
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
        Input text to the device
        
        Args:
            text: Text to input
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            # Escape special characters
            escaped_text = text.replace(" ", "%s").replace("&", "\\&")
            cmd = f"input text '{escaped_text}'"
            result = self.device.shell(cmd)
            self.logger.debug(f"Input text: {text}")
            
        except Exception as e:
            self.logger.error(f"Error inputting text: {str(e)}")
            raise
    
    def press_key(self, keycode: int):
        """
        Press a key by keycode
        
        Args:
            keycode: Android keycode (e.g., 4 for BACK, 3 for HOME)
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            cmd = f"input keyevent {keycode}"
            result = self.device.shell(cmd)
            self.logger.debug(f"Pressed key: {keycode}")
            
        except Exception as e:
            self.logger.error(f"Error pressing key {keycode}: {str(e)}")
            raise
    
    def get_current_activity(self) -> str:
        """
        Get the current activity name
        
        Returns:
            str: Current activity name
        """
        if not self.is_connected:
            raise RuntimeError("Device not connected")
        
        try:
            cmd = "dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
            result = self.device.shell(cmd).strip()
            self.logger.debug(f"Current activity info: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting current activity: {str(e)}")
            return ""