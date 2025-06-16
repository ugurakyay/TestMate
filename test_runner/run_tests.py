"""
Test Runner Module
Executes tests for web, mobile, and API applications
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from appium import webdriver as appium_webdriver
import requests

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    logs: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class TestRunner:
    """Main test runner class"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize test runner with configuration"""
        self.config = config or {}
        self.results = []
        self.driver = None
        
    def run_web_tests(self, test_files: List[str], browser: str = "chrome") -> List[TestResult]:
        """Run web tests using Selenium"""
        print(f"Starting web tests with {browser} browser...")
        
        try:
            self._setup_web_driver(browser)
            results = []
            
            for test_file in test_files:
                if test_file.endswith('.py'):
                    result = self._run_pytest_file(test_file, "web")
                    results.extend(result)
                elif test_file.endswith('.json'):
                    result = self._run_json_test_file(test_file, "web")
                    results.extend(result)
            
            return results
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def run_mobile_tests(self, test_files: List[str], platform: str = "android") -> List[TestResult]:
        """Run mobile tests using Appium"""
        print(f"Starting mobile tests on {platform}...")
        
        try:
            self._setup_mobile_driver(platform)
            results = []
            
            for test_file in test_files:
                if test_file.endswith('.py'):
                    result = self._run_pytest_file(test_file, "mobile")
                    results.extend(result)
                elif test_file.endswith('.json'):
                    result = self._run_json_test_file(test_file, "mobile")
                    results.extend(result)
            
            return results
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def run_api_tests(self, test_files: List[str], base_url: str = "") -> List[TestResult]:
        """Run API tests using requests"""
        print(f"Starting API tests against {base_url}...")
        
        results = []
        
        for test_file in test_files:
            if test_file.endswith('.py'):
                result = self._run_pytest_file(test_file, "api")
                results.extend(result)
            elif test_file.endswith('.json'):
                result = self._run_json_test_file(test_file, "api", base_url)
                results.extend(result)
        
        return results
    
    def _setup_web_driver(self, browser: str):
        """Setup web driver for browser automation"""
        if browser.lower() == "chrome":
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=chrome_options)
        elif browser.lower() == "firefox":
            self.driver = webdriver.Firefox()
        elif browser.lower() == "safari":
            self.driver = webdriver.Safari()
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        
        self.driver.implicitly_wait(10)
    
    def _setup_mobile_driver(self, platform: str):
        """Setup mobile driver for Appium"""
        if platform.lower() == "android":
            desired_caps = {
                'platformName': 'Android',
                'automationName': 'UiAutomator2',
                'deviceName': 'Android Emulator',
                'app': self.config.get('android_app_path', ''),
                'noReset': True
            }
        elif platform.lower() == "ios":
            desired_caps = {
                'platformName': 'iOS',
                'automationName': 'XCUITest',
                'deviceName': 'iPhone Simulator',
                'app': self.config.get('ios_app_path', ''),
                'noReset': True
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        appium_server = self.config.get('appium_server', 'http://localhost:4723/wd/hub')
        self.driver = appium_webdriver.Remote(appium_server, desired_caps)
    
    def _run_pytest_file(self, test_file: str, test_type: str) -> List[TestResult]:
        """Run a pytest file and collect results"""
        results = []
        
        try:
            # Run pytest and capture output
            cmd = [
                sys.executable, "-m", "pytest", 
                test_file, 
                "--json-report", 
                "--json-report-file=none",
                "-v"
            ]
            
            start_time = time.time()
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.path.dirname(test_file)
            )
            duration = time.time() - start_time
            
            # Parse pytest output
            if process.returncode == 0:
                status = "passed"
                error_message = None
            else:
                status = "failed"
                error_message = process.stderr
            
            result = TestResult(
                test_name=f"pytest_{os.path.basename(test_file)}",
                status=status,
                duration=duration,
                error_message=error_message,
                logs=process.stdout
            )
            results.append(result)
            
        except Exception as e:
            result = TestResult(
                test_name=f"pytest_{os.path.basename(test_file)}",
                status="error",
                duration=0,
                error_message=str(e)
            )
            results.append(result)
        
        return results
    
    def _run_json_test_file(self, test_file: str, test_type: str, base_url: str = "") -> List[TestResult]:
        """Run tests from a JSON test file"""
        results = []
        
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            for test_case in test_data:
                start_time = time.time()
                
                try:
                    if test_type == "web":
                        result = self._execute_web_test_case(test_case)
                    elif test_type == "mobile":
                        result = self._execute_mobile_test_case(test_case)
                    elif test_type == "api":
                        result = self._execute_api_test_case(test_case, base_url)
                    else:
                        raise ValueError(f"Unknown test type: {test_type}")
                    
                    duration = time.time() - start_time
                    result.duration = duration
                    results.append(result)
                    
                except Exception as e:
                    duration = time.time() - start_time
                    result = TestResult(
                        test_name=test_case.get('name', 'Unknown'),
                        status="error",
                        duration=duration,
                        error_message=str(e)
                    )
                    results.append(result)
        
        except Exception as e:
            result = TestResult(
                test_name=f"json_{os.path.basename(test_file)}",
                status="error",
                duration=0,
                error_message=f"Failed to load test file: {str(e)}"
            )
            results.append(result)
        
        return results
    
    def _execute_web_test_case(self, test_case: Dict[str, Any]) -> TestResult:
        """Execute a web test case"""
        test_name = test_case.get('name', 'Unknown')
        steps = test_case.get('steps', [])
        expected_result = test_case.get('expected_result', '')
        
        try:
            for step in steps:
                self._execute_web_step(step)
            
            # Take screenshot for successful tests
            screenshot_path = self._take_screenshot(test_name)
            
            return TestResult(
                test_name=test_name,
                status="passed",
                duration=0,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            # Take screenshot for failed tests
            screenshot_path = self._take_screenshot(test_name)
            
            return TestResult(
                test_name=test_name,
                status="failed",
                duration=0,
                error_message=str(e),
                screenshot_path=screenshot_path
            )
    
    def _execute_mobile_test_case(self, test_case: Dict[str, Any]) -> TestResult:
        """Execute a mobile test case"""
        test_name = test_case.get('name', 'Unknown')
        steps = test_case.get('steps', [])
        
        try:
            for step in steps:
                self._execute_mobile_step(step)
            
            # Take screenshot for successful tests
            screenshot_path = self._take_screenshot(test_name)
            
            return TestResult(
                test_name=test_name,
                status="passed",
                duration=0,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            # Take screenshot for failed tests
            screenshot_path = self._take_screenshot(test_name)
            
            return TestResult(
                test_name=test_name,
                status="failed",
                duration=0,
                error_message=str(e),
                screenshot_path=screenshot_path
            )
    
    def _execute_api_test_case(self, test_case: Dict[str, Any], base_url: str) -> TestResult:
        """Execute an API test case"""
        test_name = test_case.get('name', 'Unknown')
        steps = test_case.get('steps', [])
        
        try:
            for step in steps:
                self._execute_api_step(step, base_url)
            
            return TestResult(
                test_name=test_name,
                status="passed",
                duration=0
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                status="failed",
                duration=0,
                error_message=str(e)
            )
    
    def _execute_web_step(self, step: str):
        """Execute a web automation step"""
        # This is a simplified implementation
        # In a real scenario, you would parse the step and execute appropriate Selenium commands
        
        if "navigate" in step.lower():
            # Extract URL from step
            if "http" in step:
                url = step.split("http")[1].split()[0]
                self.driver.get(f"http{url}")
        
        elif "click" in step.lower():
            # Extract element locator from step
            if "button" in step.lower():
                element = self.driver.find_element(By.TAG_NAME, "button")
                element.click()
        
        elif "input" in step.lower() or "type" in step.lower():
            # Extract input field and text from step
            if "username" in step.lower():
                element = self.driver.find_element(By.NAME, "username")
                element.send_keys("testuser")
            elif "password" in step.lower():
                element = self.driver.find_element(By.NAME, "password")
                element.send_keys("testpass")
    
    def _execute_mobile_step(self, step: str):
        """Execute a mobile automation step"""
        # This is a simplified implementation
        # In a real scenario, you would parse the step and execute appropriate Appium commands
        
        if "tap" in step.lower():
            # Extract coordinates or element from step
            pass
        
        elif "swipe" in step.lower():
            # Extract swipe parameters from step
            pass
    
    def _execute_api_step(self, step: str, base_url: str):
        """Execute an API test step"""
        # This is a simplified implementation
        # In a real scenario, you would parse the step and execute appropriate HTTP requests
        
        if "get" in step.lower():
            response = requests.get(base_url)
            response.raise_for_status()
        
        elif "post" in step.lower():
            response = requests.post(base_url, json={})
            response.raise_for_status()
    
    def _take_screenshot(self, test_name: str) -> Optional[str]:
        """Take a screenshot and save it"""
        try:
            if self.driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshots/{test_name}_{timestamp}.png"
                
                # Create screenshots directory if it doesn't exist
                os.makedirs("screenshots", exist_ok=True)
                
                self.driver.save_screenshot(filename)
                return filename
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
        
        return None
    
    def save_results(self, filename: str):
        """Save test results to a JSON file"""
        results_data = [asdict(result) for result in self.results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"Test results saved to {filename}")
    
    def generate_report(self, output_format: str = "html") -> str:
        """Generate test execution report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        error_tests = len([r for r in self.results if r.status == "error"])
        
        if output_format == "html":
            return self._generate_html_report(total_tests, passed_tests, failed_tests, error_tests)
        else:
            return self._generate_text_report(total_tests, passed_tests, failed_tests, error_tests)
    
    def _generate_html_report(self, total: int, passed: int, failed: int, error: int) -> str:
        """Generate HTML test report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Execution Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .error {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Test Execution Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {total}</p>
                <p class="passed">Passed: {passed}</p>
                <p class="failed">Failed: {failed}</p>
                <p class="error">Error: {error}</p>
            </div>
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Error Message</th>
                </tr>
        """
        
        for result in self.results:
            status_class = result.status
            html_content += f"""
                <tr>
                    <td>{result.test_name}</td>
                    <td class="{status_class}">{result.status}</td>
                    <td>{result.duration:.2f}s</td>
                    <td>{result.error_message or ''}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_text_report(self, total: int, passed: int, failed: int, error: int) -> str:
        """Generate text test report"""
        report = f"""
Test Execution Report
====================

Summary:
--------
Total Tests: {total}
Passed: {passed}
Failed: {failed}
Error: {error}

Test Results:
-------------
"""
        
        for result in self.results:
            report += f"{result.test_name}: {result.status} ({result.duration:.2f}s)\n"
            if result.error_message:
                report += f"  Error: {result.error_message}\n"
        
        return report 