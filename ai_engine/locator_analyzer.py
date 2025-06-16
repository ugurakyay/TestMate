"""
AI Locator Analyzer Module
Analyzes web pages and suggests optimal locators for elements
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LocatorSuggestion:
    """Locator suggestion data structure"""
    element_type: str  # 'id', 'xpath', 'css', 'name', 'class'
    locator_value: str
    confidence: float  # 0.0 to 1.0
    reason: str
    alternative_locators: List[Dict[str, str]]

class LocatorAnalyzer:
    """AI-powered locator analyzer for web elements"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the locator analyzer with OpenAI API key"""
        self.api_key = api_key or openai.api_key
        if self.api_key:
            openai.api_key = self.api_key
    
    def analyze_page_locators(self, html_content: str, target_elements: List[str] = None) -> Dict[str, List[LocatorSuggestion]]:
        """Analyze HTML content and suggest optimal locators for elements"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # If no specific elements are targeted, analyze common interactive elements
        if not target_elements:
            target_elements = self._find_interactive_elements(soup)
        
        suggestions = {}
        
        for element_desc in target_elements:
            suggestions[element_desc] = self._suggest_locators_for_element(soup, element_desc)
        
        return suggestions
    
    def _find_interactive_elements(self, soup: BeautifulSoup) -> List[str]:
        """Find common interactive elements in the page"""
        elements = []
        
        # Find buttons
        buttons = soup.find_all(['button', 'input'], type=['button', 'submit'])
        for btn in buttons[:5]:  # Limit to first 5 buttons
            text = btn.get_text(strip=True) or btn.get('value', '') or btn.get('placeholder', '')
            if text:
                elements.append(f"Button: {text}")
        
        # Find links
        links = soup.find_all('a', href=True)
        for link in links[:5]:  # Limit to first 5 links
            text = link.get_text(strip=True)
            if text:
                elements.append(f"Link: {text}")
        
        # Find form inputs
        inputs = soup.find_all('input', type=['text', 'email', 'password'])
        for inp in inputs[:5]:  # Limit to first 5 inputs
            placeholder = inp.get('placeholder', '')
            name = inp.get('name', '')
            if placeholder or name:
                elements.append(f"Input: {placeholder or name}")
        
        return elements
    
    def _suggest_locators_for_element(self, soup: BeautifulSoup, element_desc: str) -> List[LocatorSuggestion]:
        """Suggest locators for a specific element"""
        try:
            if not self.api_key:
                return self._generate_mock_locators(element_desc)
            
            # Find the actual element in the HTML
            element = self._find_element_by_description(soup, element_desc)
            if not element:
                return []
            
            element_html = str(element)
            
            prompt = f"""
            Analyze the following HTML element and suggest the best locators for it:
            
            Element Description: {element_desc}
            HTML: {element_html}
            
            Please suggest locators in order of preference (most reliable first):
            1. ID (if available and unique)
            2. Name attribute (if available)
            3. CSS Selector (specific and reliable)
            4. XPath (if other options are not suitable)
            5. Class name (if unique and meaningful)
            
            For each suggestion, provide:
            - Locator type (id, name, css, xpath, class)
            - Locator value
            - Confidence score (0.0 to 1.0)
            - Reason for the suggestion
            - Alternative locators
            
            Return the suggestions in JSON format:
            {{
                "suggestions": [
                    {{
                        "element_type": "id|name|css|xpath|class",
                        "locator_value": "actual locator value",
                        "confidence": 0.95,
                        "reason": "Why this locator is recommended",
                        "alternative_locators": [
                            {{"type": "css", "value": "alternative locator"}}
                        ]
                    }}
                ]
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return [LocatorSuggestion(**s) for s in result["suggestions"]]
            
        except Exception as e:
            print(f"Error analyzing locators for {element_desc}: {e}")
            return self._generate_mock_locators(element_desc)
    
    def _find_element_by_description(self, soup: BeautifulSoup, element_desc: str) -> Optional[Any]:
        """Find an element based on its description"""
        element_type, text = element_desc.split(": ", 1)
        
        if element_type == "Button":
            return soup.find(['button', 'input'], 
                           string=re.compile(text, re.IGNORECASE)) or \
                   soup.find(['button', 'input'], 
                           value=re.compile(text, re.IGNORECASE))
        
        elif element_type == "Link":
            return soup.find('a', string=re.compile(text, re.IGNORECASE))
        
        elif element_type == "Input":
            return soup.find('input', 
                           placeholder=re.compile(text, re.IGNORECASE)) or \
                   soup.find('input', 
                           name=re.compile(text, re.IGNORECASE))
        
        return None
    
    def _generate_mock_locators(self, element_desc: str) -> List[LocatorSuggestion]:
        """Generate mock locator suggestions when AI is not available"""
        element_type, text = element_desc.split(": ", 1)
        
        mock_suggestions = {
            "Button": [
                LocatorSuggestion(
                    element_type="xpath",
                    locator_value=f"//button[contains(text(), '{text}')]",
                    confidence=0.8,
                    reason="Text-based XPath for button with specific text",
                    alternative_locators=[
                        {"type": "css", "value": f"button:contains('{text}')"},
                        {"type": "xpath", "value": f"//input[@value='{text}']"}
                    ]
                )
            ],
            "Link": [
                LocatorSuggestion(
                    element_type="xpath",
                    locator_value=f"//a[contains(text(), '{text}')]",
                    confidence=0.9,
                    reason="Text-based XPath for link with specific text",
                    alternative_locators=[
                        {"type": "css", "value": f"a:contains('{text}')"},
                        {"type": "xpath", "value": f"//a[text()='{text}']"}
                    ]
                )
            ],
            "Input": [
                LocatorSuggestion(
                    element_type="css",
                    locator_value=f"input[placeholder='{text}']",
                    confidence=0.85,
                    reason="CSS selector using placeholder attribute",
                    alternative_locators=[
                        {"type": "name", "value": text.lower().replace(" ", "_")},
                        {"type": "xpath", "value": f"//input[@placeholder='{text}']"}
                    ]
                )
            ]
        }
        
        return mock_suggestions.get(element_type, [])
    
    def validate_locator(self, html_content: str, locator_type: str, locator_value: str) -> bool:
        """Validate if a locator works correctly"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            if locator_type == "id":
                return soup.find(id=locator_value) is not None
            elif locator_type == "name":
                return soup.find(attrs={"name": locator_value}) is not None
            elif locator_type == "class":
                return soup.find(class_=locator_value) is not None
            elif locator_type == "css":
                return soup.select(locator_value) != []
            elif locator_type == "xpath":
                # Basic XPath validation (simplified)
                return self._validate_xpath(soup, locator_value)
            else:
                return False
        except Exception:
            return False
    
    def _validate_xpath(self, soup: BeautifulSoup, xpath: str) -> bool:
        """Basic XPath validation (simplified implementation)"""
        try:
            # This is a simplified validation - in a real implementation,
            # you would use lxml.etree for proper XPath evaluation
            if xpath.startswith("//"):
                tag_name = xpath.split("/")[2].split("[")[0]
                return soup.find(tag_name) is not None
            return True
        except Exception:
            return False
    
    def save_locator_suggestions(self, suggestions: Dict[str, List[LocatorSuggestion]], filename: str):
        """Save locator suggestions to a JSON file"""
        data = {}
        for element, locators in suggestions.items():
            data[element] = []
            for loc in locators:
                data[element].append({
                    "element_type": loc.element_type,
                    "locator_value": loc.locator_value,
                    "confidence": loc.confidence,
                    "reason": loc.reason,
                    "alternative_locators": loc.alternative_locators
                })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Locator suggestions saved to {filename}") 