#!/usr/bin/env python3
"""
Template-Based Test Generator
AI olmadan da profesyonel test kodları üretir
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

class TemplateTestGenerator:
    """Template-based test case generator"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.keywords = self._load_keywords()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Test template'lerini yükle"""
        return {
            "web": {
                "selenium": {
                    "login": self._get_login_template(),
                    "form_submit": self._get_form_template(),
                    "navigation": self._get_navigation_template(),
                    "data_validation": self._get_validation_template(),
                    "ui_interaction": self._get_ui_template(),
                    "api_integration": self._get_api_integration_template()
                },
                "playwright": {
                    "login": self._get_playwright_login_template(),
                    "form_submit": self._get_playwright_form_template(),
                    "navigation": self._get_playwright_navigation_template()
                }
            },
            "mobile": {
                "appium": {
                    "login": self._get_mobile_login_template(),
                    "navigation": self._get_mobile_navigation_template(),
                    "gesture": self._get_gesture_template()
                }
            },
            "api": {
                "requests": {
                    "get_request": self._get_api_get_template(),
                    "post_request": self._get_api_post_template(),
                    "authentication": self._get_api_auth_template(),
                    "data_validation": self._get_api_validation_template()
                }
            }
        }
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """Anahtar kelimeleri yükle"""
        return {
            "login": ["giriş", "login", "oturum", "kullanıcı", "şifre", "email", "username", "password"],
            "form": ["form", "formu", "kayıt", "register", "submit", "gönder", "doldur", "fill"],
            "navigation": ["navigasyon", "menü", "menu", "sayfa", "page", "link", "bağlantı", "geçiş"],
            "validation": ["doğrulama", "validation", "kontrol", "check", "verify", "assert"],
            "data": ["veri", "data", "bilgi", "information", "kayıt", "record"],
            "search": ["arama", "search", "filtre", "filter", "bul", "find"],
            "upload": ["yükle", "upload", "dosya", "file", "resim", "image"],
            "download": ["indir", "download", "dosya", "file", "pdf", "excel"]
        }
    
    async def generate_test_cases(
        self, 
        feature_description: str, 
        test_type: str, 
        framework: str = None,
        additional_context: str = None
    ) -> List[Dict[str, Any]]:
        """Template-based test case generation"""
        
        # Feature tipini belirle
        feature_type = self._identify_feature_type(feature_description)
        
        # Framework belirle
        if not framework:
            framework = self._get_default_framework(test_type)
        
        # Template seç
        template = self._select_template(test_type, framework, feature_type)
        
        # Test case'leri oluştur
        test_cases = self._generate_from_template(
            template, feature_description, test_type, framework, additional_context
        )
        
        return test_cases
    
    def _identify_feature_type(self, description: str) -> str:
        """Feature tipini belirle"""
        description_lower = description.lower()
        
        for feature_type, keywords in self.keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return feature_type
        
        return "general"
    
    def _get_default_framework(self, test_type: str) -> str:
        """Varsayılan framework'ü belirle"""
        defaults = {
            "web": "selenium",
            "mobile": "appium", 
            "api": "requests"
        }
        return defaults.get(test_type, "selenium")
    
    def _select_template(self, test_type: str, framework: str, feature_type: str) -> str:
        """Uygun template'i seç"""
        if test_type == "web":
            if framework == "selenium":
                return self._get_selenium_template(feature_type)
            elif framework == "playwright":
                return self._get_playwright_template(feature_type)
        elif test_type == "mobile":
            return self._get_mobile_template(feature_type)
        elif test_type == "api":
            return self._get_api_template(feature_type)
        
        return self._get_general_template(test_type, framework)
    
    def _generate_from_template(
        self, 
        template: str, 
        description: str, 
        test_type: str, 
        framework: str, 
        context: str = None
    ) -> List[Dict[str, Any]]:
        """Template'den test case'leri oluştur"""
        
        # Test case'leri oluştur
        test_cases = []
        
        # Ana test case
        main_test = {
            "name": f"Test {description}",
            "description": f"Test case for {description}",
            "steps": self._generate_steps(description, test_type),
            "expected_result": self._generate_expected_result(description),
            "priority": "High",
            "code": template.format(
                description=description,
                test_name=self._sanitize_name(description),
                context=context or "",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        }
        test_cases.append(main_test)
        
        # Edge case'ler ekle
        edge_cases = self._generate_edge_cases(description, test_type, framework)
        test_cases.extend(edge_cases)
        
        return test_cases
    
    def _generate_steps(self, description: str, test_type: str) -> List[str]:
        """Test adımlarını oluştur"""
        steps = []
        
        if "login" in description.lower():
            steps = [
                "Navigate to login page",
                "Enter valid credentials",
                "Click login button",
                "Verify successful login"
            ]
        elif "form" in description.lower():
            steps = [
                "Navigate to form page",
                "Fill required fields",
                "Submit the form",
                "Verify form submission"
            ]
        elif "search" in description.lower():
            steps = [
                "Navigate to search page",
                "Enter search criteria",
                "Execute search",
                "Verify search results"
            ]
        else:
            steps = [
                f"Navigate to {description} page",
                f"Perform {description} action",
                "Verify the result"
            ]
        
        return steps
    
    def _generate_expected_result(self, description: str) -> str:
        """Beklenen sonucu oluştur"""
        if "login" in description.lower():
            return "User should be successfully logged in"
        elif "form" in description.lower():
            return "Form should be submitted successfully"
        elif "search" in description.lower():
            return "Search results should be displayed correctly"
        else:
            return f"{description} should work as expected"
    
    def _generate_edge_cases(self, description: str, test_type: str, framework: str) -> List[Dict[str, Any]]:
        """Edge case'leri oluştur"""
        edge_cases = []
        
        # Invalid data test
        invalid_test = {
            "name": f"Test {description} with Invalid Data",
            "description": f"Test {description} with invalid input data",
            "steps": [
                f"Navigate to {description} page",
                "Enter invalid data",
                "Submit the form",
                "Verify error handling"
            ],
            "expected_result": "Appropriate error message should be displayed",
            "priority": "Medium",
            "code": self._get_edge_case_template(description, "invalid_data", test_type, framework)
        }
        edge_cases.append(invalid_test)
        
        # Empty data test
        empty_test = {
            "name": f"Test {description} with Empty Data",
            "description": f"Test {description} with empty input fields",
            "steps": [
                f"Navigate to {description} page",
                "Leave fields empty",
                "Submit the form",
                "Verify validation"
            ],
            "expected_result": "Validation error should be displayed",
            "priority": "Medium",
            "code": self._get_edge_case_template(description, "empty_data", test_type, framework)
        }
        edge_cases.append(empty_test)
        
        return edge_cases
    
    def _sanitize_name(self, name: str) -> str:
        """Test adını temizle"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    
    # Template Methods
    def _get_login_template(self) -> str:
        return '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class Test{test_name}:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_login(self):
        """Test {description}"""
        try:
            # Navigate to login page
            self.driver.get("https://example.com/login")
            
            # Find and fill username field
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys("test@example.com")
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys("password123")
            
            # Click login button
            login_button = self.driver.find_element(By.ID, "login-button")
            login_button.click()
            
            # Verify successful login
            dashboard = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            
            assert dashboard.is_displayed()
            assert "Welcome" in self.driver.page_source
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_form_template(self) -> str:
        return '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Test{test_name}:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_form_submit(self):
        """Test {description}"""
        try:
            # Navigate to form page
            self.driver.get("https://example.com/form")
            
            # Fill form fields
            name_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "name"))
            )
            name_field.send_keys("Test User")
            
            email_field = self.driver.find_element(By.NAME, "email")
            email_field.send_keys("test@example.com")
            
            # Submit form
            submit_button = self.driver.find_element(By.TYPE, "submit")
            submit_button.click()
            
            # Verify form submission
            success_message = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "success"))
            )
            
            assert success_message.is_displayed()
            assert "successfully" in success_message.text
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_navigation_template(self) -> str:
        return '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Test{test_name}:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_navigation(self):
        """Test {description}"""
        try:
            # Navigate to main page
            self.driver.get("https://example.com")
            
            # Find and click navigation link
            nav_link = self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "{description}"))
            )
            nav_link.click()
            
            # Verify navigation
            page_title = self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            assert "{description}" in page_title.text
            assert self.driver.current_url.endswith("/{test_name}")
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_validation_template(self) -> str:
        return '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Test{test_name}:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_validation(self):
        """Test {description}"""
        try:
            # Navigate to validation page
            self.driver.get("https://example.com/validate")
            
            # Test valid data
            valid_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "valid-field"))
            )
            valid_field.send_keys("valid_data")
            
            # Verify validation passes
            success_indicator = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "valid"))
            )
            assert success_indicator.is_displayed()
            
            # Test invalid data
            valid_field.clear()
            valid_field.send_keys("invalid_data")
            
            # Verify validation fails
            error_indicator = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "error"))
            )
            assert error_indicator.is_displayed()
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_ui_template(self) -> str:
        return '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

class Test{test_name}:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_ui_interaction(self):
        """Test {description}"""
        try:
            # Navigate to UI page
            self.driver.get("https://example.com/ui")
            
            # Find interactive element
            element = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "interactive"))
            )
            
            # Perform interaction
            self.actions.move_to_element(element).click().perform()
            
            # Verify interaction result
            result = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "result"))
            )
            
            assert result.is_displayed()
            assert "interaction" in result.text.lower()
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_api_integration_template(self) -> str:
        return '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json

class Test{test_name}:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_api_integration(self):
        """Test {description}"""
        try:
            # Navigate to page with API integration
            self.driver.get("https://example.com/api-integration")
            
            # Trigger API call
            trigger_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "api-trigger"))
            )
            trigger_button.click()
            
            # Wait for API response
            response_element = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "api-response"))
            )
            
            # Verify API integration
            assert response_element.is_displayed()
            assert "success" in response_element.text.lower()
            
            # Additional API test
            api_response = requests.get("https://api.example.com/data")
            assert api_response.status_code == 200
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_playwright_login_template(self) -> str:
        return '''
import pytest
from playwright.sync_api import sync_playwright

class Test{test_name}:
    def test_{test_name}_login(self):
        """Test {description} with Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            try:
                # Navigate to login page
                page.goto("https://example.com/login")
                
                # Fill login form
                page.fill("#username", "test@example.com")
                page.fill("#password", "password123")
                
                # Click login button
                page.click("#login-button")
                
                # Verify login success
                page.wait_for_selector(".dashboard")
                assert page.is_visible(".dashboard")
                
            finally:
                browser.close()
'''
    
    def _get_playwright_form_template(self) -> str:
        return '''
import pytest
from playwright.sync_api import sync_playwright

class Test{test_name}:
    def test_{test_name}_form(self):
        """Test {description} with Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            try:
                # Navigate to form page
                page.goto("https://example.com/form")
                
                # Fill form
                page.fill("[name='name']", "Test User")
                page.fill("[name='email']", "test@example.com")
                
                # Submit form
                page.click("button[type='submit']")
                
                # Verify submission
                page.wait_for_selector(".success")
                assert page.is_visible(".success")
                
            finally:
                browser.close()
'''
    
    def _get_playwright_navigation_template(self) -> str:
        return '''
import pytest
from playwright.sync_api import sync_playwright

class Test{test_name}:
    def test_{test_name}_navigation(self):
        """Test {description} with Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            try:
                # Navigate to main page
                page.goto("https://example.com")
                
                # Click navigation link
                page.click(f"text={description}")
                
                # Verify navigation
                page.wait_for_selector("h1")
                assert page.is_visible("h1")
                
            finally:
                browser.close()
'''
    
    def _get_mobile_login_template(self) -> str:
        return '''
import pytest
from appium import webdriver
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Test{test_name}:
    def setup_method(self):
        # Appium capabilities
        desired_caps = {{
            'platformName': 'Android',
            'deviceName': 'Android Emulator',
            'app': '/path/to/app.apk',
            'automationName': 'UiAutomator2'
        }}
        
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_mobile_login(self):
        """Test {description} on mobile"""
        try:
            # Find and fill username field
            username_field = self.wait.until(
                EC.presence_of_element_located((MobileBy.ID, "username_field"))
            )
            username_field.send_keys("test@example.com")
            
            # Find and fill password field
            password_field = self.driver.find_element(MobileBy.ID, "password_field")
            password_field.send_keys("password123")
            
            # Tap login button
            login_button = self.driver.find_element(MobileBy.ID, "login_button")
            login_button.click()
            
            # Verify login success
            dashboard = self.wait.until(
                EC.presence_of_element_located((MobileBy.CLASS_NAME, "dashboard"))
            )
            
            assert dashboard.is_displayed()
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_mobile_navigation_template(self) -> str:
        return '''
import pytest
from appium import webdriver
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Test{test_name}:
    def setup_method(self):
        desired_caps = {{
            'platformName': 'Android',
            'deviceName': 'Android Emulator',
            'app': '/path/to/app.apk',
            'automationName': 'UiAutomator2'
        }}
        
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_mobile_navigation(self):
        """Test {description} on mobile"""
        try:
            # Navigate to menu
            menu_button = self.wait.until(
                EC.element_to_be_clickable((MobileBy.ID, "menu_button"))
            )
            menu_button.click()
            
            # Select navigation item
            nav_item = self.wait.until(
                EC.element_to_be_clickable((MobileBy.XPATH, f"//*[@text='{description}']"))
            )
            nav_item.click()
            
            # Verify navigation
            page_title = self.wait.until(
                EC.presence_of_element_located((MobileBy.CLASS_NAME, "page_title"))
            )
            
            assert page_title.is_displayed()
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_gesture_template(self) -> str:
        return '''
import pytest
from appium import webdriver
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Test{test_name}:
    def setup_method(self):
        desired_caps = {{
            'platformName': 'Android',
            'deviceName': 'Android Emulator',
            'app': '/path/to/app.apk',
            'automationName': 'UiAutomator2'
        }}
        
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.wait = WebDriverWait(self.driver, 10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_{test_name}_gesture(self):
        """Test {description} gesture on mobile"""
        try:
            # Find element for gesture
            element = self.wait.until(
                EC.presence_of_element_located((MobileBy.ID, "gesture_element"))
            )
            
            # Perform swipe gesture
            self.driver.swipe(100, 500, 100, 100, 1000)
            
            # Verify gesture result
            result = self.wait.until(
                EC.presence_of_element_located((MobileBy.CLASS_NAME, "gesture_result"))
            )
            
            assert result.is_displayed()
            
        except Exception as e:
            self.driver.save_screenshot(f"test_{test_name}_error.png")
            raise e
'''
    
    def _get_api_get_template(self) -> str:
        return '''
import pytest
import requests
import json

class Test{test_name}:
    def test_{test_name}_get_request(self):
        """Test {description} GET request"""
        try:
            # Make GET request
            response = requests.get("https://api.example.com/data")
            
            # Verify response
            assert response.status_code == 200
            assert response.headers['content-type'] == 'application/json'
            
            # Parse response
            data = response.json()
            assert isinstance(data, dict)
            
            # Verify data structure
            assert 'id' in data
            assert 'name' in data
            
        except Exception as e:
            pytest.fail(f"API test failed: {{str(e)}}")
'''
    
    def _get_api_post_template(self) -> str:
        return '''
import pytest
import requests
import json

class Test{test_name}:
    def test_{test_name}_post_request(self):
        """Test {description} POST request"""
        try:
            # Prepare request data
            payload = {{
                "name": "Test User",
                "email": "test@example.com",
                "message": "Test message"
            }}
            
            headers = {{
                "Content-Type": "application/json"
            }}
            
            # Make POST request
            response = requests.post(
                "https://api.example.com/submit",
                json=payload,
                headers=headers
            )
            
            # Verify response
            assert response.status_code == 201
            assert response.headers['content-type'] == 'application/json'
            
            # Parse response
            data = response.json()
            assert data['success'] == True
            assert 'id' in data
            
        except Exception as e:
            pytest.fail(f"API test failed: {{str(e)}}")
'''
    
    def _get_api_auth_template(self) -> str:
        return '''
import pytest
import requests
import json

class Test{test_name}:
    def test_{test_name}_authentication(self):
        """Test {description} authentication"""
        try:
            # Get authentication token
            auth_response = requests.post("https://api.example.com/auth", json={{
                "username": "testuser",
                "password": "testpass"
            }})
            
            assert auth_response.status_code == 200
            token = auth_response.json()['token']
            
            # Use token for authenticated request
            headers = {{
                "Authorization": f"Bearer {{token}}",
                "Content-Type": "application/json"
            }}
            
            response = requests.get(
                "https://api.example.com/protected",
                headers=headers
            )
            
            assert response.status_code == 200
            
        except Exception as e:
            pytest.fail(f"Authentication test failed: {{str(e)}}")
'''
    
    def _get_api_validation_template(self) -> str:
        return '''
import pytest
import requests
import json
from jsonschema import validate

class Test{test_name}:
    def test_{test_name}_data_validation(self):
        """Test {description} data validation"""
        try:
            # Make API request
            response = requests.get("https://api.example.com/data")
            assert response.status_code == 200
            
            # Validate response schema
            schema = {{
                "type": "object",
                "properties": {{
                    "id": {{"type": "integer"}},
                    "name": {{"type": "string"}},
                    "email": {{"type": "string", "format": "email"}},
                    "created_at": {{"type": "string", "format": "date-time"}}
                }},
                "required": ["id", "name", "email"]
            }}
            
            data = response.json()
            validate(instance=data, schema=schema)
            
            # Additional validation
            assert data['id'] > 0
            assert len(data['name']) > 0
            assert '@' in data['email']
            
        except Exception as e:
            pytest.fail(f"Validation test failed: {{str(e)}}")
'''
    
    def _get_general_template(self, test_type: str, framework: str) -> str:
        return f'''
import pytest

class Test{test_name}:
    def test_{test_name}_general(self):
        """Test {{description}}"""
        try:
            # TODO: Implement {test_type} test using {framework}
            # This is a general template for {test_type} testing with {framework}
            
            # Add your test implementation here
            assert True
            
        except Exception as e:
            pytest.fail(f"Test failed: {{str(e)}}")
'''
    
    def _get_edge_case_template(self, description: str, case_type: str, test_type: str, framework: str) -> str:
        return f'''
import pytest

class Test{self._sanitize_name(description)}EdgeCases:
    def test_{self._sanitize_name(description)}_{case_type}(self):
        """Test {{description}} with {case_type}"""
        try:
            # TODO: Implement edge case test for {case_type}
            # Test type: {test_type}
            # Framework: {framework}
            
            # Add your edge case implementation here
            assert True
            
        except Exception as e:
            pytest.fail(f"Edge case test failed: {{str(e)}}")
'''
    
    def _get_selenium_template(self, feature_type: str) -> str:
        """Selenium template'ini seç"""
        templates = {
            "login": self._get_login_template(),
            "form": self._get_form_template(),
            "navigation": self._get_navigation_template(),
            "validation": self._get_validation_template(),
            "ui_interaction": self._get_ui_template(),
            "api_integration": self._get_api_integration_template()
        }
        return templates.get(feature_type, self._get_general_template("web", "selenium"))
    
    def _get_playwright_template(self, feature_type: str) -> str:
        """Playwright template'ini seç"""
        templates = {
            "login": self._get_playwright_login_template(),
            "form": self._get_playwright_form_template(),
            "navigation": self._get_playwright_navigation_template()
        }
        return templates.get(feature_type, self._get_general_template("web", "playwright"))
    
    def _get_mobile_template(self, feature_type: str) -> str:
        """Mobile template'ini seç"""
        templates = {
            "login": self._get_mobile_login_template(),
            "navigation": self._get_mobile_navigation_template(),
            "gesture": self._get_gesture_template()
        }
        return templates.get(feature_type, self._get_general_template("mobile", "appium"))
    
    def _get_api_template(self, feature_type: str) -> str:
        """API template'ini seç"""
        templates = {
            "get_request": self._get_api_get_template(),
            "post_request": self._get_api_post_template(),
            "authentication": self._get_api_auth_template(),
            "validation": self._get_api_validation_template()
        }
        return templates.get(feature_type, self._get_general_template("api", "requests")) 