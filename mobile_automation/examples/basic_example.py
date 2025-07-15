"""
Basic Example

Demonstrates basic usage of the mobile automation framework.
"""

import time
import sys
import os

# Add the mobile_automation module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mobile_automation import AndroidDevice, TemplateMatchers, OCRRecognizer, AutoClicker, ScreenCapture
from mobile_automation.automation.clicker import ClickType


def basic_template_matching_example():
    """Demonstrate basic template matching and clicking"""
    print("=== Basic Template Matching Example ===")
    
    # Connect to Android device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize auto clicker
        clicker = AutoClicker(device)
        
        # Take a screenshot to see current state
        screenshot = device.screenshot()
        print(f"Screenshot captured: {screenshot.shape}")
        
        # Example: Click on a template (you would replace with actual template file)
        # result = clicker.click_template("path/to/button_template.png", template_name="home_button")
        
        # For demonstration, click at center of screen
        width, height = device.get_screen_size()
        center_x, center_y = width // 2, height // 2
        
        result = clicker.click_coordinates(center_x, center_y)
        print(f"Click result: {result}")
        
        # Wait a moment
        time.sleep(2)
        
        # Take another screenshot to see changes
        screenshot_after = device.screenshot()
        print(f"Screenshot after click: {screenshot_after.shape}")
        
    finally:
        device.disconnect()
        print("Disconnected from device")


def basic_ocr_example():
    """Demonstrate OCR text recognition and clicking"""
    print("=== Basic OCR Example ===")
    
    # Connect to Android device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize OCR recognizer and auto clicker
        ocr = OCRRecognizer()
        clicker = AutoClicker(device)
        
        # Take screenshot
        screenshot = device.screenshot()
        
        # Recognize all text in the image
        text_results = ocr.recognize_text(screenshot)
        
        print(f"Found {len(text_results)} text elements:")
        for i, text_result in enumerate(text_results[:5]):  # Show first 5 results
            print(f"  {i+1}. '{text_result.text}' at ({text_result.center_x}, {text_result.center_y}) confidence: {text_result.confidence:.3f}")
        
        # Example: Click on text containing "设置" (Settings)
        if text_results:
            # Find text containing "设置" or "Settings"
            settings_text = None
            for text_result in text_results:
                if "设置" in text_result.text or "Settings" in text_result.text.lower():
                    settings_text = text_result
                    break
            
            if settings_text:
                result = clicker.click_text("设置", exact_match=False)
                print(f"Settings click result: {result}")
            else:
                print("No settings text found, clicking first text element")
                result = clicker.click_coordinates(text_results[0].center_x, text_results[0].center_y)
                print(f"First text click result: {result}")
        
    except Exception as e:
        print(f"Error in OCR example: {str(e)}")
    finally:
        device.disconnect()
        print("Disconnected from device")


def basic_color_detection_example():
    """Demonstrate color detection and clicking"""
    print("=== Basic Color Detection Example ===")
    
    # Connect to Android device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize auto clicker
        clicker = AutoClicker(device)
        
        # Take screenshot
        screenshot = device.screenshot()
        
        # Try to find and click on blue elements (common for buttons)
        result = clicker.click_color("blue", min_area=500)
        print(f"Blue color click result: {result}")
        
        if not result.success:
            # Try green color
            result = clicker.click_color("green", min_area=500)
            print(f"Green color click result: {result}")
        
        if not result.success:
            # Try any red elements
            result = clicker.click_color("red", min_area=500)
            print(f"Red color click result: {result}")
        
    except Exception as e:
        print(f"Error in color detection example: {str(e)}")
    finally:
        device.disconnect()
        print("Disconnected from device")


def action_sequence_example():
    """Demonstrate action sequence execution"""
    print("=== Action Sequence Example ===")
    
    # Connect to Android device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize auto clicker
        clicker = AutoClicker(device)
        
        # Define a sequence of actions
        actions = [
            {
                'type': 'wait',
                'duration': 1.0
            },
            {
                'type': 'click_text',
                'text': '设置',
                'click_type': 'tap',
                'exact_match': False,
                'delay_after': 2.0
            },
            {
                'type': 'click_coordinates',
                'x': 100,
                'y': 200,
                'click_type': 'tap',
                'delay_after': 1.0
            },
            {
                'type': 'click_color',
                'color': 'blue',
                'min_area': 300,
                'click_type': 'tap'
            }
        ]
        
        # Execute the action sequence
        results = clicker.execute_action_sequence(actions)
        
        print(f"Action sequence results:")
        for i, result in enumerate(results):
            print(f"  Action {i+1}: {result}")
        
    except Exception as e:
        print(f"Error in action sequence example: {str(e)}")
    finally:
        device.disconnect()
        print("Disconnected from device")


def screen_capture_example():
    """Demonstrate screen capture functionality"""
    print("=== Screen Capture Example ===")
    
    # Connect to Android device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize screen capture
        screen_capture = ScreenCapture(device)
        
        # Capture single screenshot
        screenshot = screen_capture.capture("basic_screenshot.png")
        print(f"Screenshot saved: basic_screenshot.png, shape: {screenshot.shape}")
        
        # Capture multiple screenshots with interval
        print("Capturing 3 screenshots with 2s interval...")
        screenshots = screen_capture.capture_multiple(3, interval=2.0, save_dir="multiple_screenshots")
        print(f"Captured {len(screenshots)} screenshots")
        
        # Get screen information
        screen_info = screen_capture.get_screen_info()
        print(f"Screen info: {screen_info}")
        
    except Exception as e:
        print(f"Error in screen capture example: {str(e)}")
    finally:
        device.disconnect()
        print("Disconnected from device")


def main():
    """Run all basic examples"""
    print("Mobile Automation Framework - Basic Examples")
    print("=" * 50)
    
    try:
        # Run examples
        basic_template_matching_example()
        print()
        
        basic_ocr_example()
        print()
        
        basic_color_detection_example()
        print()
        
        action_sequence_example()
        print()
        
        screen_capture_example()
        print()
        
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    print("Examples completed!")


if __name__ == "__main__":
    main()