import openai
import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

load_dotenv()

class LocatorAnalyzer:
    """AI-powered locator analyzer for web elements"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.ai_enabled = True
        else:
            self.client = None
            self.ai_enabled = False
            print("Warning: OPENAI_API_KEY not found. Using fallback locator analysis.")
        
        self.model = "gpt-4"
    
    async def analyze_locators(
        self, 
        page_source: str, 
        element_description: str, 
        preferred_locator_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze page source and suggest locators for elements
        
        Args:
            page_source: HTML page source
            element_description: Description of the element to locate
            preferred_locator_type: Preferred locator type (id, class, xpath, css, etc.)
            
        Returns:
            List of suggested locators
        """
        
        print(f"Analyzing locators for element description: '{element_description}'")
        print(f"Page source length: {len(page_source)} characters")
        print(f"AI enabled: {self.ai_enabled}")
        
        if not self.ai_enabled:
            print("Using fallback locator analysis")
            return self._generate_fallback_locators(page_source, element_description)
        
        # Parse HTML and extract relevant elements
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Build the prompt for AI analysis
        prompt = self._build_prompt(page_source, element_description, preferred_locator_type)
        
        try:
            print("Sending request to AI for locator analysis...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert web automation engineer. Analyze HTML and suggest the best locators for elements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            print("Received response from AI")
            # Parse the response
            locators = self._parse_response(response.choices[0].message.content)
            print(f"Parsed {len(locators)} locators from AI response")
            return locators
            
        except Exception as e:
            print(f"Error analyzing locators with AI: {e}")
            # Return fallback locators
            print("Falling back to non-AI locator analysis")
            return self._generate_fallback_locators(page_source, element_description)
    
    def _build_prompt(self, page_source: str, element_description: str, preferred_locator_type: str) -> str:
        """Build the prompt for locator analysis"""
        
        # Truncate page source if too long
        if len(page_source) > 3000:
            page_source = page_source[:3000] + "..."
        
        prompt = f"""
        You are an expert web automation engineer. Analyze the following HTML and suggest the best locators for the element described.
        
        Element Description: {element_description}
        Preferred Locator Type: {preferred_locator_type or 'Any'}
        
        HTML Source:
        {page_source}
        
        Instructions:
        1. First, identify which element(s) in the HTML match the description "{element_description}"
        2. Look for elements that contain the keywords from the description
        3. Consider element types, text content, attributes, and context
        4. Suggest multiple locator strategies in order of preference:
           - ID (most preferred - unique and stable)
           - CSS Selector (specific and readable)
           - XPath (when other options are not suitable)
           - Name attribute (for form elements)
           - Class name (if unique and meaningful)
           - Link text (for links)
           - Partial link text (for links with long text)
        
        For each suggestion, provide:
        - Locator type (id, css, xpath, name, class_name, link_text, partial_link_text)
        - Locator value (the actual locator string)
        - Confidence level (High/Medium/Low based on uniqueness and stability)
        - Reasoning (why this locator is recommended for this specific element)
        - Selenium code example (complete line of code)
        
        Format the response as a JSON object with the following structure:
        {{
            "locators": [
                {{
                    "type": "locator_type",
                    "value": "locator_value",
                    "confidence": "High/Medium/Low",
                    "reasoning": "Detailed explanation of why this locator is recommended for the described element",
                    "selenium_code": "driver.find_element(By.LOCATOR_TYPE, \"locator_value\")"
                }}
            ]
        }}
        
        Important considerations:
        - Uniqueness: The locator should identify exactly one element
        - Stability: The locator should be resistant to minor HTML changes
        - Readability: The locator should be easy to understand and maintain
        - Performance: Prefer faster locator types (ID > CSS > XPath)
        - Context: Consider the element's purpose and relationship to other elements
        
        If you cannot find a specific element matching the description, suggest the most relevant elements you can find and explain why they might be what the user is looking for.
        """
        
        return prompt
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the AI response into structured locators"""
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
            return data.get("locators", [])
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing response: {e}")
            return []
    
    def _generate_fallback_locators(self, page_source: str, element_description: str) -> List[Dict[str, Any]]:
        """Generate fallback locators when AI analysis fails"""
        
        print(f"Generating fallback locators for: '{element_description}'")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        all_locators = []
        
        # Split by comma and strip whitespace
        descriptions = [desc.strip() for desc in element_description.split(',') if desc.strip()]
        print(f"Split descriptions: {descriptions}")
        
        for desc in descriptions:
            locators = []
            try:
                desc_lower = desc.lower()
                print(f"Looking for elements matching keywords: {desc_lower}")
                # Look for buttons
                if any(keyword in desc_lower for keyword in ['button', 'buton', 'click', 'tıkla']):
                    print("Searching for buttons...")
                    buttons = soup.find_all(['button', 'input'], type=['button', 'submit'])
                    print(f"Found {len(buttons)} buttons")
                    for button in buttons[:3]:
                        button_text = button.get_text(strip=True) or button.get('value', '') or button.get('placeholder', '')
                        if button_text:
                            print(f"Button text: '{button_text}'")
                            if any(word in button_text.lower() for word in desc_lower.split()):
                                print(f"Found matching button: '{button_text}'")
                                locators.append({
                                    "type": "xpath",
                                    "value": f"//button[contains(text(), '{button_text}')]",
                                    "confidence": "High",
                                    "reasoning": f"Found button with text matching description: '{button_text}'",
                                    "selenium_code": f'driver.find_element(By.XPATH, "//button[contains(text(), \'{button_text}\')]")'
                                })
                                break
                    if not locators:
                        print("No specific matching buttons found, adding generic button locators")
                        for button in buttons[:2]:
                            button_text = button.get_text(strip=True) or button.get('value', '')
                            if button_text:
                                locators.append({
                                    "type": "xpath",
                                    "value": f"//button[contains(text(), '{button_text}')]",
                                    "confidence": "Medium",
                                    "reasoning": f"Found button: '{button_text}'",
                                    "selenium_code": f'driver.find_element(By.XPATH, "//button[contains(text(), \'{button_text}\')]")'
                                })
                elif any(keyword in desc_lower for keyword in ['input', 'text', 'email', 'password', 'username', 'kullanıcı', 'şifre']):
                    print("Searching for input fields...")
                    inputs = soup.find_all('input', type=['text', 'email', 'password', 'search'])
                    print(f"Found {len(inputs)} input fields")
                    for inp in inputs[:3]:
                        placeholder = inp.get('placeholder', '')
                        name = inp.get('name', '')
                        id_attr = inp.get('id', '')
                        print(f"Input - placeholder: '{placeholder}', name: '{name}', id: '{id_attr}'")
                        if placeholder:
                            locators.append({
                                "type": "css",
                                "value": f"input[placeholder='{placeholder}']",
                                "confidence": "High",
                                "reasoning": f"Found input with placeholder: '{placeholder}'",
                                "selenium_code": f'driver.find_element(By.CSS_SELECTOR, "input[placeholder=\'{placeholder}\']")'
                            })
                        elif name:
                            locators.append({
                                "type": "name",
                                "value": name,
                                "confidence": "Medium",
                                "reasoning": f"Found input with name: '{name}'",
                                "selenium_code": f'driver.find_element(By.NAME, "{name}")'
                            })
                        elif id_attr:
                            locators.append({
                                "type": "id",
                                "value": id_attr,
                                "confidence": "High",
                                "reasoning": f"Found input with ID: '{id_attr}'",
                                "selenium_code": f'driver.find_element(By.ID, "{id_attr}")'
                            })
                elif any(keyword in desc_lower for keyword in ['link', 'href', 'url', 'bağlantı']):
                    print("Searching for links...")
                    links = soup.find_all('a', href=True)
                    print(f"Found {len(links)} links")
                    for link in links[:3]:
                        link_text = link.get_text(strip=True)
                        if link_text:
                            print(f"Link text: '{link_text}'")
                            locators.append({
                                "type": "link_text",
                                "value": link_text,
                                "confidence": "High",
                                "reasoning": f"Found link with text: '{link_text}'",
                                "selenium_code": f'driver.find_element(By.LINK_TEXT, "{link_text}")'
                            })
                elif any(keyword in desc_lower for keyword in ['form', 'formu']):
                    print("Searching for forms...")
                    forms = soup.find_all('form')
                    print(f"Found {len(forms)} forms")
                    for form in forms[:2]:
                        form_id = form.get('id', '')
                        form_class = ' '.join(form.get('class', []))
                        if form_id:
                            locators.append({
                                "type": "id",
                                "value": form_id,
                                "confidence": "High",
                                "reasoning": f"Found form with ID: '{form_id}'",
                                "selenium_code": f'driver.find_element(By.ID, "{form_id}")'
                            })
                        elif form_class:
                            css_selector = f"form.{form_class.replace(' ', '.')}"
                            locators.append({
                                "type": "css",
                                "value": css_selector,
                                "confidence": "Medium",
                                "reasoning": f"Found form with class: '{form_class}'",
                                "selenium_code": f'driver.find_element(By.CSS_SELECTOR, "{css_selector}")'
                            })
                else:
                    print("Searching for elements with matching text...")
                    elements_with_text = soup.find_all(text=lambda text: text and any(word in text.lower() for word in desc_lower.split() if len(word) > 2))
                    print(f"Found {len(elements_with_text)} text elements")
                    for text_element in elements_with_text[:2]:
                        parent = text_element.parent
                        if parent:
                            parent_tag = parent.name
                            parent_text = text_element.strip()
                            print(f"Text element: '{parent_text}' in <{parent_tag}>")
                            if parent_tag in ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                locators.append({
                                    "type": "xpath",
                                    "value": f"//{parent_tag}[contains(text(), '{parent_text}')]",
                                    "confidence": "Medium",
                                    "reasoning": f"Found {parent_tag} with text: '{parent_text}'",
                                    "selenium_code": f'driver.find_element(By.XPATH, "//{parent_tag}[contains(text(), \'{parent_text}\')]")'
                                })
                            elif parent_tag == 'a':
                                locators.append({
                                    "type": "link_text",
                                    "value": parent_text,
                                    "confidence": "High",
                                    "reasoning": f"Found link with text: '{parent_text}'",
                                    "selenium_code": f'driver.find_element(By.LINK_TEXT, "{parent_text}")'
                                })
                            elif parent_tag == 'button':
                                locators.append({
                                    "type": "xpath",
                                    "value": f"//button[contains(text(), '{parent_text}')]",
                                    "confidence": "High",
                                    "reasoning": f"Found button with text: '{parent_text}'",
                                    "selenium_code": f'driver.find_element(By.XPATH, "//button[contains(text(), \'{parent_text}\')]")'
                                })
                    if not locators:
                        print("No specific elements found, providing generic suggestions...")
                        elements_with_id = soup.find_all(attrs={"id": True})
                        if elements_with_id:
                            locators.append({
                                "type": "id",
                                "value": elements_with_id[0]["id"],
                                "confidence": "Medium",
                                "reasoning": "Found element with ID attribute",
                                "selenium_code": f'driver.find_element(By.ID, "{elements_with_id[0]["id"]}")'
                            })
                        elements_with_class = soup.find_all(class_=True)
                        if elements_with_class:
                            class_name = elements_with_class[0]["class"][0]
                            locators.append({
                                "type": "class_name",
                                "value": class_name,
                                "confidence": "Low",
                                "reasoning": "Found element with class attribute",
                                "selenium_code": f'driver.find_element(By.CLASS_NAME, "{class_name}")'
                            })
                        buttons = soup.find_all("button")
                        if buttons:
                            locators.append({
                                "type": "tag_name",
                                "value": "button",
                                "confidence": "Low",
                                "reasoning": "Found button element",
                                "selenium_code": 'driver.find_element(By.TAG_NAME, "button")'
                            })
                        links = soup.find_all("a")
                        if links:
                            locators.append({
                                "type": "tag_name",
                                "value": "a",
                                "confidence": "Low",
                                "reasoning": "Found link element",
                                "selenium_code": 'driver.find_element(By.TAG_NAME, "a")'
                            })
            except Exception as e:
                print(f"Error generating fallback locators for '{desc}': {e}")
            print(f"Generated {len(locators)} fallback locators for '{desc}'")
            all_locators.extend(locators)
        print(f"Total fallback locators generated: {len(all_locators)}")
        return all_locators
    
    def analyze_page_structure(self, page_source: str) -> Dict[str, Any]:
        """Analyze the overall structure of a web page"""
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        analysis = {
            "title": soup.title.string if soup.title else "No title",
            "forms": len(soup.find_all("form")),
            "buttons": len(soup.find_all("button")),
            "links": len(soup.find_all("a")),
            "inputs": len(soup.find_all("input")),
            "elements_with_id": len(soup.find_all(attrs={"id": True})),
            "elements_with_class": len(soup.find_all(class_=True)),
            "suggested_improvements": []
        }
        
        # Suggest improvements
        if analysis["elements_with_id"] == 0:
            analysis["suggested_improvements"].append("Add unique IDs to important elements for better testability")
        
        if analysis["elements_with_class"] == 0:
            analysis["suggested_improvements"].append("Add CSS classes to elements for styling and testing")
        
        return analysis
    
    def validate_locator(self, page_source: str, locator_type: str, locator_value: str) -> Dict[str, Any]:
        """Validate if a locator works on the given page"""
        
        soup = BeautifulSoup(page_source, 'html.parser')
        validation_result = {
            "valid": False,
            "elements_found": 0,
            "message": "",
            "suggestions": []
        }
        
        try:
            if locator_type == "id":
                elements = soup.find_all(attrs={"id": locator_value})
                validation_result["elements_found"] = len(elements)
                validation_result["valid"] = len(elements) > 0
                
            elif locator_type == "class_name":
                elements = soup.find_all(class_=locator_value)
                validation_result["elements_found"] = len(elements)
                validation_result["valid"] = len(elements) > 0
                
            elif locator_type == "tag_name":
                elements = soup.find_all(locator_value)
                validation_result["elements_found"] = len(elements)
                validation_result["valid"] = len(elements) > 0
                
            elif locator_type == "css_selector":
                elements = soup.select(locator_value)
                validation_result["elements_found"] = len(elements)
                validation_result["valid"] = len(elements) > 0
            
            # Set appropriate messages
            if validation_result["elements_found"] == 0:
                validation_result["message"] = f"No elements found with {locator_type}: {locator_value}"
            elif validation_result["elements_found"] == 1:
                validation_result["message"] = f"Found exactly 1 element with {locator_type}: {locator_value}"
            else:
                validation_result["message"] = f"Found {validation_result['elements_found']} elements with {locator_type}: {locator_value}"
                validation_result["suggestions"].append("Consider using a more specific locator to target a single element")
                
        except Exception as e:
            validation_result["message"] = f"Error validating locator: {str(e)}"
        
        return validation_result 