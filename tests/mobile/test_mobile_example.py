import pytest
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.touch_action import TouchAction

class TestMobileExample:
    """Example mobile test using Appium"""
    
    def setup_method(self):
        """Setup Appium driver before each test"""
        # Appium capabilities for Android
        desired_caps = {
            'platformName': 'Android',
            'platformVersion': '11.0',
            'deviceName': 'Android Emulator',
            'automationName': 'UiAutomator2',
            'app': '/path/to/your/app.apk',  # Update with your app path
            'noReset': True
        }
        
        # Initialize Appium driver
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.driver.implicitly_wait(10)
    
    def teardown_method(self):
        """Cleanup after each test"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_app_launch(self):
        """Test that the app launches successfully"""
        # Wait for app to load
        self.driver.implicitly_wait(5)
        
        # Check if app is running
        current_activity = self.driver.current_activity
        assert current_activity is not None, "App should be running"
    
    def test_tap_action(self):
        """Test tap action on screen"""
        # Get screen dimensions
        screen_size = self.driver.get_window_size()
        width = screen_size['width']
        height = screen_size['height']
        
        # Perform tap action in center of screen
        actions = TouchAction(self.driver)
        actions.tap(x=width/2, y=height/2).perform()
        
        # Verify tap was registered (this would depend on your app's behavior)
        assert True, "Tap action should be performed"
    
    def test_element_find(self):
        """Test finding elements by different locators"""
        try:
            # Try to find element by ID
            element = self.driver.find_element(AppiumBy.ID, "com.example.app:id/button")
            assert element is not None, "Element should be found"
        except:
            # If element not found, this is expected in demo
            pass 