import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class TestWebExample:
    """Example web test using Selenium"""
    
    def setup_method(self):
        """Setup webdriver before each test"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.implicitly_wait(10)
    
    def teardown_method(self):
        """Cleanup after each test"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_google_search(self):
        """Test Google search functionality"""
        # Navigate to Google
        self.driver.get("https://www.google.com")
        
        # Find and fill search box
        search_box = self.driver.find_element(By.NAME, "q")
        search_box.send_keys("AI test automation")
        search_box.submit()
        
        # Wait for results
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        
        # Verify search results are present
        results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
        assert len(results) > 0, "Search results should be present"
    
    def test_page_title(self):
        """Test page title verification"""
        self.driver.get("https://www.python.org")
        assert "Python" in self.driver.title, "Page title should contain 'Python'" 