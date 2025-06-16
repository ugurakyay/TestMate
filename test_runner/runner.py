import asyncio
import subprocess
import sys
import os
from typing import Dict, Any, List
import json
from datetime import datetime

class TestRunner:
    """Test runner for executing different types of tests"""
    
    def __init__(self):
        self.results = {}
    
    async def run_tests(
        self, 
        test_path: str, 
        test_type: str, 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run tests based on type and parameters
        
        Args:
            test_path: Path to test files or directory
            test_type: Type of tests (web, mobile, api)
            parameters: Additional parameters for test execution
            
        Returns:
            Test execution results
        """
        
        start_time = datetime.now()
        
        try:
            if test_type == "api":
                results = await self._run_api_tests(test_path, parameters)
            elif test_type == "web":
                results = await self._run_web_tests(test_path, parameters)
            elif test_type == "mobile":
                results = await self._run_mobile_tests(test_path, parameters)
            else:
                results = {
                    "success": False,
                    "error": f"Unsupported test type: {test_type}"
                }
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            results.update({
                "execution_time": execution_time,
                "test_type": test_type,
                "test_path": test_path,
                "timestamp": start_time.isoformat()
            })
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0,
                "test_type": test_type,
                "test_path": test_path,
                "timestamp": start_time.isoformat()
            }
    
    async def _run_api_tests(self, test_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run API tests using pytest"""
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=api_test_results.json"
        ]
        
        # Add additional parameters
        if parameters:
            if parameters.get("parallel"):
                cmd.extend(["-n", "auto"])
            if parameters.get("coverage"):
                cmd.extend(["--cov", "--cov-report=html"])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            results = self._parse_pytest_output(stdout.decode(), stderr.decode())
            
            # Try to load JSON report if available
            if os.path.exists("api_test_results.json"):
                with open("api_test_results.json", "r") as f:
                    json_results = json.load(f)
                    results.update(json_results)
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run API tests: {str(e)}",
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
    
    async def _run_web_tests(self, test_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run web tests using pytest with Selenium"""
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=web_test_results.json"
        ]
        
        # Add browser-specific parameters
        if parameters and parameters.get("browser"):
            os.environ["BROWSER"] = parameters["browser"]
        
        # Add headless mode if specified
        if parameters and parameters.get("headless"):
            os.environ["HEADLESS"] = "true"
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            results = self._parse_pytest_output(stdout.decode(), stderr.decode())
            
            # Try to load JSON report if available
            if os.path.exists("web_test_results.json"):
                with open("web_test_results.json", "r") as f:
                    json_results = json.load(f)
                    results.update(json_results)
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run web tests: {str(e)}",
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
    
    async def _run_mobile_tests(self, test_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run mobile tests using pytest with Appium"""
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=mobile_test_results.json"
        ]
        
        # Add device-specific parameters
        if parameters and parameters.get("device"):
            os.environ["DEVICE"] = parameters["device"]
        
        if parameters and parameters.get("platform"):
            os.environ["PLATFORM"] = parameters["platform"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            results = self._parse_pytest_output(stdout.decode(), stderr.decode())
            
            # Try to load JSON report if available
            if os.path.exists("mobile_test_results.json"):
                with open("mobile_test_results.json", "r") as f:
                    json_results = json.load(f)
                    results.update(json_results)
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run mobile tests: {str(e)}",
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse pytest output to extract test results"""
        
        results = {
            "success": True,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "output": stdout,
            "errors_output": stderr
        }
        
        try:
            # Parse the output to count results
            lines = stdout.split('\n')
            
            for line in lines:
                if "PASSED" in line:
                    results["passed"] += 1
                elif "FAILED" in line:
                    results["failed"] += 1
                elif "SKIPPED" in line:
                    results["skipped"] += 1
                elif "ERROR" in line:
                    results["errors"] += 1
            
            # Determine overall success
            total_tests = results["passed"] + results["failed"] + results["skipped"] + results["errors"]
            results["total"] = total_tests
            
            if results["failed"] > 0 or results["errors"] > 0:
                results["success"] = False
            
            # Extract summary if available
            for line in reversed(lines):
                if "failed" in line.lower() and "passed" in line.lower():
                    results["summary"] = line.strip()
                    break
            
        except Exception as e:
            results["success"] = False
            results["error"] = f"Error parsing output: {str(e)}"
        
        return results
    
    async def run_test_suite(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete test suite"""
        
        suite_results = {
            "suite_name": test_suite.get("name", "Unknown Suite"),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "execution_time": 0,
            "test_results": []
        }
        
        start_time = datetime.now()
        
        for test_case in test_suite.get("test_cases", []):
            test_result = await self.run_tests(
                test_path=test_case.get("path", ""),
                test_type=test_case.get("type", "api"),
                parameters=test_case.get("parameters", {})
            )
            
            suite_results["test_results"].append(test_result)
            suite_results["total_tests"] += test_result.get("total", 0)
            suite_results["passed"] += test_result.get("passed", 0)
            suite_results["failed"] += test_result.get("failed", 0)
            suite_results["skipped"] += test_result.get("skipped", 0)
        
        end_time = datetime.now()
        suite_results["execution_time"] = (end_time - start_time).total_seconds()
        
        return suite_results 