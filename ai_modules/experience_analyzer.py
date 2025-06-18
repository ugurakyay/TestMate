"""TestMate Studio - Experience Analyzer"""

import json
import re
from typing import Dict, List, Any
from datetime import datetime

class ExperienceAnalyzer:
    def __init__(self):
        self.similarity_threshold = 0.6
    
    def analyze_test_scenario(self, test_scenario: str, framework: str) -> Dict[str, Any]:
        keywords = self._extract_keywords(test_scenario)
        return {"success": True, "keywords": keywords, "similar_patterns": []}
    
    def _extract_keywords(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        words = text.split()
        stop_words = {"the", "a", "an", "and", "or", "but"}
        keywords = [word for word in words if len(word) >= 3 and word not in stop_words]
        return list(set(keywords))

# Global instance
experience_analyzer = ExperienceAnalyzer()