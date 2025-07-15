"""
WeChat Automation Example

Demonstrates specific automation tasks for WeChat application.
"""

import time
import sys
import os

# Add the mobile_automation module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mobile_automation import AndroidDevice, AutoClicker, ScreenCapture
from mobile_automation.automation.clicker import ClickType


class WeChatAutomation:
    """WeChat automation helper class"""
    
    def __init__(self, device):
        self.device = device
        self.clicker = AutoClicker(device)
        self.screen_capture = ScreenCapture(device)
        
    def open_wechat(self):
        """Open WeChat application"""
        print("Opening WeChat...")
        
        # Try to find WeChat icon by text
        result = self.clicker.click_text("微信", exact_match=False)
        if result.success:
            print("WeChat opened via text")
            return True
        
        # Try alternative text
        result = self.clicker.click_text("WeChat", exact_match=False)
        if result.success:
            print("WeChat opened via English text")
            return True
        
        print("Could not find WeChat app icon")
        return False
    
    def navigate_to_contacts(self):
        """Navigate to contacts tab"""
        print("Navigating to contacts...")
        
        # Try to click on contacts tab (通讯录)
        result = self.clicker.click_text("通讯录", exact_match=False)
        if result.success:
            print("Navigated to contacts")
            return True
        
        # Try English text
        result = self.clicker.click_text("Contacts", exact_match=False, ignore_case=True)
        if result.success:
            print("Navigated to contacts (English)")
            return True
        
        print("Could not find contacts tab")
        return False
    
    def search_contact(self, contact_name):
        """Search for a specific contact"""
        print(f"Searching for contact: {contact_name}")
        
        # Try to find search icon or search box
        search_terms = ["搜索", "Search", "🔍"]
        
        for term in search_terms:
            result = self.clicker.click_text(term, exact_match=False)
            if result.success:
                print(f"Clicked search using term: {term}")
                break
        else:
            # Try to find search area by looking for typical search UI elements
            print("Could not find search button, trying to click at typical search location")
            width, height = self.device.get_screen_size()
            # Typical search location is usually at top of screen
            search_x = width - 100
            search_y = 150
            self.clicker.click_coordinates(search_x, search_y)
        
        # Wait for search interface to appear
        time.sleep(1)
        
        # Type the contact name
        try:
            self.device.input_text(contact_name)
            print(f"Typed contact name: {contact_name}")
            time.sleep(1)
            
            # Try to click on the search result
            result = self.clicker.click_text(contact_name, exact_match=False)
            if result.success:
                print(f"Clicked on contact: {contact_name}")
                return True
            else:
                print(f"Could not find contact in search results: {contact_name}")
                return False
                
        except Exception as e:
            print(f"Error typing contact name: {str(e)}")
            return False
    
    def send_message(self, message_text):
        """Send a message in current chat"""
        print(f"Sending message: {message_text}")
        
        # Look for message input box
        # Try to find the message input area
        width, height = self.device.get_screen_size()
        
        # Message input is usually at the bottom of the screen
        input_x = width // 2
        input_y = height - 100
        
        # Click on message input area
        self.clicker.click_coordinates(input_x, input_y)
        time.sleep(0.5)
        
        try:
            # Type the message
            self.device.input_text(message_text)
            print(f"Typed message: {message_text}")
            time.sleep(1)
            
            # Look for send button (发送)
            send_result = self.clicker.click_text("发送", exact_match=False)
            if send_result.success:
                print("Message sent via Chinese text")
                return True
            
            # Try English send button
            send_result = self.clicker.click_text("Send", exact_match=False)
            if send_result.success:
                print("Message sent via English text")
                return True
            
            # Try to find send button by looking for common send icon location
            send_x = width - 50
            send_y = height - 100
            send_result = self.clicker.click_coordinates(send_x, send_y)
            if send_result.success:
                print("Message sent via coordinate click")
                return True
            
            print("Could not find send button")
            return False
            
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
    
    def open_chat_with_contact(self, contact_name):
        """Open chat with specific contact"""
        print(f"Opening chat with: {contact_name}")
        
        if not self.navigate_to_contacts():
            return False
        
        if not self.search_contact(contact_name):
            return False
        
        # Wait for contact profile to load
        time.sleep(2)
        
        # Look for message/chat button (发消息 or 聊天)
        chat_terms = ["发消息", "聊天", "Message", "Chat"]
        
        for term in chat_terms:
            result = self.clicker.click_text(term, exact_match=False)
            if result.success:
                print(f"Opened chat using term: {term}")
                return True
        
        # If no specific chat button found, try clicking on contact name again
        result = self.clicker.click_text(contact_name, exact_match=False)
        if result.success:
            print("Opened chat by clicking contact name")
            return True
        
        print("Could not open chat with contact")
        return False
    
    def check_new_messages(self):
        """Check for new messages in chat list"""
        print("Checking for new messages...")
        
        # Navigate to chat list (微信 tab)
        result = self.clicker.click_text("微信", exact_match=False)
        if not result.success:
            result = self.clicker.click_text("Chats", exact_match=False)
        
        if result.success:
            print("Navigated to chat list")
            
            # Take screenshot and analyze for red dots or unread indicators
            screenshot = self.screen_capture.capture()
            
            # Look for red color (typically used for unread message indicators)
            red_indicators = self.clicker.color_detector.detect_color(screenshot, "red", min_area=50)
            
            if red_indicators:
                print(f"Found {len(red_indicators)} potential unread message indicators")
                
                # Click on the first red indicator (largest area)
                largest_indicator = red_indicators[0]
                result = self.clicker.click_coordinates(largest_indicator.center_x, largest_indicator.center_y)
                
                if result.success:
                    print("Clicked on unread message indicator")
                    return True
            else:
                print("No unread message indicators found")
                return False
        else:
            print("Could not navigate to chat list")
            return False
    
    def scroll_chat_list(self, direction="down", count=3):
        """Scroll through chat list"""
        print(f"Scrolling chat list {direction} {count} times")
        
        width, height = self.device.get_screen_size()
        center_x = width // 2
        start_y = height // 3
        end_y = 2 * height // 3
        
        for i in range(count):
            if direction.lower() == "down":
                self.device.swipe(center_x, end_y, center_x, start_y, 0.5)
            else:  # up
                self.device.swipe(center_x, start_y, center_x, end_y, 0.5)
            
            time.sleep(1)
            print(f"Scroll {i + 1} completed")
    
    def auto_reply_messages(self, reply_text="自动回复", max_chats=3):
        """Automatically reply to recent messages"""
        print(f"Auto-replying to recent messages with: '{reply_text}'")
        
        # Navigate to chat list
        if not self.clicker.click_text("微信", exact_match=False).success:
            self.clicker.click_text("Chats", exact_match=False)
        
        time.sleep(2)
        
        # Take screenshot to analyze chat list
        screenshot = self.screen_capture.capture()
        
        # Look for chat items (approximate positions)
        width, height = self.device.get_screen_size()
        chat_height = height // 8  # Approximate height of each chat item
        
        replied_count = 0
        
        for i in range(min(max_chats, 8)):  # Check up to 8 visible chats
            if replied_count >= max_chats:
                break
            
            # Calculate approximate chat position
            chat_y = 200 + (i * chat_height)
            
            # Click on chat
            result = self.clicker.click_coordinates(width // 2, chat_y)
            
            if result.success:
                time.sleep(2)  # Wait for chat to open
                
                # Send reply
                if self.send_message(reply_text):
                    replied_count += 1
                    print(f"Replied to chat {i + 1}")
                
                # Go back to chat list
                self.device.press_key(4)  # Android back button
                time.sleep(1)
        
        print(f"Auto-replied to {replied_count} chats")


def wechat_basic_operations_example():
    """Demonstrate basic WeChat operations"""
    print("=== WeChat Basic Operations Example ===")
    
    # Connect to device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize WeChat automation
        wechat = WeChatAutomation(device)
        
        # Open WeChat
        if wechat.open_wechat():
            time.sleep(3)  # Wait for app to load
            
            # Check for new messages
            wechat.check_new_messages()
            time.sleep(2)
            
            # Navigate to contacts
            wechat.navigate_to_contacts()
            time.sleep(2)
            
            # Scroll through chat list
            wechat.scroll_chat_list("down", 2)
            
        else:
            print("Could not open WeChat")
    
    except Exception as e:
        print(f"Error in WeChat basic operations: {str(e)}")
    finally:
        device.disconnect()


def wechat_automated_messaging_example():
    """Demonstrate automated messaging"""
    print("=== WeChat Automated Messaging Example ===")
    
    # Connect to device
    device = AndroidDevice()
    
    if not device.connect():
        print("Failed to connect to Android device")
        return
    
    try:
        # Initialize WeChat automation
        wechat = WeChatAutomation(device)
        
        # Open WeChat
        if wechat.open_wechat():
            time.sleep(3)
            
            # Example: Send message to a contact (replace with actual contact name)
            contact_name = "测试联系人"  # Replace with actual contact name
            message = "这是一个自动发送的测试消息"
            
            if wechat.open_chat_with_contact(contact_name):
                time.sleep(2)
                wechat.send_message(message)
                print(f"Message sent to {contact_name}")
            else:
                print(f"Could not open chat with {contact_name}")
                
                # Alternative: Auto-reply to recent messages
                print("Trying auto-reply to recent messages instead...")
                wechat.auto_reply_messages("自动回复测试", max_chats=2)
        
        else:
            print("Could not open WeChat")
    
    except Exception as e:
        print(f"Error in WeChat automated messaging: {str(e)}")
    finally:
        device.disconnect()


def main():
    """Run WeChat automation examples"""
    print("WeChat Automation Examples")
    print("=" * 30)
    
    print("Note: Make sure WeChat is installed and you have appropriate permissions.")
    print("This example is for educational purposes only.")
    print()
    
    try:
        wechat_basic_operations_example()
        print()
        
        # Uncomment to test automated messaging (use with caution!)
        # wechat_automated_messaging_example()
        # print()
        
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    print("WeChat examples completed!")


if __name__ == "__main__":
    main()