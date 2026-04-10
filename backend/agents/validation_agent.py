"""
Validation Agent - Checks DNA sequence validity

This agent validates the input sequence before processing:
- Checks for valid nucleotides (A, T, C, G only)
- Checks sequence length
- Cleans input (uppercase, removes whitespace)
- Validates gene name
"""

import logging
from typing import Any, Dict, List

from backend.core.constants import NUCLEOTIDES, SUPPORTED_GENES
from backend.models.pydantic_models import GeneEnum, ValidationOutput

logger = logging.getLogger(__name__)


class ValidationAgent:
    """
    Agent for validating DNA sequences and gene names.

    Input State:
        - sequence: str (raw, may have whitespace)
        - gene: str or GeneEnum

    Output State (adds):
        - validation_result: ValidationOutput
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("agents.validation")
        self.min_length = 10
        self.max_length = 50000

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate sequence and gene with comprehensive error handling.
        """

        self.logger.info("Validation Agent: Starting validation")

        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            sequence = state.get("sequence", "")
            gene = state.get("gene", "")

            errors: List[str] = []
            warnings: List[str] = []

            if not sequence or not isinstance(sequence, str):
                errors.append("Sequence must be a non-empty string")

            if not gene:
                errors.append("Gene must be a non-empty string")

            gene_input = gene.value if isinstance(gene, GeneEnum) else gene
            if gene_input and not isinstance(gene_input, str):
                errors.append("Gene must be a non-empty string")

            if errors:
                validation_result = ValidationOutput(
                    is_valid=False,
                    cleaned_sequence="",
                    length=0,
                    errors=errors,
                    warnings=warnings,
                )
                state["validation_result"] = validation_result
                state["errors"].extend(errors)
                self.logger.warning("Validation failed: invalid inputs")
                return state

            cleaned = ""
            self.logger.debug("Raw sequence length: %s", len(sequence))

            try:
                cleaned = (
                    sequence.strip()
                    .replace(" ", "")
                    .replace("\n", "")
                    .replace("\t", "")
                    .upper()
                )
                if not cleaned:
                    errors.append("Sequence is empty after cleaning")
            except Exception as exc:
                errors.append(f"Error cleaning sequence: {str(exc)}")
                self.logger.error("Sequence cleaning failed: %s", str(exc))

            try:
                invalid_chars = set(cleaned) - NUCLEOTIDES
                if invalid_chars:
                    errors.append(
                        f"Invalid nucleotides found: {', '.join(sorted(invalid_chars))}. "
                        "Only A, T, C, G allowed."
                    )
            except Exception as exc:
                errors.append(f"Error validating nucleotides: {str(exc)}")

            try:
                if len(cleaned) < self.min_length:
                    errors.append(
                        f"Sequence too short: {len(cleaned)} bp. "
                        f"Minimum: {self.min_length} bp"
                    )
                if len(cleaned) > self.max_length:
                    errors.append(
                        f"Sequence too long: {len(cleaned)} bp. "
                        f"Maximum: {self.max_length} bp"
                    )
            except Exception as exc:
                errors.append(f"Error validating length: {str(exc)}")

            try:
                if cleaned and len(cleaned) % 3 != 0:
                    warnings.append(
                        f"Sequence length ({len(cleaned)}) not divisible by 3. "
                        "Protein translation may be incomplete."
                    )
            except Exception as exc:
                warnings.append(f"Could not check sequence divisibility: {str(exc)}")

            if isinstance(gene, GeneEnum):
                gene_str = gene.value.upper()
            else:
                gene_str = str(gene).upper() if gene else ""

            try:
                if not gene_str:
                    errors.append("Gene name is required")
                elif gene_str not in SUPPORTED_GENES:
                    errors.append(
                        f"Gene '{gene}' not supported. "
                        f"Supported genes: {', '.join(sorted(SUPPORTED_GENES))}"
                    )
            except Exception as exc:
                errors.append(f"Error validating gene: {str(exc)}")

            is_valid = len(errors) == 0
            validation_result = ValidationOutput(
                is_valid=is_valid,
                cleaned_sequence=cleaned if is_valid else "",
                length=len(cleaned) if cleaned else 0,
                errors=errors,
                warnings=warnings,
            )

            state["validation_result"] = validation_result
            state["warnings"].extend(warnings)

            if not is_valid:
                state["errors"].extend(errors)
            else:
                state["cleaned_sequence"] = cleaned
                state["gene"] = gene_str

            self.logger.info(
                "Validation complete: is_valid=%s, length=%s, errors=%s, warnings=%s",
                is_valid,
                len(cleaned) if cleaned else 0,
                len(errors),
                len(warnings),
            )

            return state

        except Exception as exc:
            self.logger.error("Validation exception: %s", str(exc), exc_info=True)
            state["errors"].append(f"Validation exception: {str(exc)}")
            state["validation_result"] = ValidationOutput(
                is_valid=False,
                cleaned_sequence="",
                length=0,
                errors=[f"Validation exception: {str(exc)}"],
                warnings=[],
            )
            return state


def validation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node wrapper for validation.
    """

    agent = ValidationAgent()
    return agent.execute(state)
