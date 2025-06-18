import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

class CodeGenerator:
    """Excel test senaryolarından otomasyon kodu üreten sınıf"""
    
    def __init__(self):
        self.template_dir = "templates"
        self.output_dir = "generated_tests"
        self.framework_templates = {
            "selenium": {
                "imports": [
                    "from selenium import webdriver",
                    "from selenium.webdriver.common.by import By",
                    "from selenium.webdriver.support.ui import WebDriverWait",
                    "from selenium.webdriver.support import expected_conditions as EC",
                    "from selenium.webdriver.common.keys import Keys",
                    "import time",
                    "import pytest"
                ],
                "setup": "self.driver = webdriver.Chrome()",
                "teardown": "self.driver.quit()",
                "wait": "WebDriverWait(self.driver, 10)"
            },
            "appium": {
                "imports": [
                    "from appium import webdriver",
                    "from appium.webdriver.common.mobileby import MobileBy",
                    "from selenium.webdriver.support.ui import WebDriverWait",
                    "from selenium.webdriver.support import expected_conditions as EC",
                    "import time",
                    "import pytest"
                ],
                "setup": "self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)",
                "teardown": "self.driver.quit()",
                "wait": "WebDriverWait(self.driver, 10)"
            },
            "requests": {
                "imports": [
                    "import requests",
                    "import json",
                    "import pytest",
                    "from typing import Dict, Any"
                ],
                "setup": "self.session = requests.Session()",
                "teardown": "self.session.close()",
                "wait": "time.sleep(1)"
            },
            # Java/Maven framework templates
            "selenium-java": {
                "imports": [
                    "import org.openqa.selenium.WebDriver;",
                    "import org.openqa.selenium.WebElement;",
                    "import org.openqa.selenium.By;",
                    "import org.openqa.selenium.chrome.ChromeDriver;",
                    "import org.openqa.selenium.support.ui.WebDriverWait;",
                    "import org.openqa.selenium.support.ui.ExpectedConditions;",
                    "import org.openqa.selenium.support.PageFactory;",
                    "import org.testng.annotations.*;",
                    "import org.testng.Assert;",
                    "import java.time.Duration;"
                ],
                "setup": "driver = new ChromeDriver();",
                "teardown": "driver.quit();",
                "wait": "new WebDriverWait(driver, Duration.ofSeconds(10))"
            },
            "appium-java": {
                "imports": [
                    "import io.appium.java_client.AppiumDriver;",
                    "import io.appium.java_client.android.AndroidDriver;",
                    "import io.appium.java_client.ios.IOSDriver;",
                    "import org.openqa.selenium.remote.DesiredCapabilities;",
                    "import org.testng.annotations.*;",
                    "import org.testng.Assert;",
                    "import java.net.URL;"
                ],
                "setup": "driver = new AndroidDriver(new URL(\"http://localhost:4723/wd/hub\"), capabilities);",
                "teardown": "driver.quit();",
                "wait": "new WebDriverWait(driver, Duration.ofSeconds(10))"
            },
            "rest-assured": {
                "imports": [
                    "import io.restassured.RestAssured;",
                    "import io.restassured.response.Response;",
                    "import io.restassured.specification.RequestSpecification;",
                    "import org.testng.annotations.*;",
                    "import org.testng.Assert;",
                    "import static io.restassured.RestAssured.*;",
                    "import static org.hamcrest.Matchers.*;"
                ],
                "setup": "RestAssured.baseURI = \"https://api.example.com\";",
                "teardown": "// Cleanup if needed",
                "wait": "// No wait needed for API tests"
            },
            # Modern Framework Templates
            "webdriverio": {
                "imports": [
                    "import { browser, $, $$, expect } from '@wdio/globals'",
                    "import { describe, it, before, after } from '@wdio/mocha-framework'",
                    "import assert from 'assert'"
                ],
                "setup": "await browser.url('https://example.com')",
                "teardown": "await browser.deleteSession()",
                "wait": "await browser.waitUntil(async () => { return await $('selector').isDisplayed() }, { timeout: 10000 })"
            },
            "karate": {
                "imports": [
                    "import com.intuit.karate.junit5.Karate;",
                    "import com.intuit.karate.KarateOptions;",
                    "import org.junit.jupiter.api.Test;",
                    "import static com.intuit.karate.junit5.Karate.run;"
                ],
                "setup": "// Karate setup is done in feature files",
                "teardown": "// Karate teardown is automatic",
                "wait": "// Karate has built-in wait mechanisms"
            },
            "playwright": {
                "imports": [
                    "import { test, expect } from '@playwright/test';",
                    "import { chromium, firefox, webkit } from '@playwright/test';"
                ],
                "setup": "const browser = await chromium.launch(); const page = await browser.newPage();",
                "teardown": "await browser.close();",
                "wait": "await page.waitForSelector('selector', { timeout: 10000 });"
            },
            "cypress": {
                "imports": [
                    "/// <reference types=\"cypress\" />",
                    "describe('Test Suite', () => {",
                    "  beforeEach(() => {",
                    "    cy.visit('https://example.com')",
                    "  })"
                ],
                "setup": "cy.visit('https://example.com')",
                "teardown": "// Cypress cleanup is automatic",
                "wait": "cy.get('selector', { timeout: 10000 }).should('be.visible')"
            }
        }
    
    def generate_test_project(self, scenarios: List[Dict[str, Any]], project_name: str = "automation_project", project_type: str = "python", framework: str = "selenium") -> Dict[str, Any]:
        """Excel senaryolarından tam otomasyon projesi oluştur"""
        project_path = os.path.join(self.output_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Proje yapısını oluştur
        project_structure = {
            "project_path": project_path,
            "files_created": [],
            "test_count": len(scenarios),
            "framework": framework,
            "project_type": project_type
        }
        
        if project_type.lower() == "java":
            self._create_maven_project(project_path, project_name, project_structure, scenarios)
        elif project_type.lower() == "nodejs":
            self._create_nodejs_project(project_path, project_name, project_structure, scenarios)
        else:
            self._create_python_project(project_path, project_structure, scenarios)
        
        return project_structure
    
    def _detect_framework(self, scenarios: List[Dict[str, Any]]) -> str:
        """Test senaryolarından framework türünü tespit et"""
        test_types = set(scenario.get('test_type', '').lower() for scenario in scenarios)
        
        if 'web' in test_types:
            return 'selenium'
        elif 'mobile' in test_types:
            return 'appium'
        elif 'api' in test_types:
            return 'requests'
        else:
            return 'selenium'  # Varsayılan
    
    def _create_requirements_file(self, project_path: str, framework: str):
        """requirements.txt dosyası oluştur"""
        requirements = {
            'selenium': [
                'selenium==4.15.2',
                'pytest==7.4.3',
                'pytest-html==4.1.1',
                'webdriver-manager==4.0.1',
                'pytest-xdist==3.3.1'
            ],
            'appium': [
                'Appium-Python-Client==3.1.1',
                'pytest==7.4.3',
                'pytest-html==4.1.1',
                'pytest-xdist==3.3.1'
            ],
            'requests': [
                'requests==2.31.0',
                'pytest==7.4.3',
                'pytest-html==4.1.1',
                'pytest-xdist==3.3.1'
            ]
        }
        
        with open(os.path.join(project_path, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(requirements.get(framework, requirements['selenium'])))
    
    def _create_config_file(self, project_path: str, framework: str):
        """Konfigürasyon dosyası oluştur"""
        config_content = f'''# Otomasyon Projesi Konfigürasyonu
# Framework: {framework.upper()}

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
    ANDROID_CAPS = {{
        "platformName": "Android",
        "platformVersion": "11.0",
        "deviceName": "Android Emulator",
        "automationName": "UiAutomator2",
        "app": "path/to/your/app.apk"
    }}
    
    IOS_CAPS = {{
        "platformName": "iOS",
        "platformVersion": "15.0",
        "deviceName": "iPhone Simulator",
        "automationName": "XCUITest",
        "app": "path/to/your/app.app"
    }}
    
    # API ayarları
    BASE_URL = "https://api.example.com"
    API_TIMEOUT = 30
    
    # Test verileri
    TEST_DATA = {{
        "valid_user": {{
            "email": "test@example.com",
            "password": "123456"
        }},
        "invalid_user": {{
            "email": "invalid@example.com",
            "password": "wrong"
        }}
    }}
    
    # Rapor ayarları
    REPORT_DIR = "reports"
    SCREENSHOT_DIR = "screenshots"
    
    @classmethod
    def get_driver_caps(cls) -> Dict[str, Any]:
        """Driver capabilities döndür"""
        if framework == "appium":
            return cls.ANDROID_CAPS
        return {{}}
'''
        
        with open(os.path.join(project_path, "config.py"), "w", encoding="utf-8") as f:
            f.write(config_content)
    
    def _create_setup_script(self, project_path: str, framework: str):
        """Otomatik kurulum scripti oluştur"""
        if os.name == 'nt':  # Windows
            setup_content = f'''@echo off
echo ========================================
echo AI Test Tool - Otomatik Kurulum
echo ========================================
echo.

echo Python kontrol ediliyor...
python --version
if %errorlevel% neq 0 (
    echo HATA: Python bulunamadı! Lütfen Python 3.8+ yükleyin.
    pause
    exit /b 1
)

echo.
echo Virtual environment oluşturuluyor...
python -m venv venv
if %errorlevel% neq 0 (
    echo HATA: Virtual environment oluşturulamadı!
    pause
    exit /b 1
)

echo.
echo Virtual environment aktifleştiriliyor...
call venv\\Scripts\\activate.bat

echo.
echo Dependencies yükleniyor...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Kurulum tamamlandı!
echo.
echo Testleri çalıştırmak için:
echo 1. venv\\Scripts\\activate.bat
echo 2. python run_tests.py
echo.
pause
'''
            setup_file = "setup.bat"
        else:  # Unix/Linux/Mac
            setup_content = f'''#!/bin/bash

echo "========================================"
echo "AI Test Tool - Otomatik Kurulum"
echo "========================================"
echo

echo "Python kontrol ediliyor..."
python3 --version
if [ $? -ne 0 ]; then
    echo "HATA: Python bulunamadı! Lütfen Python 3.8+ yükleyin."
    exit 1
fi

echo
echo "Virtual environment oluşturuluyor..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "HATA: Virtual environment oluşturulamadı!"
    exit 1
fi

echo
echo "Virtual environment aktifleştiriliyor..."
source venv/bin/activate

echo
echo "Dependencies yükleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Kurulum tamamlandı!"
echo
echo "Testleri çalıştırmak için:"
echo "1. source venv/bin/activate"
echo "2. python run_tests.py"
echo
'''
            setup_file = "setup.sh"
        
        with open(os.path.join(project_path, setup_file), "w", encoding="utf-8") as f:
            f.write(setup_content)
        
        # Make executable (Unix/Linux/Mac only)
        if os.name != 'nt':  # Not Windows
            os.chmod(os.path.join(project_path, setup_file), 0o755)
        
        return setup_file
    
    def _generate_test_file(self, project_path: str, scenario: Dict[str, Any], framework: str) -> str:
        """Tek bir test senaryosu için test dosyası oluştur"""
        test_id = scenario.get('test_id', 'test')
        test_name = scenario.get('test_name', 'Test')
        
        # Test sınıf adını oluştur
        class_name = self._generate_class_name(test_name)
        
        # Test metodunu oluştur
        test_method = self._generate_test_method(scenario, framework)
        
        # Tam test dosyası içeriğini oluştur
        test_content = self._generate_test_file_content(class_name, test_method, framework)
        
        # Dosyayı kaydet
        filename = f"test_{test_id.lower()}.py"
        filepath = os.path.join(project_path, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        return filename
    
    def _generate_class_name(self, test_name: str) -> str:
        """Test adından sınıf adı oluştur"""
        # Özel karakterleri temizle ve camelCase yap
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', test_name)
        words = clean_name.split()
        class_name = ''.join(word.capitalize() for word in words)
        return f"Test{class_name}"
    
    def _generate_test_method(self, scenario: Dict[str, Any], framework: str) -> str:
        """Test metodunu oluştur"""
        test_id = scenario.get('test_id', 'test')
        test_method = []
        test_method.append(f"    def test_{test_id.lower()}(self):")
        test_method.append(f'        """{scenario.get("test_description", "Test açıklaması")}"""')
        test_method.append("        try:")
        
        # Test adımlarını işle
        for step in scenario.get('steps', []):
            step_code = self._generate_step_code(step, framework)
            test_method.extend([f"            {line}" for line in step_code])
        
        # Assertion ekle
        test_method.append("            # Test başarılı")
        test_method.append("            assert True")
        test_method.append("        except Exception as e:")
        test_method.append("            # Hata durumunda ekran görüntüsü al")
        if framework == 'selenium':
            test_method.append(f"            self.driver.save_screenshot(f'screenshots/error_{test_id}.png')")
        test_method.append("            raise e")
        
        return "\n".join(test_method)
    
    def _generate_step_code(self, step: Dict[str, Any], framework: str) -> List[str]:
        """Tek bir test adımı için kod oluştur"""
        action = step.get('action', '').lower()
        locator_type = step.get('locator_type', '').lower()
        locator_value = step.get('locator_value', '')
        test_data = step.get('test_data', '')
        
        code_lines = []
        
        if action == 'aç':
            if framework == 'selenium':
                code_lines.append(f"self.driver.get('{test_data}')")
            elif framework == 'appium':
                code_lines.append(f"# Uygulama zaten açık")
            elif framework == 'requests':
                code_lines.append(f"response = self.session.get('{test_data}')")
                code_lines.append("assert response.status_code == 200")
        
        elif action == 'tıkla':
            if locator_value:
                element_code = self._get_element_code(locator_type, locator_value, framework)
                code_lines.append(f"element = {element_code}")
                code_lines.append("element.click()")
        
        elif action == 'yaz':
            if locator_value and test_data:
                element_code = self._get_element_code(locator_type, locator_value, framework)
                code_lines.append(f"element = {element_code}")
                code_lines.append(f"element.clear()")
                code_lines.append(f"element.send_keys('{test_data}')")
        
        elif action == 'bekle':
            if framework == 'selenium':
                code_lines.append("time.sleep(2)")
            elif framework == 'appium':
                code_lines.append("time.sleep(2)")
            elif framework == 'requests':
                code_lines.append("time.sleep(1)")
        
        elif action == 'seç':
            if locator_value and test_data:
                element_code = self._get_element_code(locator_type, locator_value, framework)
                code_lines.append(f"element = {element_code}")
                code_lines.append(f"element.click()")
                # Dropdown seçimi için ek kod eklenebilir
        
        # Beklenen sonuç kontrolü
        expected_result = step.get('expected_result', '')
        if expected_result:
            code_lines.append(f"# Beklenen sonuç: {expected_result}")
        
        return code_lines
    
    def _get_element_code(self, locator_type: str, locator_value: str, framework: str) -> str:
        """Element bulma kodu oluştur"""
        if framework == 'selenium':
            locator_map = {
                'id': 'By.ID',
                'class': 'By.CLASS_NAME',
                'xpath': 'By.XPATH',
                'css': 'By.CSS_SELECTOR',
                'name': 'By.NAME',
                'link': 'By.LINK_TEXT'
            }
            by_type = locator_map.get(locator_type, 'By.ID')
            return f"self.wait.until(EC.element_to_be_clickable(({by_type}, '{locator_value}')))"
        
        elif framework == 'appium':
            locator_map = {
                'id': 'MobileBy.ID',
                'class': 'MobileBy.CLASS_NAME',
                'xpath': 'MobileBy.XPATH',
                'css': 'MobileBy.CSS_SELECTOR',
                'name': 'MobileBy.NAME',
                'link': 'MobileBy.LINK_TEXT'
            }
            by_type = locator_map.get(locator_type, 'MobileBy.ID')
            return f"self.wait.until(EC.element_to_be_clickable(({by_type}, '{locator_value}')))"
        
        else:
            return f"# Element bulma kodu: {locator_type} = '{locator_value}'"
    
    def _generate_test_file_content(self, class_name: str, test_method: str, framework: str) -> str:
        """Tam test dosyası içeriğini oluştur"""
        imports = self.framework_templates[framework]["imports"]
        setup = self.framework_templates[framework]["setup"]
        teardown = self.framework_templates[framework]["teardown"]
        wait = self.framework_templates[framework]["wait"]
        
        content = f'''{chr(10).join(imports)}

from config import Config


class {class_name}:
    """{class_name} test sınıfı"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        {setup}
        self.wait = {wait}
    
    def teardown_method(self):
        """Her test sonrası çalışır"""
        {teardown}
    
{test_method}
'''
        return content
    
    def _create_readme_file(self, project_path: str, project_structure: Dict[str, Any]):
        """README.md dosyası oluştur"""
        readme_content = f'''# Otomasyon Projesi

Bu proje, AI Test Tool tarafından otomatik olarak oluşturulmuştur.

## Proje Bilgileri

- **Framework**: {project_structure["framework"].upper()}
- **Test Sayısı**: {project_structure["test_count"]}
- **Oluşturulma Tarihi**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Kurulum

1. Python 3.8+ yüklü olduğundan emin olun
2. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Test Çalıştırma

### Tüm testleri çalıştır:
```bash
pytest
```

### Belirli bir testi çalıştır:
```bash
pytest test_tc001.py
```

### HTML rapor ile çalıştır:
```bash
pytest --html=reports/report.html
```

## Proje Yapısı

```
{project_structure["project_path"]}/
├── requirements.txt      # Gerekli paketler
├── config.py            # Konfigürasyon dosyası
├── test_*.py           # Test dosyaları
├── README.md           # Bu dosya
└── reports/            # Test raporları
```

## Konfigürasyon

`config.py` dosyasından aşağıdaki ayarları yapabilirsiniz:

- Tarayıcı türü (Selenium için)
- Bekleme süreleri
- Test verileri
- API endpoint'leri

## Notlar

- Test çalıştırmadan önce `config.py` dosyasındaki ayarları kontrol edin
- Mobil testler için Appium Server'ın çalışır durumda olduğundan emin olun
- API testleri için doğru endpoint URL'lerini ayarlayın

## Destek

Sorunlar için AI Test Tool'u kullanabilirsiniz.
'''
        
        with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)
    
    def _create_test_runner(self, project_path: str, framework: str) -> str:
        """Test runner script'i oluştur"""
        runner_content = f'''#!/usr/bin/env python3
"""
Test Runner Script
Framework: {framework.upper()}
"""

import pytest
import sys
import os
from datetime import datetime

def main():
    """Ana test runner fonksiyonu"""
    
    # Rapor dizinini oluştur
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    
    # Ekran görüntüsü dizinini oluştur
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Test argümanları
    args = [
        "--verbose",
        f"--html={{report_dir}}/report_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.html",
        "--self-contained-html",
        "--tb=short"
    ]
    
    # Komut satırı argümanlarını ekle
    args.extend(sys.argv[1:])
    
    # Testleri çalıştır
    exit_code = pytest.main(args)
    
    print(f"\\nTest çalıştırma tamamlandı. Çıkış kodu: {{exit_code}}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
'''
        
        runner_path = os.path.join(project_path, "run_tests.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(runner_content)
        
        # Çalıştırılabilir yap
        os.chmod(runner_path, 0o755)
        
        return "run_tests.py"

    def _create_maven_project(self, project_path: str, project_name: str, project_structure: Dict[str, Any], scenarios: List[Dict[str, Any]]):
        """Maven projesi oluştur"""
        # Maven dizin yapısını oluştur
        src_main_java = os.path.join(project_path, "src", "main", "java")
        src_test_java = os.path.join(project_path, "src", "test", "java")
        src_main_resources = os.path.join(project_path, "src", "main", "resources")
        src_test_resources = os.path.join(project_path, "src", "test", "resources")
        
        os.makedirs(src_main_java, exist_ok=True)
        os.makedirs(src_test_java, exist_ok=True)
        os.makedirs(src_main_resources, exist_ok=True)
        os.makedirs(src_test_resources, exist_ok=True)
        
        # pom.xml oluştur
        self._create_pom_xml(project_path, project_name, project_structure["framework"])
        project_structure["files_created"].append("pom.xml")
        
        # Test dosyalarını oluştur
        package_name = f"com.testmate.{project_name.lower().replace('-', '').replace('_', '')}"
        test_package_path = os.path.join(src_test_java, *package_name.split('.'))
        os.makedirs(test_package_path, exist_ok=True)
        
        for scenario in scenarios:
            test_file = self._generate_java_test_file(test_package_path, scenario, project_structure["framework"], package_name)
            project_structure["files_created"].append(test_file)
        
        # TestNG XML oluştur
        self._create_testng_xml(project_path, package_name)
        project_structure["files_created"].append("testng.xml")
        
        # README dosyası oluştur
        self._create_java_readme_file(project_path, project_structure)
        project_structure["files_created"].append("README.md")
        
        # Config dosyası oluştur
        self._create_java_config_file(src_test_resources, project_structure["framework"])
        project_structure["files_created"].append("src/test/resources/config.properties")
    
    def _create_pom_xml(self, project_path: str, project_name: str, framework: str):
        """Maven pom.xml dosyası oluştur"""
        pom_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.testmate</groupId>
    <artifactId>{project_name.lower().replace(' ', '-')}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>{project_name}</name>
    <description>TestMate Studio Generated Test Project</description>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <selenium.version>4.15.0</selenium.version>
        <testng.version>7.7.1</testng.version>
        <appium.version>8.5.1</appium.version>
        <restassured.version>5.3.0</restassured.version>
        <webdrivermanager.version>5.5.3</webdrivermanager.version>
    </properties>

    <dependencies>
        <!-- TestNG -->
        <dependency>
            <groupId>org.testng</groupId>
            <artifactId>testng</artifactId>
            <version>${{testng.version}}</version>
            <scope>test</scope>
        </dependency>

        <!-- Selenium WebDriver -->
        <dependency>
            <groupId>org.seleniumhq.selenium</groupId>
            <artifactId>selenium-java</artifactId>
            <version>${{selenium.version}}</version>
        </dependency>

        <!-- WebDriverManager -->
        <dependency>
            <groupId>io.github.bonigarcia</groupId>
            <artifactId>webdrivermanager</artifactId>
            <version>${{webdrivermanager.version}}</version>
        </dependency>'''

        # Framework-specific dependencies
        if framework == "appium-java":
            pom_content += '''

        <!-- Appium Java Client -->
        <dependency>
            <groupId>io.appium</groupId>
            <artifactId>java-client</artifactId>
            <version>${appium.version}</version>
        </dependency>'''
        elif framework == "rest-assured":
            pom_content += '''

        <!-- REST Assured -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <version>${restassured.version}</version>
            <scope>test</scope>
        </dependency>
        
        <!-- JSON Path -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>json-path</artifactId>
            <version>${restassured.version}</version>
            <scope>test</scope>
        </dependency>
        
        <!-- XML Path -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>xml-path</artifactId>
            <version>${restassured.version}</version>
            <scope>test</scope>
        </dependency>'''
        elif framework == "karate":
            pom_content += '''

        <!-- Karate Framework -->
        <dependency>
            <groupId>com.intuit.karate</groupId>
            <artifactId>karate-junit5</artifactId>
            <version>1.4.1</version>
            <scope>test</scope>
        </dependency>
        
        <!-- Karate Netty -->
        <dependency>
            <groupId>com.intuit.karate</groupId>
            <artifactId>karate-netty</artifactId>
            <version>1.4.1</version>
            <scope>test</scope>
        </dependency>'''

        pom_content += '''

        <!-- Logging -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>2.0.7</version>
        </dependency>
        
        <dependency>
            <groupId>ch.qos.logback</groupId>
            <artifactId>logback-classic</artifactId>
            <version>1.4.7</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Maven Compiler Plugin -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>

            <!-- Maven Surefire Plugin for TestNG -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
                <configuration>
                    <suiteXmlFiles>
                        <suiteXmlFile>testng.xml</suiteXmlFile>
                    </suiteXmlFiles>
                    <parallel>methods</parallel>
                    <threadCount>2</threadCount>
                </configuration>
            </plugin>

            <!-- Maven Failsafe Plugin -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-failsafe-plugin</artifactId>
                <version>3.1.2</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>integration-test</goal>
                            <goal>verify</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>'''

        with open(os.path.join(project_path, "pom.xml"), "w", encoding="utf-8") as f:
            f.write(pom_content)
    
    def _create_testng_xml(self, project_path: str, package_name: str):
        """TestNG XML dosyası oluştur"""
        testng_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">
<suite name="TestMate Suite" parallel="methods" thread-count="2">
    <test name="TestMate Tests">
        <classes>
            <class name="{package_name}.*"/>
        </classes>
    </test>
</suite>'''

        with open(os.path.join(project_path, "testng.xml"), "w", encoding="utf-8") as f:
            f.write(testng_content)
    
    def _create_java_config_file(self, resources_path: str, framework: str):
        """Java konfigürasyon dosyası oluştur"""
        config_content = f'''# TestMate Studio Configuration
# Framework: {framework}

# Browser Configuration
browser=chrome
headless=false
implicit.wait=10
explicit.wait=10
page.load.timeout=30

# Appium Configuration
appium.server=http://localhost:4723/wd/hub
android.platform=Android
android.version=11.0
android.device=Android Emulator
android.automation=UiAutomator2

# API Configuration
api.base.url=https://api.example.com
api.timeout=30

# Test Data
test.data.valid.email=test@example.com
test.data.valid.password=123456
test.data.invalid.email=invalid@example.com
test.data.invalid.password=wrong

# Report Configuration
report.dir=target/reports
screenshot.dir=target/screenshots'''

        with open(os.path.join(resources_path, "config.properties"), "w", encoding="utf-8") as f:
            f.write(config_content)
    
    def _generate_java_test_file(self, test_package_path: str, scenario: Dict[str, Any], framework: str, package_name: str) -> str:
        """Java test dosyası oluştur"""
        test_name = scenario.get('test_name', 'TestScenario')
        class_name = self._generate_java_class_name(test_name)
        
        # Framework'a göre Java framework'ünü belirle
        java_framework = self._get_java_framework(framework)
        
        # Test metodunu oluştur
        test_method = self._generate_java_test_method(scenario, java_framework)
        
        # Test dosyası içeriğini oluştur
        test_content = self._generate_java_test_file_content(class_name, test_method, java_framework, package_name)
        
        # Dosyayı kaydet
        file_path = os.path.join(test_package_path, f"{class_name}.java")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        return f"src/test/java/{package_name.replace('.', '/')}/{class_name}.java"
    
    def _get_java_framework(self, framework: str) -> str:
        """Framework'ü Java karşılığına çevir"""
        framework_map = {
            "selenium": "selenium-java",
            "appium": "appium-java",
            "requests": "rest-assured"
        }
        return framework_map.get(framework, "selenium-java")
    
    def _generate_java_class_name(self, test_name: str) -> str:
        """Java sınıf adı oluştur"""
        # Test adından geçerli Java sınıf adı oluştur
        class_name = re.sub(r'[^a-zA-Z0-9]', '', test_name)
        if not class_name[0].isalpha():
            class_name = "Test" + class_name
        return class_name + "Test"
    
    def _generate_java_test_method(self, scenario: Dict[str, Any], framework: str) -> str:
        """Java test metodu oluştur"""
        test_steps = scenario.get('steps', [])
        method_content = []
        
        if framework == "selenium-java":
            method_content.extend([
                "    @Test",
                "    public void testScenario() {",
                "        try {",
                "            // Test setup",
                "            driver.manage().window().maximize();",
                "            driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));"
            ])
            
            for step in test_steps:
                step_code = self._generate_java_step_code(step, framework)
                method_content.extend(step_code)
            
            method_content.extend([
                "        } catch (Exception e) {",
                "            Assert.fail(\"Test failed: \" + e.getMessage());",
                "        }",
                "    }"
            ])
        
        elif framework == "appium-java":
            method_content.extend([
                "    @Test",
                "    public void testScenario() {",
                "        try {",
                "            // Test setup"
            ])
            
            for step in test_steps:
                step_code = self._generate_java_step_code(step, framework)
                method_content.extend(step_code)
            
            method_content.extend([
                "        } catch (Exception e) {",
                "            Assert.fail(\"Test failed: \" + e.getMessage());",
                "        }",
                "    }"
            ])
        
        elif framework == "rest-assured":
            method_content.extend([
                "    @Test",
                "    public void testScenario() {",
                "        try {",
                "            // Test setup"
            ])
            
            for step in test_steps:
                step_code = self._generate_java_step_code(step, framework)
                method_content.extend(step_code)
            
            method_content.extend([
                "        } catch (Exception e) {",
                "            Assert.fail(\"Test failed: \" + e.getMessage());",
                "        }",
                "    }"
            ])
        
        return "\n".join(method_content)
    
    def _generate_java_step_code(self, step: Dict[str, Any], framework: str) -> List[str]:
        """Java adım kodu oluştur"""
        action = step.get('action', '').lower()
        element = step.get('element', '')
        value = step.get('value', '')
        
        code_lines = []
        
        if framework == "selenium-java":
            if 'click' in action:
                code_lines.append(f"            // Click on {element}")
                code_lines.append(f"            WebElement {element.lower().replace(' ', '_')} = driver.findElement(By.xpath(\"//*[contains(text(),'{element}')]\"));")
                code_lines.append(f"            {element.lower().replace(' ', '_')}.click();")
            elif 'input' in action or 'type' in action:
                code_lines.append(f"            // Input text: {value}")
                code_lines.append(f"            WebElement inputField = driver.findElement(By.name(\"input\"));")
                code_lines.append(f"            inputField.clear();")
                code_lines.append(f"            inputField.sendKeys(\"{value}\");")
            elif 'verify' in action or 'assert' in action:
                code_lines.append(f"            // Verify: {element}")
                code_lines.append(f"            WebElement verifyElement = driver.findElement(By.xpath(\"//*[contains(text(),'{element}')]\"));")
                code_lines.append(f"            Assert.assertTrue(verifyElement.isDisplayed(), \"Element {element} should be displayed\");")
        
        elif framework == "appium-java":
            if 'click' in action:
                code_lines.append(f"            // Click on {element}")
                code_lines.append(f"            driver.findElement(By.xpath(\"//*[@text='{element}']\")).click();")
            elif 'input' in action or 'type' in action:
                code_lines.append(f"            // Input text: {value}")
                code_lines.append(f"            driver.findElement(By.className(\"android.widget.EditText\")).sendKeys(\"{value}\");")
            elif 'verify' in action or 'assert' in action:
                code_lines.append(f"            // Verify: {element}")
                code_lines.append(f"            WebElement verifyElement = driver.findElement(By.xpath(\"//*[@text='{element}']\"));")
                code_lines.append(f"            Assert.assertTrue(verifyElement.isDisplayed(), \"Element {element} should be displayed\");")
        
        elif framework == "rest-assured":
            if 'get' in action:
                code_lines.append(f"            // GET request")
                code_lines.append(f"            Response response = given()")
                code_lines.append(f"                .when()")
                code_lines.append(f"                .get(\"/api/endpoint\")")
                code_lines.append(f"                .then()")
                code_lines.append(f"                .statusCode(200)")
                code_lines.append(f"                .extract().response();")
            elif 'post' in action:
                code_lines.append(f"            // POST request")
                code_lines.append(f"            Response response = given()")
                code_lines.append(f"                .contentType(\"application/json\")")
                code_lines.append(f"                .body(\"{value}\")")
                code_lines.append(f"                .when()")
                code_lines.append(f"                .post(\"/api/endpoint\")")
                code_lines.append(f"                .then()")
                code_lines.append(f"                .statusCode(201)")
                code_lines.append(f"                .extract().response();")
        
        return code_lines
    
    def _generate_java_test_file_content(self, class_name: str, test_method: str, framework: str, package_name: str) -> str:
        """Java test dosyası içeriği oluştur"""
        template = self.framework_templates.get(framework, self.framework_templates["selenium-java"])
        
        imports = "\n".join(template["imports"])
        setup = template["setup"]
        teardown = template["teardown"]
        
        if framework == "selenium-java":
            content = f'''package {package_name};

{imports}

public class {class_name} {{
    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {{
        {setup}
        wait = {template["wait"]};
    }}

    @AfterMethod
    public void tearDown() {{
        {teardown}
    }}

{test_method}
}}'''
        
        elif framework == "appium-java":
            content = f'''package {package_name};

{imports}

public class {class_name} {{
    private AppiumDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {{
        DesiredCapabilities capabilities = new DesiredCapabilities();
        capabilities.setCapability("platformName", "Android");
        capabilities.setCapability("platformVersion", "11.0");
        capabilities.setCapability("deviceName", "Android Emulator");
        capabilities.setCapability("automationName", "UiAutomator2");
        
        {setup}
        wait = {template["wait"]};
    }}

    @AfterMethod
    public void tearDown() {{
        {teardown}
    }}

{test_method}
}}'''
        
        elif framework == "rest-assured":
            content = f'''package {package_name};

{imports}

public class {class_name} {{
    
    @BeforeMethod
    public void setUp() {{
        {setup}
    }}

    @AfterMethod
    public void tearDown() {{
        {teardown}
    }}

{test_method}
}}'''
        
        return content
    
    def _create_java_readme_file(self, project_path: str, project_structure: Dict[str, Any]):
        """Java projesi için README dosyası oluştur"""
        readme_content = f'''# {project_structure.get("project_name", "TestMate Project")}

Bu proje TestMate Studio tarafından otomatik olarak oluşturulmuştur.

## Proje Bilgileri

- **Framework**: {project_structure["framework"]}
- **Proje Türü**: Java/Maven
- **Test Sayısı**: {project_structure["test_count"]}
- **Oluşturulan Dosyalar**: {len(project_structure["files_created"])}

## Gereksinimler

- Java 11 veya üzeri
- Maven 3.6 veya üzeri
- Chrome WebDriver (Selenium için)
- Appium Server (Mobil testler için)

## Kurulum

1. Projeyi klonlayın veya indirin
2. Maven dependencies'leri yükleyin:
   ```bash
   mvn clean install
   ```

## Testleri Çalıştırma

### Tüm Testleri Çalıştırma
```bash
mvn test
```

### TestNG XML ile Çalıştırma
```bash
mvn test -DsuiteXmlFile=testng.xml
```

### Belirli Test Sınıfını Çalıştırma
```bash
mvn test -Dtest=TestClassName
```

## Proje Yapısı

```
src/
├── main/
│   ├── java/          # Ana Java kaynak kodları
│   └── resources/     # Kaynak dosyaları
└── test/
    ├── java/          # Test Java kaynak kodları
    └── resources/     # Test kaynak dosyaları
        └── config.properties  # Test konfigürasyonu
```

## Konfigürasyon

Test ayarlarını `src/test/resources/config.properties` dosyasından düzenleyebilirsiniz.

## Raporlar

Test raporları `target/reports` klasöründe oluşturulur.

## Destek

TestMate Studio ile oluşturulan bu proje için destek almak için:
- Dokümantasyonu inceleyin
- TestMate Studio'yu kullanın
- Gerekirse ek test senaryoları ekleyin

---
*TestMate Studio tarafından oluşturuldu - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''

        with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_python_project(self, project_path: str, project_structure: Dict[str, Any], scenarios: List[Dict[str, Any]]):
        """Python projesi oluştur"""
        # requirements.txt oluştur
        self._create_requirements_file(project_path, project_structure["framework"])
        project_structure["files_created"].append("requirements.txt")
        
        # Setup script oluştur
        setup_file = self._create_setup_script(project_path, project_structure["framework"])
        project_structure["files_created"].append(setup_file)
        
        # config dosyası oluştur
        self._create_config_file(project_path, project_structure["framework"])
        project_structure["files_created"].append("config.py")
        
        # Test dosyalarını oluştur
        for scenario in scenarios:
            test_file = self._generate_test_file(project_path, scenario, project_structure["framework"])
            project_structure["files_created"].append(test_file)
        
        # README dosyası oluştur
        self._create_readme_file(project_path, project_structure)
        project_structure["files_created"].append("README.md")
        
        # Test runner oluştur
        runner_file = self._create_test_runner(project_path, project_structure["framework"])
        project_structure["files_created"].append(runner_file) 