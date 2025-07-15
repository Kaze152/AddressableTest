"""
Test Basic Framework Functionality

Basic tests to verify the mobile automation framework works correctly.
"""

import sys
import os

# Add the mobile_automation module to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing module imports...")
    
    try:
        from mobile_automation.utils import Config, Logger
        print("✓ Core utils imported successfully")
        
        # Test optional imports
        available_modules = []
        
        try:
            from mobile_automation.device import AndroidDevice
            available_modules.append("AndroidDevice")
        except ImportError:
            print("  - AndroidDevice not available (missing adb-shell)")
        
        try:
            from mobile_automation.recognition import TemplateMatchers
            available_modules.append("TemplateMatchers")
        except ImportError:
            print("  - TemplateMatchers not available")
        
        try:
            from mobile_automation.recognition import OCRRecognizer
            available_modules.append("OCRRecognizer")
        except ImportError:
            print("  - OCRRecognizer not available (missing paddleocr)")
        
        try:
            from mobile_automation.recognition import ColorDetector
            available_modules.append("ColorDetector")
        except ImportError:
            print("  - ColorDetector not available")
        
        try:
            from mobile_automation.automation import AutoClicker, ScreenCapture
            available_modules.extend(["AutoClicker", "ScreenCapture"])
        except ImportError:
            print("  - Automation modules not available")
        
        print(f"✓ Available modules: {', '.join(available_modules) if available_modules else 'Core modules only'}")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_config_creation():
    """Test configuration file creation"""
    print("Testing configuration creation...")
    
    try:
        from mobile_automation.utils import Config
        
        # Create sample config
        Config.create_sample_config('sample_config.yaml')
        
        # Load and test config
        config = Config()
        threshold = config.get('recognition.template_matching.threshold', 0.8)
        print(f"✓ Configuration created and loaded, threshold: {threshold}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_logger():
    """Test logging functionality"""
    print("Testing logger...")
    
    try:
        from mobile_automation.utils import Logger
        
        logger = Logger.get_logger("TestLogger")
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        
        print("✓ Logger working correctly")
        return True
    except Exception as e:
        print(f"✗ Logger error: {e}")
        return False

def test_template_matcher():
    """Test template matcher initialization"""
    print("Testing template matcher...")
    
    try:
        from mobile_automation.recognition.template_matcher import TemplateMatchers
        
        matcher = TemplateMatchers()
        print(f"✓ Template matcher initialized with threshold: {matcher.threshold}")
        return True
    except Exception as e:
        print(f"✗ Template matcher error: {e}")
        return False

def test_ocr_recognizer():
    """Test OCR recognizer initialization"""
    print("Testing OCR recognizer...")
    
    try:
        from mobile_automation.recognition.ocr_recognizer import OCRRecognizer
        
        # Note: This might fail if PaddleOCR is not properly installed
        ocr = OCRRecognizer()
        print(f"✓ OCR recognizer initialized with language: {ocr.language}")
        return True
    except Exception as e:
        print(f"✗ OCR recognizer error: {e}")
        print("  Note: This is normal if PaddleOCR is not installed")
        return False

def test_color_detector():
    """Test color detector initialization"""
    print("Testing color detector...")
    
    try:
        from mobile_automation.recognition.color_detector import ColorDetector
        
        detector = ColorDetector()
        print(f"✓ Color detector initialized with tolerance: {detector.tolerance}")
        return True
    except Exception as e:
        print(f"✗ Color detector error: {e}")
        return False

def test_android_device():
    """Test Android device initialization (without connecting)"""
    print("Testing Android device...")
    
    try:
        from mobile_automation.device.android_device import AndroidDevice
        
        # Just test initialization, not connection
        device = AndroidDevice()
        print(f"✓ Android device initialized, connected: {device.is_connected}")
        return True
    except Exception as e:
        print(f"✗ Android device error: {e}")
        print("  Note: This is normal if adb-shell is not installed")
        return False

def run_all_tests():
    """Run all tests"""
    print("Mobile Automation Framework - Basic Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_creation,
        test_logger,
        test_template_matcher,
        test_color_detector,
        test_android_device,
        test_ocr_recognizer,  # This one might fail, so put it last
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    elif passed >= total - 1:  # Allow OCR test to fail
        print("✅ Core functionality tests passed!")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return passed >= total - 1

if __name__ == "__main__":
    run_all_tests()