"""
Basic Working Example

Demonstrates basic functionality that works without external device dependencies.
"""

import sys
import os
import numpy as np
import cv2

# Add the mobile_automation module to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.insert(0, root_dir)

from mobile_automation.recognition import TemplateMatchers, ColorDetector
from mobile_automation.utils import Config, Logger


def create_sample_image():
    """Create a sample image for testing"""
    # Create a sample image with some colored rectangles and text-like patterns
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255  # White background
    
    # Add some colored rectangles
    cv2.rectangle(img, (50, 50), (150, 100), (255, 0, 0), -1)  # Blue rectangle
    cv2.rectangle(img, (200, 50), (300, 100), (0, 255, 0), -1)  # Green rectangle
    cv2.rectangle(img, (350, 50), (450, 100), (0, 0, 255), -1)  # Red rectangle
    
    # Add some text-like patterns
    cv2.putText(img, 'BUTTON', (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, 'Settings', (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, '确认', (350, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Add some circles
    cv2.circle(img, (100, 350), 30, (128, 0, 128), -1)  # Purple circle
    cv2.circle(img, (250, 350), 25, (255, 165, 0), -1)  # Orange circle
    
    return img


def test_template_matching():
    """Test template matching with sample images"""
    print("=== Template Matching Test ===")
    
    # Create main image
    main_img = create_sample_image()
    
    # Create a template from part of the main image
    template = main_img[40:110, 40:160]  # Extract blue rectangle area
    
    # Initialize template matcher
    matcher = TemplateMatchers()
    
    # Find matches
    matches = matcher.match_template(main_img, template, template_name="blue_rectangle")
    
    print(f"Found {len(matches)} matches")
    for i, match in enumerate(matches):
        print(f"  Match {i+1}: {match}")
    
    # Draw matches on image
    if matches:
        result_img = matcher.draw_matches(main_img, matches)
        cv2.imwrite("template_matching_result.png", result_img)
        print("Template matching result saved as 'template_matching_result.png'")
    
    return len(matches) > 0


def test_color_detection():
    """Test color detection with sample images"""
    print("=== Color Detection Test ===")
    
    # Create main image
    main_img = create_sample_image()
    
    # Initialize color detector
    detector = ColorDetector()
    
    # Test different colors
    colors_to_test = ['blue', 'green', 'red', 'purple', 'orange']
    total_matches = 0
    
    for color in colors_to_test:
        matches = detector.detect_color(main_img, color, min_area=100)
        print(f"Found {len(matches)} {color} regions")
        for match in matches:
            print(f"  {color}: {match}")
        total_matches += len(matches)
    
    # Draw all color matches
    all_matches = []
    for color in colors_to_test:
        matches = detector.detect_color(main_img, color, min_area=100)
        all_matches.extend(matches)
    
    if all_matches:
        result_img = detector.draw_matches(main_img, all_matches)
        cv2.imwrite("color_detection_result.png", result_img)
        print("Color detection result saved as 'color_detection_result.png'")
    
    return total_matches > 0


def test_configuration():
    """Test configuration management"""
    print("=== Configuration Test ===")
    
    # Create and test configuration
    Config.create_sample_config("test_config.yaml")
    print("Sample configuration created as 'test_config.yaml'")
    
    # Load configuration
    config = Config()
    config.load_from_file("test_config.yaml")
    
    # Test configuration values
    threshold = config.get('recognition.template_matching.threshold')
    tolerance = config.get('recognition.color_detection.tolerance')
    log_level = config.get('logging.level')
    
    print(f"Template matching threshold: {threshold}")
    print(f"Color detection tolerance: {tolerance}")
    print(f"Logging level: {log_level}")
    
    # Test setting values
    config.set('recognition.template_matching.threshold', 0.9)
    new_threshold = config.get('recognition.template_matching.threshold')
    print(f"Updated threshold: {new_threshold}")
    
    return True


def test_logging():
    """Test logging functionality"""
    print("=== Logging Test ===")
    
    # Get logger
    logger = Logger.get_logger("TestLogger")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("Logging test completed (check console output above)")
    return True


def main():
    """Run all working examples"""
    print("Mobile Automation Framework - Working Examples")
    print("=" * 55)
    print("Testing core functionality without external dependencies...")
    print()
    
    tests = [
        ("Configuration Management", test_configuration),
        ("Logging System", test_logging),
        ("Template Matching", test_template_matching),
        ("Color Detection", test_color_detection),
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            if test_func():
                print(f"✓ {test_name} test passed")
                passed += 1
            else:
                print(f"✗ {test_name} test failed")
        except Exception as e:
            print(f"✗ {test_name} test failed with error: {e}")
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All core functionality tests passed!")
        print("\nNext steps:")
        print("1. Install 'pip install adb-shell' for Android device support")
        print("2. Install 'pip install paddleocr' for OCR functionality")
        print("3. Connect an Android device to test full automation")
    else:
        print("❌ Some tests failed")
    
    print("\nGenerated files:")
    print("- template_matching_result.png: Template matching visualization")
    print("- color_detection_result.png: Color detection visualization") 
    print("- test_config.yaml: Sample configuration file")


if __name__ == "__main__":
    main()