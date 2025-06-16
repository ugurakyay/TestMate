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
            }
        }
    
    def generate_test_project(self, scenarios: List[Dict[str, Any]], project_name: str = "automation_project") -> Dict[str, Any]:
        """Excel senaryolarından tam otomasyon projesi oluştur"""
        project_path = os.path.join(self.output_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Proje yapısını oluştur
        project_structure = {
            "project_path": project_path,
            "files_created": [],
            "test_count": len(scenarios),
            "framework": self._detect_framework(scenarios)
        }
        
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
        test_method = []
        test_method.append(f"    def test_{scenario.get('test_id', 'test').lower()}(self):")
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
            test_method.append("            self.driver.save_screenshot(f'screenshots/error_{scenario.get(\"test_id\", \"test\")}.png')")
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