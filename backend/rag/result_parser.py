"""
NCBI Response Parser & Result Ranking.

Parses NCBI responses, extracts key metadata, and ranks results by
relevance and quality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class NCBIResponseParser:
    """Parse dense NCBI API responses into a flatter internal structure."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("ncbi_response_parser")

    def parse_variant_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a raw NCBI response entry."""

        try:
            return {
                "id": response.get("accession", "") or response.get("uid", ""),
                "gene": self._extract_gene(response),
                "protein_change": self._extract_protein_change(response),
                "clinical_significance": self._extract_clinical_significance(response),
                "review_status": self._extract_review_status(response),
                "condition": self._extract_condition(response),
                "evidence": self._extract_evidence_summary(response),
                "last_evaluated": self._extract_date(response),
            }
        except Exception as exc:
            self.logger.warning("Parse error: %s", str(exc))
            return {}

    def _extract_gene(self, response: Dict[str, Any]) -> str:
        """Extract gene symbol."""

        genes = response.get("gene_symbol", []) or response.get("genes", [])
        if isinstance(genes, list):
            return genes[0] if genes else "Unknown"
        return str(genes) if genes else "Unknown"

    def _extract_protein_change(self, response: Dict[str, Any]) -> str:
        """Extract protein change notation."""

        protein = response.get("protein_change", {})
        if isinstance(protein, dict):
            return protein.get("canonical_spdi", "") or protein.get("cdna_effect", "")
        return str(protein) if protein else ""

    def _extract_clinical_significance(self, response: Dict[str, Any]) -> str:
        """Extract clinical significance."""

        interpretations = response.get("interpretations", [])
        if interpretations and isinstance(interpretations, list):
            first = interpretations[0]
            if isinstance(first, dict):
                return first.get("clinical_significance", "")
        return response.get("clinical_significance", "")

    def _extract_review_status(self, response: Dict[str, Any]) -> str:
        """Extract review status."""

        return response.get("review_status", "")

    def _extract_condition(self, response: Dict[str, Any]) -> str:
        """Extract associated condition."""

        conditions = response.get("conditions", [])
        if conditions and isinstance(conditions, list):
            first = conditions[0]
            if isinstance(first, dict):
                return first.get("disease_name", "")
        return response.get("condition", "")

    def _extract_evidence_summary(self, response: Dict[str, Any]) -> str:
        """Extract evidence summary text."""

        return response.get("assertion", "") or response.get("evidence", "")

    def _extract_date(self, response: Dict[str, Any]) -> str:
        """Extract last evaluated date."""

        return response.get("last_evaluated", "")


class ResultRanker:
    """
    Rank clinical evidence results by combined score.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("result_ranker")

    def rank_results(
        self,
        results: List[Dict[str, Any]],
        query_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Rank results by combined score and add relevance_score."""

        scored_results = []
        for result in results:
            score = self._calculate_score(result, query_context)
            scored_results.append((result, score))

        scored_results.sort(key=lambda item: item[1], reverse=True)
        return [{**result, "relevance_score": float(score)} for result, score in scored_results]

    def _calculate_score(self, result: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate a combined score between 0 and 1."""

        score = 0.0
        score += self._score_relevance(result, context) * 0.4
        score += self._score_quality(result) * 0.3
        score += self._score_recency(result) * 0.2
        score += self._score_expert_review(result) * 0.1
        return min(1.0, score)

    def _score_relevance(self, result: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Score relevance to the current query context."""

        score = 0.0
        if context.get("gene") and result.get("gene"):
            if str(context["gene"]).upper() == str(result["gene"]).upper():
                score += 0.4

        if context.get("protein_change") and result.get("protein_change"):
            if str(context["protein_change"]).upper() in str(result["protein_change"]).upper():
                score += 0.4

        if context.get("condition") and result.get("condition"):
            if str(context["condition"]).lower() in str(result["condition"]).lower():
                score += 0.2

        return min(1.0, score)

    def _score_quality(self, result: Dict[str, Any]) -> float:
        """Score evidence quality."""

        score = 0.5
        significance = result.get("clinical_significance", "")
        if significance in ["Pathogenic", "Benign"]:
            score += 0.3
        elif significance in ["Likely pathogenic", "Likely benign"]:
            score += 0.2

        review = result.get("review_status", "")
        if "expert" in str(review).lower():
            score += 0.2

        return min(1.0, score)

    def _score_recency(self, result: Dict[str, Any]) -> float:
        """Score recency of evaluation."""

        date_str = result.get("last_evaluated", "")
        if not date_str:
            return 0.3

        try:
            eval_date = datetime.fromisoformat(date_str)
            days_ago = (datetime.now() - eval_date).days
            if days_ago < 365:
                return 1.0
            if days_ago < 1825:
                return 0.7
            return 0.4
        except Exception:
            return 0.3

    def _score_expert_review(self, result: Dict[str, Any]) -> float:
        """Score the expert-review level."""

        review = str(result.get("review_status", ""))
        if "expert panel" in review.lower():
            return 1.0
        if "reviewed" in review.lower():
            return 0.7
        return 0.3


class ResultFormatter:
    """Format ranked results into user-readable summaries."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("result_formatter")

    def format_for_display(self, results: List[Dict[str, Any]]) -> List[str]:
        """Format results for display."""

        return [self._format_single_result(result, index) for index, result in enumerate(results, 1)]

    def _format_single_result(self, result: Dict[str, Any], index: int) -> str:
        """Format a single result."""

        lines = []
        lines.append(f"\n{'=' * 60}")
        lines.append(f"Finding #{index} (Relevance: {result.get('relevance_score', 0):.1%})")
        lines.append(f"{'=' * 60}")

        if result.get("gene"):
            lines.append(f"Gene: {result['gene']}")
        if result.get("protein_change"):
            lines.append(f"Protein Change: {result['protein_change']}")
        if result.get("clinical_significance"):
            lines.append(f"Classification: {result['clinical_significance']}")
        if result.get("condition"):
            lines.append(f"Associated Condition: {result['condition']}")
        if result.get("review_status"):
            lines.append(f"Review Status: {result['review_status']}")
        if result.get("evidence"):
            lines.append(f"Evidence: {str(result['evidence'])[:200]}...")
        if result.get("last_evaluated"):
            lines.append(f"Last Evaluated: {result['last_evaluated']}")

        return "\n".join(lines)


parser = NCBIResponseParser()
ranker = ResultRanker()
formatter = ResultFormatter()

logger.info("Result parsing and ranking initialized")

__all__ = [
    "NCBIResponseParser",
    "ResultRanker",
    "ResultFormatter",
    "parser",
    "ranker",
    "formatter",
]
