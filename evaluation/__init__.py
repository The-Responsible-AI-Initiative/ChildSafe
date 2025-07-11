# evaluation/__init__.py
# ChildSafe Evaluation Package

from .scoring_system import ChildSafeScorer, ScoringResult
from .score_corpus import CorpusScorer

__version__ = "1.0.0"
__author__ = "ChildSafe Research Team"

__all__ = [
    "ChildSafeScorer",
    "ScoringResult", 
    "CorpusScorer"
]