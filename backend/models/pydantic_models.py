"""
Pydantic models for the Gene Mutation Detection System

This file contains all data models for:
- Request validation
- Response formatting
- Internal data contracts between agents
- Type safety throughout the application
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


# ============================================================================
# ENUMS - Define allowed values
# ============================================================================

class GeneEnum(str, Enum):
    """Supported genes"""
    TP53 = "TP53"
    BRCA1 = "BRCA1"
    BRCA2 = "BRCA2"
    EGFR = "EGFR"
    APP = "APP"
    PSEN1 = "PSEN1"
    TCF7L2 = "TCF7L2"
    PPARG = "PPARG"
    FTO = "FTO"


class MutationTypeEnum(str, Enum):
    """Types of mutations"""
    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"


class MutationEffectEnum(str, Enum):
    """Effect of mutation"""
    FRAMESHIFT = "frameshift"
    MISSENSE = "missense"
    NONSENSE = "nonsense"
    SYNONYMOUS = "synonymous"
    INFRAME_INSERTION = "inframe_insertion"
    INFRAME_DELETION = "inframe_deletion"
    UNKNOWN = "unknown"


class ClassificationEnum(str, Enum):
    """Clinical classification"""
    PATHOGENIC = "Pathogenic"
    POTENTIALLY_PATHOGENIC = "Potentially Pathogenic"
    UNCERTAIN = "Uncertain"
    BENIGN = "Benign"


class RiskLevelEnum(str, Enum):
    """Risk level"""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class ConfidenceEnum(str, Enum):
    """Confidence level"""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class DiseaseCategoryEnum(str, Enum):
    """Disease categories"""
    CANCER = "Cancer"
    METABOLIC = "Metabolic"
    NEUROLOGICAL = "Neurological"


# ============================================================================
# REQUEST MODELS (From user/frontend)
# ============================================================================

class AnalysisRequest(BaseModel):
    """
    Request model for single mutation analysis

    Example:
        {
            "sequence": "ATGCGATAA...",
            "gene": "TP53",
            "disease_category": "Cancer"
        }
    """

    sequence: str = Field(
        ...,
        description="DNA sequence to analyze (only A, T, C, G allowed)",
        min_length=10,
        max_length=50000,
        examples=["ATGCGATAA"]
    )

    gene: GeneEnum = Field(
        ...,
        description="Gene name",
        examples=[GeneEnum.TP53]
    )

    disease_category: Optional[DiseaseCategoryEnum] = Field(
        None,
        description="Disease category for context"
    )

    @field_validator('sequence')
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        """Validate sequence contains only ATCG"""
        valid_chars = set('ATCG')
        if not all(c.upper() in valid_chars for c in v):
            raise ValueError('Sequence must contain only A, T, C, G')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "sequence": "ATGCGATAA",
                "gene": "TP53",
                "disease_category": "Cancer"
            }
        }


class BulkAnalysisRequest(BaseModel):
    """Request for batch analysis"""

    requests: List[AnalysisRequest] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of analysis requests"
    )


class SequenceUploadRequest(BaseModel):
    """Request for file upload"""
    gene: GeneEnum
    filename: str


# ============================================================================
# INTERNAL DATA MODELS (Between agents)
# ============================================================================

class ValidationOutput(BaseModel):
    """Output from Validation Agent"""

    is_valid: bool = Field(
        ...,
        description="Whether sequence is valid"
    )

    cleaned_sequence: str = Field(
        ...,
        description="Cleaned (uppercase, no whitespace) sequence"
    )

    length: int = Field(
        ...,
        description="Length of cleaned sequence",
        ge=0
    )

    errors: List[str] = Field(
        default_factory=list,
        description="Critical errors preventing processing"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical warnings"
    )


class AlignmentOutput(BaseModel):
    """Output from Alignment Agent"""

    success: bool = Field(
        ...,
        description="Whether alignment succeeded"
    )

    aligned_reference: Optional[str] = Field(
        None,
        description="Reference sequence with gaps"
    )

    aligned_query: Optional[str] = Field(
        None,
        description="Query sequence with gaps"
    )

    score: Optional[float] = Field(
        None,
        description="Alignment score"
    )

    matches: Optional[int] = Field(
        None,
        description="Number of matching positions",
        ge=0
    )

    mismatches: Optional[int] = Field(
        None,
        description="Number of mismatching positions",
        ge=0
    )

    gaps: Optional[int] = Field(
        None,
        description="Total number of gaps",
        ge=0
    )

    identity_percent: Optional[float] = Field(
        None,
        description="Sequence identity percentage",
        ge=0,
        le=100
    )

    reference_length: Optional[int] = Field(
        None,
        description="Original reference length",
        ge=0
    )

    query_length: Optional[int] = Field(
        None,
        description="Original query length",
        ge=0
    )

    alignment_visual: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Visual representation of alignment"
    )

    error: Optional[str] = Field(
        None,
        description="Error message if alignment failed"
    )


class Mutation(BaseModel):
    """A single detected mutation"""

    type: MutationTypeEnum = Field(
        ...,
        description="Type of mutation"
    )

    position: int = Field(
        ...,
        description="Position in sequence (1-indexed)",
        ge=1
    )

    reference_base: Optional[str] = Field(
        None,
        description="Original base(s)"
    )

    alternate_base: Optional[str] = Field(
        None,
        description="Mutated base(s)"
    )

    length: Optional[int] = Field(
        None,
        description="Length of indel",
        ge=1
    )

    context: Optional[str] = Field(
        None,
        description="Surrounding sequence context"
    )


class MutationDetectionOutput(BaseModel):
    """Output from Mutation Detection Agent"""

    total_mutations: int = Field(
        ...,
        description="Total number of mutations detected",
        ge=0
    )

    mutations: List[Mutation] = Field(
        default_factory=list,
        description="List of detected mutations"
    )

    mutation_counts: Dict[str, int] = Field(
        ...,
        description="Count by mutation type"
    )

    has_mutations: bool = Field(
        ...,
        description="Whether any mutations were found"
    )


class Annotation(BaseModel):
    """Annotation of a mutation with protein-level effects"""

    # Base mutation info
    type: MutationTypeEnum
    position: int
    reference_base: Optional[str] = None
    alternate_base: Optional[str] = None

    # Protein-level annotation
    protein_position: Optional[int] = Field(
        None,
        description="Position in protein (amino acid)"
    )

    reference_codon: Optional[str] = Field(
        None,
        description="Reference codon"
    )

    mutant_codon: Optional[str] = Field(
        None,
        description="Mutant codon"
    )

    reference_aa: Optional[str] = Field(
        None,
        description="Reference amino acid (1-letter code)"
    )

    mutant_aa: Optional[str] = Field(
        None,
        description="Mutant amino acid (1-letter code)"
    )

    protein_change: Optional[str] = Field(
        None,
        description="HGVS-style protein change (e.g., R175H)"
    )

    effect: MutationEffectEnum = Field(
        ...,
        description="Effect on protein"
    )

    impact: str = Field(
        ...,
        description="Human-readable impact description"
    )


class AnnotationOutput(BaseModel):
    """Output from Annotation Agent"""

    annotated_mutations: List[Annotation] = Field(
        ...,
        description="Mutations with protein-level annotations"
    )

    impact_summary: Dict[str, int] = Field(
        ...,
        description="Summary of impacts (high/moderate/low)"
    )


class ClassificationOutput(BaseModel):
    """Output from Classification Agent"""

    overall_classification: ClassificationEnum = Field(
        ...,
        description="Overall clinical classification"
    )

    risk_level: RiskLevelEnum = Field(
        ...,
        description="Overall risk level"
    )

    confidence: ConfidenceEnum = Field(
        ...,
        description="Confidence in classification"
    )

    rationale: str = Field(
        ...,
        description="Explanation for classification"
    )

    classified_mutations: List[Dict[str, Any]] = Field(
        ...,
        description="Each mutation with its classification"
    )

    summary: Dict[str, int] = Field(
        ...,
        description="Count of mutations by classification"
    )

    recommendation: str = Field(
        ...,
        description="Clinical recommendation"
    )


class ClinVarRecord(BaseModel):
    """Clinical evidence from ClinVar"""

    mutation_id: str = Field(
        ...,
        description="ClinVar mutation ID"
    )

    position: int = Field(
        ...,
        description="Position in sequence",
        ge=1
    )

    mutation_type: str = Field(
        ...,
        description="Type of mutation"
    )

    clinical_significance: str = Field(
        ...,
        description="Clinical significance"
    )

    review_status: Optional[str] = Field(
        None,
        description="ClinVar review status"
    )

    condition: str = Field(
        ...,
        description="Associated condition"
    )

    evidence_summary: str = Field(
        ...,
        description="Summary of evidence"
    )

    protein_change: Optional[str] = Field(
        None,
        description="Protein-level change"
    )

    match_quality: float = Field(
        ...,
        description="Relevance score (0-1)",
        ge=0,
        le=1
    )


class RetrievalOutput(BaseModel):
    """Output from Retrieval Agent"""

    success: bool = Field(
        ...,
        description="Whether retrieval succeeded"
    )

    total_evidence: int = Field(
        ...,
        description="Number of evidence records found",
        ge=0
    )

    evidence: List[ClinVarRecord] = Field(
        default_factory=list,
        description="Clinical evidence records"
    )

    database: str = Field(
        ...,
        description="Source database"
    )

    gene: str = Field(
        ...,
        description="Gene analyzed"
    )

    error: Optional[str] = Field(
        None,
        description="Error message if retrieval failed"
    )


# ============================================================================
# RESPONSE MODELS (To user/frontend)
# ============================================================================

class AnalysisResponse(BaseModel):
    """
    Complete analysis response

    Contains results from all agents in the pipeline
    """

    # Metadata
    analysis_id: str = Field(
        ...,
        description="Unique analysis identifier",
        examples=[str(uuid.uuid4())]
    )

    timestamp: str = Field(
        ...,
        description="Analysis timestamp (ISO 8601)",
        examples=["2024-01-15T10:30:00Z"]
    )

    gene: str = Field(
        ...,
        description="Gene analyzed"
    )

    # Results from each agent
    validation: ValidationOutput = Field(
        ...,
        description="Validation results"
    )

    alignment: Optional[AlignmentOutput] = Field(
        None,
        description="Sequence alignment results"
    )

    mutations: Optional[List[Mutation]] = Field(
        None,
        description="Detected mutations"
    )

    annotations: Optional[AnnotationOutput] = Field(
        None,
        description="Protein-level annotations"
    )

    classification: Optional[ClassificationOutput] = Field(
        None,
        description="Risk classification"
    )

    evidence: Optional[RetrievalOutput] = Field(
        None,
        description="Clinical evidence"
    )

    # Status
    status: str = Field(
        ...,
        description="Analysis status (completed, partial_error, failed)",
        examples=["completed", "partial_error", "failed"]
    )

    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "gene": "TP53",
                "status": "completed",
                "errors": [],
                "warnings": []
            }
        }


class BulkAnalysisResponse(BaseModel):
    """Response for batch analysis"""

    responses: List[AnalysisResponse] = Field(
        ...,
        description="Analysis results for each request"
    )

    total_submitted: int = Field(...)
    total_completed: int = Field(...)
    total_failed: int = Field(...)


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str = Field(
        ...,
        description="Error message"
    )

    detail: Optional[str] = Field(
        None,
        description="Detailed error information"
    )

    status_code: int = Field(
        ...,
        description="HTTP status code",
        ge=400,
        le=599
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp"
    )


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(
        ...,
        description="Service status",
        examples=["healthy", "degraded"]
    )

    timestamp: str = Field(
        ...,
        description="Check timestamp"
    )

    version: str = Field(
        ...,
        description="API version"
    )

    services: Dict[str, str] = Field(
        ...,
        description="Status of each component"
    )


class ReferenceGenesResponse(BaseModel):
    """Response listing available genes"""

    available_genes: List[str] = Field(
        ...,
        description="List of supported genes"
    )

    categorized_genes: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Supported genes grouped by disease category"
    )

    total_genes: int = Field(
        ...,
        description="Total number of genes"
    )


# ============================================================================
# METADATA MODELS
# ============================================================================

class GeneMetadata(BaseModel):
    """Metadata about a gene"""

    name: str = Field(...)
    full_name: str = Field(...)
    category: DiseaseCategoryEnum = Field(...)
    chromosome: str = Field(...)
    description: Optional[str] = Field(None)


class SystemStatus(BaseModel):
    """System status information"""

    is_healthy: bool
    timestamp: datetime
    components: Dict[str, bool] = Field(
        default_factory=dict,
        description="Status of each component (validation, alignment, etc.)"
    )


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class AnalysisConfig(BaseModel):
    """Configuration for analysis"""

    use_ml_classifier: bool = True
    use_llamaindex_retrieval: bool = True
    enable_caching: bool = True
    timeout_seconds: int = 300


# ============================================================================
# TYPE ALIASES (For clarity in code)
# ============================================================================

# Example of using these in type hints:
# def process_mutation(mutation: Mutation) -> Annotation:
#     ...

__all__ = [
    # Enums
    'GeneEnum',
    'MutationTypeEnum',
    'MutationEffectEnum',
    'ClassificationEnum',
    'RiskLevelEnum',
    'ConfidenceEnum',
    'DiseaseCategoryEnum',
    # Requests
    'AnalysisRequest',
    'BulkAnalysisRequest',
    'SequenceUploadRequest',
    # Internal
    'ValidationOutput',
    'AlignmentOutput',
    'Mutation',
    'MutationDetectionOutput',
    'Annotation',
    'AnnotationOutput',
    'ClassificationOutput',
    'ClinVarRecord',
    'RetrievalOutput',
    # Responses
    'AnalysisResponse',
    'BulkAnalysisResponse',
    'ErrorResponse',
    'HealthResponse',
    'ReferenceGenesResponse',
    # Metadata
    'GeneMetadata',
    'SystemStatus',
    'AnalysisConfig',
]