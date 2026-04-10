"""
Type hints and custom types for the application

This file centralizes type definitions for:
- Better IDE autocomplete
- Clearer function signatures
- Runtime validation opportunities
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from backend.models.pydantic_models import (
    ValidationOutput,
    AlignmentOutput,
    Mutation,
    Annotation,
    ClassificationOutput,
    ClinVarRecord,
)

# ============================================================================
# STATE TYPES
# ============================================================================

# Type for workflow state
AnalysisState = Dict[str, Any]

# Type for agent results
AgentResult = Union[
    ValidationOutput,
    AlignmentOutput,
    List[Mutation],
    List[Annotation],
    ClassificationOutput,
    List[ClinVarRecord]
]

# ============================================================================
# SEQUENCE TYPES
# ============================================================================

# DNA sequence (string of ATCG)
DNASequence = str

# Protein sequence (string of amino acids)
ProteinSequence = str

# Codon (3-nucleotide triplet)
Codon = str

# ============================================================================
# POSITION TYPES
# ============================================================================

# 0-indexed position
Position0Indexed = int

# 1-indexed position (more common in biology)
Position1Indexed = int

# ============================================================================
# FUNCTION SIGNATURES (Examples)
# ============================================================================

def validate_sequence(sequence: DNASequence) -> ValidationOutput:
    """Example: Type hints make this clear"""
    pass

def align_sequences(
    reference: DNASequence,
    query: DNASequence
) -> AlignmentOutput:
    """Example: Clear what type of alignment is returned"""
    pass

def detect_mutations(
    aligned_ref: DNASequence,
    aligned_query: DNASequence
) -> List[Mutation]:
    """Example: Returns list of Mutation objects"""
    pass

def annotate_mutations(
    mutations: List[Mutation],
    reference: DNASequence
) -> List[Annotation]:
    """Example: Transforms Mutations to Annotations"""
    pass

def classify_mutations(
    annotations: List[Annotation]
) -> ClassificationOutput:
    """Example: Clear return type"""
    pass

def retrieve_evidence(
    mutations: List[Mutation],
    gene: str
) -> List[ClinVarRecord]:
    """Example: Retrieves clinical records"""
    pass

__all__ = [
    'AnalysisState',
    'AgentResult',
    'DNASequence',
    'ProteinSequence',
    'Codon',
    'Position0Indexed',
    'Position1Indexed',
]