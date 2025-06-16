import openai
import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()

class TestCaseGenerator:
    """AI-powered test case generator using OpenAI"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.ai_enabled = True
        else:
            self.client = None
            self.ai_enabled = False
            print("Warning: OPENAI_API_KEY not found. Using fallback test generation.")
        
        self.model = "gpt-4"
    
    async def generate_test_cases(
        self, 
        feature_description: str, 
        test_type: str, 
        framework: str = None,
        additional_context: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate test cases using AI
        
        Args:
            feature_description: Description of the feature to test
            test_type: Type of test (web, mobile, api)
            framework: Testing framework to use
            additional_context: Additional context for test generation
            
        Returns:
            List of generated test cases
        """
        
        if not self.ai_enabled:
            return await self._generate_fallback_test(feature_description, test_type, framework)
        
        # Build the prompt based on test type
        prompt = self._build_prompt(feature_description, test_type, framework, additional_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert test automation engineer. Generate comprehensive test cases in Python."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            test_cases = await self._parse_response(response.choices[0].message.content, test_type, feature_description, framework)
            return test_cases
            
        except Exception as e:
            print(f"Error generating test cases: {e}")
            # Return a fallback test case
            return await self._generate_fallback_test(feature_description, test_type, framework)
    
    def _build_prompt(self, feature_description: str, test_type: str, framework: str, additional_context: str) -> str:
        """Build the prompt for test generation"""
        
        base_prompt = f"""
        Generate comprehensive test cases for the following feature:
        
        Feature Description: {feature_description}
        Test Type: {test_type}
        Framework: {framework or 'Default'}
        Additional Context: {additional_context or 'None'}
        
        Please generate test cases that include:
        1. Happy path scenarios
        2. Edge cases
        3. Error scenarios
        4. Performance considerations (if applicable)
        
        Format the response as a JSON array with the following structure:
        {{
            "test_cases": [
                {{
                    "name": "Test case name",
                    "description": "Test case description",
                    "steps": ["Step 1", "Step 2", ...],
                    "expected_result": "Expected outcome",
                    "priority": "High/Medium/Low",
                    "code": "Python test code"
                }}
            ]
        }}
        """
        
        # Add framework-specific instructions
        if test_type == "web":
            base_prompt += "\nUse Selenium WebDriver for web testing."
        elif test_type == "mobile":
            base_prompt += "\nUse Appium for mobile testing."
        elif test_type == "api":
            base_prompt += "\nUse requests library for API testing."
        
        return base_prompt
    
    async def _parse_response(self, response: str, test_type: str, feature_description: str = "", framework: str = "") -> List[Dict[str, Any]]:
        """Parse the AI response into structured test cases"""
        try:
            # Try to extract JSON from the response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            return data.get("test_cases", [])
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing response: {e}")
            return await self._generate_fallback_test(feature_description, test_type, framework)
    
    async def _generate_fallback_test(self, feature_description: str, test_type: str, framework: str) -> List[Dict[str, Any]]:
        """Generate a fallback test case when AI generation fails"""
        
        if test_type == "web":
            return [{
                "name": f"Basic {feature_description} Test",
                "description": f"Basic test for {feature_description}",
                "steps": [
                    "Navigate to the application",
                    f"Perform {feature_description} action",
                    "Verify the result"
                ],
                "expected_result": "Feature should work as expected",
                "priority": "High",
                "code": f"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_{feature_description.lower().replace(' ', '_')}():
    driver = webdriver.Chrome()
    try:
        driver.get("https://example.com")
        # Add test implementation here
        assert True
    finally:
        driver.quit()
                """
            }]
        
        elif test_type == "api":
            return [{
                "name": f"API {feature_description} Test",
                "description": f"API test for {feature_description}",
                "steps": [
                    "Send request to endpoint",
                    "Verify response status",
                    "Validate response data"
                ],
                "expected_result": "API should return correct response",
                "priority": "High",
                "code": f"""
import requests

def test_{feature_description.lower().replace(' ', '_')}():
    response = requests.get("https://api.example.com/endpoint")
    assert response.status_code == 200
    # Add more assertions here
                """
            }]
        
        else:  # mobile
            return [{
                "name": f"Mobile {feature_description} Test",
                "description": f"Mobile test for {feature_description}",
                "steps": [
                    "Launch the app",
                    f"Perform {feature_description} action",
                    "Verify the result"
                ],
                "expected_result": "Feature should work on mobile",
                "priority": "High",
                "code": f"""
from appium import webdriver

def test_{feature_description.lower().replace(' ', '_')}():
    # Add Appium test implementation here
    assert True
                """
            }]
    
    async def generate_test_suite(self, features: List[str], test_type: str) -> Dict[str, Any]:
        """Generate a complete test suite for multiple features"""
        
        test_suite = {
            "name": f"{test_type.title()} Test Suite",
            "description": f"Comprehensive test suite for {test_type} testing",
            "test_cases": []
        }
        
        for feature in features:
            test_cases = await self.generate_test_cases(feature, test_type)
            test_suite["test_cases"].extend(test_cases)
        
        return test_suite 