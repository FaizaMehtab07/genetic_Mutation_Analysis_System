"""
Agents module - Multi-agent pipeline

All agents implement the Agent interface:
- Input: State (dict-like)
- Process: Perform task
- Output: Modified state
"""

from backend.agents.alignment_agent import AlignmentAgent
from backend.agents.annotation_agent import AnnotationAgent
from backend.agents.aggregation_agent import AggregationAgent
from backend.agents.classification_agent import ClassificationAgent
from backend.agents.mutation_detection_agent import MutationDetectionAgent
from backend.agents.retrieval_agent import RetrievalAgent
from backend.agents.validation_agent import ValidationAgent

__all__ = [
    "ValidationAgent",
    "AlignmentAgent",
    "MutationDetectionAgent",
    "AnnotationAgent",
    "ClassificationAgent",
    "AggregationAgent",
    "RetrievalAgent",
]
