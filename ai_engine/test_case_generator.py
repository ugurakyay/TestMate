"""
AI Test Case Generator Module
Generates test cases using AI models for web, mobile, and API testing
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TestCase:
    """Test case data structure"""
    name: str
    description: str
    steps: List[str]
    expected_result: str
    test_type: str  # 'web', 'mobile', 'api'
    priority: str   # 'high', 'medium', 'low'
    tags: List[str]

class TestCaseGenerator:
    """AI-powered test case generator"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the test case generator with OpenAI API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
    
    def generate_web_test_cases(self, page_url: str, page_content: str = "") -> List[TestCase]:
        """Generate web test cases for a given page"""
        prompt = f"""
        Generate comprehensive web test cases for the following page:
        URL: {page_url}
        Content: {page_content[:1000]}...
        
        Please generate test cases covering:
        1. Functional testing
        2. UI/UX testing
        3. Cross-browser compatibility
        4. Responsive design
        5. Accessibility
        
        Return the test cases in JSON format with the following structure:
        {{
            "test_cases": [
                {{
                    "name": "Test case name",
                    "description": "Detailed description",
                    "steps": ["Step 1", "Step 2", ...],
                    "expected_result": "Expected outcome",
                    "priority": "high|medium|low",
                    "tags": ["functional", "ui", ...]
                }}
            ]
        }}
        """
        
        try:
            if not self.api_key:
                return self._generate_mock_test_cases("web", page_url)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            return [TestCase(**tc, test_type="web") for tc in result["test_cases"]]
            
        except Exception as e:
            print(f"Error generating web test cases: {e}")
            return self._generate_mock_test_cases("web", page_url)
    
    def generate_mobile_test_cases(self, app_info: Dict[str, Any]) -> List[TestCase]:
        """Generate mobile test cases for a given app"""
        prompt = f"""
        Generate comprehensive mobile test cases for the following app:
        App Name: {app_info.get('name', 'Unknown')}
        Platform: {app_info.get('platform', 'Unknown')}
        Features: {app_info.get('features', [])}
        
        Please generate test cases covering:
        1. Functional testing
        2. UI/UX testing
        3. Performance testing
        4. Device compatibility
        5. Network conditions
        6. Battery usage
        
        Return the test cases in JSON format.
        """
        
        try:
            if not self.api_key:
                return self._generate_mock_test_cases("mobile", app_info.get('name', 'Unknown'))
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            return [TestCase(**tc, test_type="mobile") for tc in result["test_cases"]]
            
        except Exception as e:
            print(f"Error generating mobile test cases: {e}")
            return self._generate_mock_test_cases("mobile", app_info.get('name', 'Unknown'))
    
    def generate_api_test_cases(self, api_spec: Dict[str, Any]) -> List[TestCase]:
        """Generate API test cases based on API specification"""
        prompt = f"""
        Generate comprehensive API test cases for the following API:
        Base URL: {api_spec.get('base_url', 'Unknown')}
        Endpoints: {api_spec.get('endpoints', [])}
        Methods: {api_spec.get('methods', [])}
        
        Please generate test cases covering:
        1. Positive testing
        2. Negative testing
        3. Boundary value testing
        4. Performance testing
        5. Security testing
        6. Error handling
        
        Return the test cases in JSON format.
        """
        
        try:
            if not self.api_key:
                return self._generate_mock_test_cases("api", api_spec.get('base_url', 'Unknown'))
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            return [TestCase(**tc, test_type="api") for tc in result["test_cases"]]
            
        except Exception as e:
            print(f"Error generating API test cases: {e}")
            return self._generate_mock_test_cases("api", api_spec.get('base_url', 'Unknown'))
    
    def _generate_mock_test_cases(self, test_type: str, target: str) -> List[TestCase]:
        """Generate mock test cases when AI is not available"""
        mock_cases = {
            "web": [
                TestCase(
                    name="Page Load Test",
                    description=f"Verify that {target} loads correctly",
                    steps=["Navigate to the page", "Wait for page to load", "Check page title"],
                    expected_result="Page loads within 3 seconds with correct title",
                    test_type="web",
                    priority="high",
                    tags=["functional", "performance"]
                ),
                TestCase(
                    name="Navigation Test",
                    description="Test main navigation menu",
                    steps=["Click on navigation menu", "Verify all menu items are visible", "Click on each menu item"],
                    expected_result="All navigation items work correctly",
                    test_type="web",
                    priority="high",
                    tags=["functional", "ui"]
                )
            ],
            "mobile": [
                TestCase(
                    name="App Launch Test",
                    description=f"Verify that {target} app launches correctly",
                    steps=["Launch the app", "Wait for splash screen", "Check main screen loads"],
                    expected_result="App launches within 5 seconds",
                    test_type="mobile",
                    priority="high",
                    tags=["functional", "performance"]
                )
            ],
            "api": [
                TestCase(
                    name="Health Check Test",
                    description=f"Verify {target} API health endpoint",
                    steps=["Send GET request to /health", "Check response status", "Validate response format"],
                    expected_result="Returns 200 OK with valid JSON",
                    test_type="api",
                    priority="high",
                    tags=["functional", "health"]
                )
            ]
        }
        
        return mock_cases.get(test_type, [])
    
    def save_test_cases(self, test_cases: List[TestCase], filename: str):
        """Save test cases to a JSON file"""
        data = []
        for tc in test_cases:
            data.append({
                "name": tc.name,
                "description": tc.description,
                "steps": tc.steps,
                "expected_result": tc.expected_result,
                "test_type": tc.test_type,
                "priority": tc.priority,
                "tags": tc.tags
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Test cases saved to {filename}") 