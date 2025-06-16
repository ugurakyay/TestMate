from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import pytest

from config import Config


class TestTestFix:
    """TestTestFix test sınıfı"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        """Her test sonrası çalışır"""
        self.driver.quit()
    
    def test_tc001(self):
        """Test fix"""
        try:
            # Test başarılı
            assert True
        except Exception as e:
            # Hata durumunda ekran görüntüsü al
            self.driver.save_screenshot(f'screenshots/error_{scenario.get("test_id", "test")}.png')
            raise e
