"""
Mobile Automation Framework

A comprehensive Python solution for mobile app image recognition and automated clicking.
Supports Android and iOS devices with multiple recognition methods.
"""

__version__ = "1.0.0"
__author__ = "Mobile Automation Team"

from .device import DeviceController, AndroidDevice
from .recognition import TemplateMatchers, OCRRecognizer, ColorDetector
from .automation import AutoClicker, ScreenCapture
from .utils import Config, Logger

__all__ = [
    'DeviceController',
    'AndroidDevice', 
    'TemplateMatchers',
    'OCRRecognizer',
    'ColorDetector',
    'AutoClicker',
    'ScreenCapture',
    'Config',
    'Logger'
]