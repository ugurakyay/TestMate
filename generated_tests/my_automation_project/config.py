# Otomasyon Projesi Konfigürasyonu
# Framework: SELENIUM

import os
from typing import Dict, Any

class Config:
    """Test konfigürasyonu"""
    
    # Test ayarları
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 10
    PAGE_LOAD_TIMEOUT = 30
    
    # Tarayıcı ayarları (Selenium için)
    BROWSER = "chrome"  # chrome, firefox, safari, edge
    HEADLESS = False
    
    # Appium ayarları (Mobil için)
    APPIUM_SERVER = "http://localhost:4723/wd/hub"
    ANDROID_CAPS = {
        "platformName": "Android",
        "platformVersion": "11.0",
        "deviceName": "Android Emulator",
        "automationName": "UiAutomator2",
        "app": "path/to/your/app.apk"
    }
    
    IOS_CAPS = {
        "platformName": "iOS",
        "platformVersion": "15.0",
        "deviceName": "iPhone Simulator",
        "automationName": "XCUITest",
        "app": "path/to/your/app.app"
    }
    
    # API ayarları
    BASE_URL = "https://api.example.com"
    API_TIMEOUT = 30
    
    # Test verileri
    TEST_DATA = {
        "valid_user": {
            "email": "test@example.com",
            "password": "123456"
        },
        "invalid_user": {
            "email": "invalid@example.com",
            "password": "wrong"
        }
    }
    
    # Rapor ayarları
    REPORT_DIR = "reports"
    SCREENSHOT_DIR = "screenshots"
    
    @classmethod
    def get_driver_caps(cls) -> Dict[str, Any]:
        """Driver capabilities döndür"""
        if framework == "appium":
            return cls.ANDROID_CAPS
        return {}
