"""
ClinVar Schema Mapping - The Table of Contents.

Maps user-friendly terms to ClinVar technical fields and defines the
structure of the metadata we care about.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ClinVarField(str, Enum):
    """ClinVar database field names."""

    VARIANT_ID = "VariationID"
    VARIANT_TYPE = "VariationType"
    NUCLEOTIDE_CHANGE = "Nucleotide"
    PROTEIN_CHANGE = "Protein"
    GENE_SYMBOL = "GeneSymbol"
    CLINICAL_SIGNIFICANCE = "ClinicalSignificance"
    REVIEW_STATUS = "ReviewStatus"
    LAST_EVALUATED = "LastEvaluated"
    CONDITION = "Condition"
    DISEASE_MECHANISM = "DiseaseMechanism"
    PHENOTYPE = "Phenotype"
    ASSERTION_METHOD = "AssertionMethod"
    ASSERTION_TYPE = "AssertionType"
    NUMBER_SUBMITTERS = "NumberSubmitters"
    CONFLICTED_INTERPRETATION = "ConflictedInterpretation"
    MOLECULAR_CONSEQUENCE = "MolecularConsequence"
    TRANSCRIPT_ID = "TranscriptID"


class ClinicalSignificanceMapping(str, Enum):
    """User-facing to ClinVar clinical significance values."""

    PATHOGENIC = "Pathogenic"
    LIKELY_PATHOGENIC = "Likely pathogenic"
    VUS = "Uncertain significance"
    LIKELY_BENIGN = "Likely benign"
    BENIGN = "Benign"


class ReviewStatusMapping(str, Enum):
    """Common ClinVar review statuses."""

    EXPERT = "reviewed by expert panel"
    MULTIPLE = "multiple submitters"
    SINGLE = "single submitter"
    NO_ASSERTION = "no assertion provided"


class ClinVarSchema:
    """
    Complete ClinVar data schema abstraction for search and filtering.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("clinvar_schema")
        self._define_fields()
        self._define_search_capabilities()

    def _define_fields(self) -> None:
        """Define all available fields used by the retrieval layer."""

        self.fields = {
            "variant_id": {
                "technical_name": ClinVarField.VARIANT_ID,
                "description": "Unique ClinVar variation ID",
                "type": "integer",
                "searchable": True,
                "example": "12345",
            },
            "variant_type": {
                "technical_name": ClinVarField.VARIANT_TYPE,
                "description": "Type of genetic variation",
                "type": "string",
                "searchable": True,
                "values": [
                    "single nucleotide variant",
                    "deletion",
                    "insertion",
                    "indel",
                    "structural variation",
                ],
                "example": "single nucleotide variant",
            },
            "nucleotide_change": {
                "technical_name": ClinVarField.NUCLEOTIDE_CHANGE,
                "description": "DNA change notation",
                "type": "string",
                "searchable": True,
                "example": "NC_000017.11:g.7571720C>T",
            },
            "protein_change": {
                "technical_name": ClinVarField.PROTEIN_CHANGE,
                "description": "Protein change notation (HGVS)",
                "type": "string",
                "searchable": True,
                "example": "NP_000537.3:p.Arg175His",
            },
            "gene_symbol": {
                "technical_name": ClinVarField.GENE_SYMBOL,
                "description": "Gene name",
                "type": "string",
                "searchable": True,
                "example": "TP53",
            },
            "clinical_significance": {
                "technical_name": ClinVarField.CLINICAL_SIGNIFICANCE,
                "description": "Clinical classification of variant",
                "type": "string",
                "searchable": True,
                "values": [entry.value for entry in ClinicalSignificanceMapping],
                "example": "Pathogenic",
            },
            "review_status": {
                "technical_name": ClinVarField.REVIEW_STATUS,
                "description": "Quality of classification review",
                "type": "string",
                "searchable": True,
                "values": [entry.value for entry in ReviewStatusMapping],
                "example": "reviewed by expert panel",
            },
            "last_evaluated": {
                "technical_name": ClinVarField.LAST_EVALUATED,
                "description": "Date of last clinical evaluation",
                "type": "date",
                "searchable": True,
                "example": "2024-01-15",
            },
            "condition": {
                "technical_name": ClinVarField.CONDITION,
                "description": "Associated disease or phenotype",
                "type": "string",
                "searchable": True,
                "example": "Li-Fraumeni syndrome",
            },
            "phenotype": {
                "technical_name": ClinVarField.PHENOTYPE,
                "description": "Observable characteristics",
                "type": "string",
                "searchable": True,
                "example": "Neoplasm",
            },
            "number_submitters": {
                "technical_name": ClinVarField.NUMBER_SUBMITTERS,
                "description": "Number of submitting organizations",
                "type": "integer",
                "searchable": False,
                "example": 5,
            },
            "assertion_method": {
                "technical_name": ClinVarField.ASSERTION_METHOD,
                "description": "Method used to classify variant",
                "type": "string",
                "searchable": True,
                "example": "clinical testing",
            },
            "molecular_consequence": {
                "technical_name": ClinVarField.MOLECULAR_CONSEQUENCE,
                "description": "Effect on gene or protein",
                "type": "string",
                "searchable": True,
                "values": [
                    "frameshift variant",
                    "missense variant",
                    "nonsense variant",
                    "synonymous variant",
                    "splice region variant",
                ],
                "example": "missense variant",
            },
        }

    def _define_search_capabilities(self) -> None:
        """Describe supported search styles."""

        self.search_capabilities = {
            "exact_match": {
                "description": "Exact field matching",
                "fields": ["variant_id", "gene_symbol", "variant_type"],
                "operator": "==",
            },
            "text_search": {
                "description": "Full-text search across fields",
                "fields": ["condition", "phenotype", "protein_change"],
                "operator": "CONTAINS",
            },
            "range_search": {
                "description": "Range queries",
                "fields": ["last_evaluated", "number_submitters"],
                "operator": "BETWEEN",
            },
            "categorical_search": {
                "description": "Search within predefined categories",
                "fields": [
                    "clinical_significance",
                    "review_status",
                    "molecular_consequence",
                ],
                "operator": "IN",
            },
        }

    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """Get information about a field."""

        return self.fields.get(field_name.lower(), {})

    def get_all_searchable_fields(self) -> List[str]:
        """Get all searchable field names."""

        return [
            name
            for name, info in self.fields.items()
            if info.get("searchable", False)
        ]

    def get_schema_description(self) -> str:
        """Generate a human-readable schema description."""

        description = "ClinVar Database Schema\n"
        description += "=" * 80 + "\n\n"

        for field_name, field_info in self.fields.items():
            description += f"{field_name}\n"
            description += f"  Description: {field_info.get('description', 'N/A')}\n"
            description += f"  Type: {field_info.get('type', 'N/A')}\n"
            description += f"  Searchable: {field_info.get('searchable', False)}\n"
            if "values" in field_info:
                description += f"  Possible values: {', '.join(field_info['values'])}\n"
            description += "\n"

        return description


class QueryTermMapper:
    """
    Maps user-friendly terms to technical ClinVar terms.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("query_term_mapper")
        self.schema = ClinVarSchema()
        self._build_term_mappings()

    def _build_term_mappings(self) -> None:
        """Build mapping of user terms to technical terms."""

        self.term_mappings: Dict[str, Tuple[str, Any]] = {
            "harmful": ("clinical_significance", "Pathogenic"),
            "pathogenic": ("clinical_significance", "Pathogenic"),
            "disease-causing": ("clinical_significance", "Pathogenic"),
            "likely harmful": ("clinical_significance", "Likely pathogenic"),
            "uncertain": ("clinical_significance", "Uncertain significance"),
            "safe": ("clinical_significance", "Benign"),
            "benign": ("clinical_significance", "Benign"),
            "not harmful": ("clinical_significance", "Benign"),
            "expert-reviewed": ("review_status", "reviewed by expert panel"),
            "well-studied": ("review_status", "multiple submitters"),
            "rare": ("number_submitters", 1),
            "common": ("number_submitters", ">5"),
            "frameshift": ("molecular_consequence", "frameshift variant"),
            "missense": ("molecular_consequence", "missense variant"),
            "nonsense": ("molecular_consequence", "nonsense variant"),
            "silent": ("molecular_consequence", "synonymous variant"),
            "splice": ("molecular_consequence", "splice region variant"),
            "snp": ("variant_type", "single nucleotide variant"),
            "deletion": ("variant_type", "deletion"),
            "insertion": ("variant_type", "insertion"),
            "indel": ("variant_type", "indel"),
        }

    def translate_query(self, user_term: str) -> Optional[Tuple[str, Any]]:
        """Translate a user-friendly term to a technical field/value pair."""

        user_term_lower = user_term.lower().strip()
        if user_term_lower in self.term_mappings:
            return self.term_mappings[user_term_lower]

        for mapped_term, mapping in self.term_mappings.items():
            if mapped_term in user_term_lower:
                self.logger.debug("Partial match: '%s' -> '%s'", user_term, mapped_term)
                return mapping

        return None


class ClinVarFilterBuilder:
    """
    Converts user criteria dictionaries into query filter dictionaries.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("filter_builder")
        self.mapper = QueryTermMapper()

    def build_filter(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Build a simple filter dict from user criteria."""

        filter_dict: Dict[str, Any] = {}
        for key, value in criteria.items():
            if key == "gene":
                filter_dict["GeneSymbol"] = value
            elif key == "pathogenicity":
                mapped = self.mapper.translate_query(str(value))
                if mapped:
                    field, tech_value = mapped
                    filter_dict[field] = tech_value
            elif key == "condition":
                filter_dict["Condition"] = value
            elif key == "variant_type":
                mapped = self.mapper.translate_query(str(value))
                if mapped:
                    field, tech_value = mapped
                    filter_dict[field] = tech_value

        self.logger.debug("Built filter: %s", filter_dict)
        return filter_dict


clinvar_schema = ClinVarSchema()
query_mapper = QueryTermMapper()
filter_builder = ClinVarFilterBuilder()

logger.info("ClinVar schema initialized")

__all__ = [
    "ClinVarField",
    "ClinicalSignificanceMapping",
    "ReviewStatusMapping",
    "ClinVarSchema",
    "QueryTermMapper",
    "ClinVarFilterBuilder",
    "clinvar_schema",
    "query_mapper",
    "filter_builder",
]
