"""
Device Controller Base Class

Provides the base interface for device control operations.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np


class DeviceController(ABC):
    """Base class for device controllers"""
    
    def __init__(self, device_id: Optional[str] = None):
        """
        Initialize device controller
        
        Args:
            device_id: Device identifier (optional)
        """
        self.device_id = device_id
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the device
        
        Returns:
            bool: True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the device"""
        pass
    
    @abstractmethod
    def screenshot(self) -> np.ndarray:
        """
        Take a screenshot of the device screen
        
        Returns:
            np.ndarray: Screenshot image in BGR format
        """
        pass
    
    @abstractmethod
    def click(self, x: int, y: int):
        """
        Perform a click at specified coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        pass
    
    @abstractmethod
    def long_press(self, x: int, y: int, duration: float = 1.0):
        """
        Perform a long press at specified coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Press duration in seconds
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the screen size of the device
        
        Returns:
            Tuple[int, int]: (width, height) of the screen
        """
        pass
    
    def is_device_connected(self) -> bool:
        """
        Check if device is connected
        
        Returns:
            bool: True if device is connected
        """
        return self.is_connected