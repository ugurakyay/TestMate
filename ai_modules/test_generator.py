import openai
import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
from .template_generator import TemplateTestGenerator
from datetime import datetime

load_dotenv()

class TestCaseGenerator:
    """Hibrit test case generator - Template-based + AI"""
    
    def __init__(self):
        # Template-based generator
        self.template_generator = TemplateTestGenerator()
        
        # AI configuration
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.ai_enabled = True
        else:
            self.client = None
            self.ai_enabled = False
            print("Info: OPENAI_API_KEY not found. Using template-based generation only.")
        
        self.model = "gpt-4"
        self.use_ai_threshold = 0.7  # AI kullanım eşiği
    
    async def generate_test_cases(
        self, 
        feature_description: str, 
        test_type: str, 
        framework: str = None,
        additional_context: str = None,
        use_ai: bool = False  # Kullanıcı AI tercihi
    ) -> List[Dict[str, Any]]:
        """
        Generate test cases using hybrid approach
        
        Args:
            feature_description: Description of the feature to test
            test_type: Type of test (web, mobile, api)
            framework: Testing framework to use
            additional_context: Additional context for test generation
            use_ai: Force AI usage (for premium users)
            
        Returns:
            List of generated test cases
        """
        
        # 1. Template-based generation (her zaman)
        template_cases = await self.template_generator.generate_test_cases(
            feature_description, test_type, framework, additional_context
        )
        
        # 2. AI enhancement (opsiyonel)
        if use_ai and self.ai_enabled:
            try:
                ai_cases = await self._generate_ai_enhancement(
                    feature_description, test_type, framework, additional_context
                )
                # AI sonuçlarını template sonuçlarıyla birleştir
                return self._merge_test_cases(template_cases, ai_cases)
            except Exception as e:
                print(f"AI enhancement failed: {e}. Using template results only.")
                return template_cases
        
        # 3. Karmaşıklık analizi ile AI önerisi
        complexity_score = self._analyze_complexity(feature_description, additional_context)
        if complexity_score > self.use_ai_threshold and self.ai_enabled:
            print(f"High complexity detected ({complexity_score:.2f}). Consider using AI for better results.")
        
        return template_cases
    
    def _analyze_complexity(self, description: str, context: str = None) -> float:
        """Feature karmaşıklığını analiz et"""
        complexity_score = 0.0
        
        # Uzunluk faktörü
        length_factor = min(len(description) / 100, 1.0)
        complexity_score += length_factor * 0.3
        
        # Anahtar kelime analizi
        complex_keywords = [
            "api", "authentication", "authorization", "database", "cache",
            "websocket", "real-time", "async", "concurrent", "distributed",
            "microservice", "integration", "workflow", "pipeline", "queue"
        ]
        
        description_lower = description.lower()
        context_lower = (context or "").lower()
        
        for keyword in complex_keywords:
            if keyword in description_lower or keyword in context_lower:
                complexity_score += 0.1
        
        # Context uzunluğu
        if context:
            context_factor = min(len(context) / 200, 1.0)
            complexity_score += context_factor * 0.2
        
        return min(complexity_score, 1.0)
    
    async def _generate_ai_enhancement(
        self, 
        feature_description: str, 
        test_type: str, 
        framework: str, 
        additional_context: str
    ) -> List[Dict[str, Any]]:
        """AI ile test case'leri geliştir"""
        
        # Build the prompt for AI enhancement
        prompt = self._build_enhancement_prompt(feature_description, test_type, framework, additional_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert test automation engineer. Enhance existing test cases with advanced scenarios and edge cases."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            enhanced_cases = await self._parse_ai_response(response.choices[0].message.content)
            return enhanced_cases
            
        except Exception as e:
            print(f"Error in AI enhancement: {e}")
            return []
    
    def _build_enhancement_prompt(self, feature_description: str, test_type: str, framework: str, additional_context: str) -> str:
        """AI enhancement için prompt oluştur"""
        
        return f"""
        Enhance the following test scenario with advanced test cases:
        
        Feature: {feature_description}
        Test Type: {test_type}
        Framework: {framework}
        Context: {additional_context or 'None'}
        
        Please generate additional test cases that include:
        1. Performance test scenarios
        2. Security test cases
        3. Accessibility testing
        4. Cross-browser compatibility (for web)
        5. Data-driven test scenarios
        6. Negative test cases
        7. Boundary value analysis
        8. Error handling scenarios
        
        Focus on:
        - Real-world scenarios
        - Industry best practices
        - Comprehensive coverage
        - Maintainable test code
        
        Format as JSON array:
        {{
            "enhanced_cases": [
                {{
                    "name": "Test case name",
                    "description": "Detailed description",
                    "category": "performance|security|accessibility|compatibility|data-driven|negative|boundary|error",
                    "steps": ["Step 1", "Step 2", ...],
                    "expected_result": "Expected outcome",
                    "priority": "High|Medium|Low",
                    "code": "Python test code"
                }}
            ]
        }}
        """
    
    async def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """AI yanıtını parse et"""
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
            return data.get("enhanced_cases", [])
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing AI response: {e}")
            return []
    
    def _merge_test_cases(self, template_cases: List[Dict], ai_cases: List[Dict]) -> List[Dict]:
        """Template ve AI test case'lerini birleştir"""
        merged_cases = template_cases.copy()
        
        # AI case'lerini ekle
        for ai_case in ai_cases:
            # Duplicate kontrolü
            if not self._is_duplicate(ai_case, template_cases):
                merged_cases.append(ai_case)
        
        return merged_cases
    
    def _is_duplicate(self, ai_case: Dict, template_cases: List[Dict]) -> bool:
        """Duplicate test case kontrolü"""
        ai_name = ai_case.get("name", "").lower()
        
        for template_case in template_cases:
            template_name = template_case.get("name", "").lower()
            if ai_name == template_name:
                return True
        
        return False
    
    async def generate_test_suite(self, features: List[str], test_type: str, use_ai: bool = False) -> Dict[str, Any]:
        """Complete test suite oluştur"""
        
        test_suite = {
            "name": f"{test_type.title()} Test Suite",
            "description": f"Comprehensive test suite for {test_type} testing",
            "test_cases": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_cases": 0,
                "ai_enhanced": use_ai,
                "complexity_score": 0.0
            }
        }
        
        total_complexity = 0.0
        
        for feature in features:
            test_cases = await self.generate_test_cases(feature, test_type, use_ai=use_ai)
            test_suite["test_cases"].extend(test_cases)
            
            # Complexity hesapla
            complexity = self._analyze_complexity(feature)
            total_complexity += complexity
        
        # Metadata güncelle
        test_suite["metadata"]["total_cases"] = len(test_suite["test_cases"])
        test_suite["metadata"]["complexity_score"] = total_complexity / len(features) if features else 0.0
        
        return test_suite
    
    # Legacy methods for backward compatibility
    async def _generate_fallback_test(self, feature_description: str, test_type: str, framework: str) -> List[Dict[str, Any]]:
        """Fallback test generation (template-based)"""
        return await self.template_generator.generate_test_cases(
            feature_description, test_type, framework
        )
    
    def _build_prompt(self, feature_description: str, test_type: str, framework: str, additional_context: str) -> str:
        """Legacy prompt builder"""
        return self._build_enhancement_prompt(feature_description, test_type, framework, additional_context)
    
    async def _parse_response(self, response: str, test_type: str, feature_description: str = "", framework: str = "") -> List[Dict[str, Any]]:
        """Legacy response parser"""
        return await self._parse_ai_response(response) 