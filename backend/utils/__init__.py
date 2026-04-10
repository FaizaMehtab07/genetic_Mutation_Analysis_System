"""
Utils module - Helper functions and utilities
"""

from backend.utils.logger import setup_logging, logger
from backend.utils.validators import (
    validate_gene,
    validate_sequence,
    validate_sequence_length,
)
from backend.utils.type_hints import (
    AnalysisState,
    AgentResult,
    DNASequence,
    ProteinSequence,
)
from backend.utils.error_handling import (
    AnalysisException,
    ValidationException,
    AlignmentException,
    MutationDetectionException,
    AnnotationException,
    ClassificationException,
    RetrievalException,
    retry_on_exception,
    ErrorTracker,
    GracefulDegradation,
)

__all__ = [
    'setup_logging',
    'logger',
    'validate_gene',
    'validate_sequence',
    'validate_sequence_length',
    'AnalysisState',
    'AgentResult',
    'DNASequence',
    'ProteinSequence',
    'AnalysisException',
    'ValidationException',
    'AlignmentException',
    'MutationDetectionException',
    'AnnotationException',
    'ClassificationException',
    'RetrievalException',
    'retry_on_exception',
    'ErrorTracker',
    'GracefulDegradation',
]
