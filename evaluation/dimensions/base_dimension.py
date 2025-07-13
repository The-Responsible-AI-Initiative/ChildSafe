from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any

class BaseDimensionScorer(ABC):
    """
    Base class for all ChildSafe scoring dimensions
    
    Provides common functionality and interface for all scoring dimensions
    """
    
    def __init__(self):
        self.age_groups = {
            "A3-5": {"min_age": 3, "max_age": 5, "vocabulary_level": "simple"},
            "A6-8": {"min_age": 6, "max_age": 8, "vocabulary_level": "elementary"},
            "A9-11": {"min_age": 9, "max_age": 11, "vocabulary_level": "intermediate"},
            "A12-14": {"min_age": 12, "max_age": 14, "vocabulary_level": "advanced"},
            "A15-17": {"min_age": 15, "max_age": 17, "vocabulary_level": "sophisticated"}
        }
        self._load_keywords()
    
    @abstractmethod
    def _load_keywords(self):
        """Load keywords specific to this dimension"""
        pass
    
    @abstractmethod
    def score(self, turns: List[Dict], agent_age: str) -> Tuple[float, Dict]:
        """
        Score the dimension for given conversation turns
        
        Args:
            turns: List of conversation turns
            agent_age: Age group of the agent (A3-5, A6-8, etc.)
            
        Returns:
            Tuple of (score, analysis_details)
        """
        pass
    
    def _get_model_responses(self, turns: List[Dict]) -> List[str]:
        """Extract model responses from turns"""
        return [turn.get("model", "") for turn in turns if turn.get("model")]
    
    def _get_child_requests(self, turns: List[Dict]) -> List[str]:
        """Extract child requests from turns"""
        return [turn.get("child", "") for turn in turns if turn.get("child")]
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count matches for keywords in text"""
        text_lower = text.lower()
        return sum(1 for keyword in keywords if keyword in text_lower)