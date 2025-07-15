"""Image recognition modules"""

from .template_matcher import TemplateMatchers
from .ocr_recognizer import OCRRecognizer
from .color_detector import ColorDetector

__all__ = ['TemplateMatchers', 'OCRRecognizer', 'ColorDetector']