"""Image recognition modules"""

from .template_matcher import TemplateMatchers
from .color_detector import ColorDetector

# Optional OCR import
try:
    from .ocr_recognizer import OCRRecognizer
    __all__ = ['TemplateMatchers', 'OCRRecognizer', 'ColorDetector']
except ImportError:
    __all__ = ['TemplateMatchers', 'ColorDetector']