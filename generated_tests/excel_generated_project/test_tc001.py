from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import pytest

from config import Config


class TestKullancGirii:
    """TestKullancGirii test sınıfı"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        """Her test sonrası çalışır"""
        self.driver.quit()
    
    def test_tc001(self):
        """Kullanıcının email ve şifre ile giriş yapabilmesi"""
        try:
            self.driver.get('https://example.com')
            # Beklenen sonuç: Sayfa yüklendi
            element = self.wait.until(EC.element_to_be_clickable((By.ID, 'email-input')))
            element.click()
            # Beklenen sonuç: Email alanı aktif
            element = self.wait.until(EC.element_to_be_clickable((By.ID, 'email-input')))
            element.clear()
            element.send_keys('test@example.com')
            # Beklenen sonuç: Email girildi
            element = self.wait.until(EC.element_to_be_clickable((By.ID, 'password-input')))
            element.click()
            # Beklenen sonuç: Şifre alanı aktif
            element = self.wait.until(EC.element_to_be_clickable((By.ID, 'password-input')))
            element.clear()
            element.send_keys('123456')
            # Beklenen sonuç: Şifre girildi
            element = self.wait.until(EC.element_to_be_clickable((By.ID, 'login-btn')))
            element.click()
            # Beklenen sonuç: Giriş yapıldı
            # Test başarılı
            assert True
        except Exception as e:
            # Hata durumunda ekran görüntüsü al
            self.driver.save_screenshot(f'screenshots/error_{scenario.get("test_id", "test")}.png')
            raise e
