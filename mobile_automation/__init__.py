"""
Mobile Automation Framework

A comprehensive Python solution for mobile app image recognition and automated clicking.
Supports Android and iOS devices with multiple recognition methods.
"""

__version__ = "1.0.0"
__author__ = "Mobile Automation Team"

# Import core modules
from .utils import Config, Logger

# Optional imports - only import if dependencies are available
__all__ = ['Config', 'Logger']

try:
    from .device import DeviceController
    __all__.append('DeviceController')
except ImportError:
    pass

try:
    from .device import AndroidDevice
    __all__.append('AndroidDevice')
except ImportError:
    pass

try:
    from .recognition import TemplateMatchers
    __all__.append('TemplateMatchers')
except ImportError:
    pass

try:
    from .recognition import OCRRecognizer
    __all__.append('OCRRecognizer')
except ImportError:
    pass

try:
    from .recognition import ColorDetector
    __all__.append('ColorDetector')
except ImportError:
    pass

try:
    from .automation import AutoClicker
    __all__.append('AutoClicker')
except ImportError:
    pass

try:
    from .automation import ScreenCapture
    __all__.append('ScreenCapture')
except ImportError:
    pass