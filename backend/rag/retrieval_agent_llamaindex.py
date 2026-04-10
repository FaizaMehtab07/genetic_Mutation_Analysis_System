"""
Retrieval Agent - Live NCBI with automatic local ClinVar fallback.

Behavior:
1. Try live NCBI ClinVar retrieval when an email is configured.
2. If live retrieval is unavailable or empty, fall back to the local ClinVar CSV.
3. Return ranked clinical evidence without failing the whole workflow.

Gemini is kept optional and out of the retrieval critical path for now.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.config import settings
from backend.models.pydantic_models import ClinVarRecord, RetrievalOutput
from backend.rag.clinvar_schema import clinvar_schema, filter_builder, query_mapper
from backend.rag.ncbi_client import NCBIClientWithCache
from backend.rag.result_parser import parser, ranker

logger = logging.getLogger(__name__)


class LlamaIndexRetrievalAgent:
    """
    Retrieval agent for clinical evidence.
    """

    def __init__(self, ncbi_email: str, ncbi_api_key: Optional[str] = None) -> None:
        self.logger = logging.getLogger("retrieval_agent")
        self.ncbi_client = NCBIClientWithCache(
            ncbi_email,
            ncbi_api_key,
            cache_ttl=settings.cache_ttl_seconds,
        )
        self.schema = clinvar_schema
        self.mapper = query_mapper
        self.filter_builder = filter_builder
        self.local_clinvar_path = Path(settings.clinvar_csv_path)
        self.logger.info("Retrieval Agent initialized")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute retrieval workflow and attach evidence to workflow state.
        """

        self.logger.info("Retrieval Agent: Starting evidence retrieval")
        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            mutations = state.get("mutations", []) or []
            gene = state.get("gene", "") or ""

            if not mutations or not gene:
                self.logger.info("No mutations or gene to retrieve evidence for")
                self._set_retrieval_state(
                    state,
                    gene=gene,
                    evidence=[],
                    success=True,
                    error=None,
                )
                return state

            live_evidence: List[ClinVarRecord] = []
            live_error: Optional[str] = None

            if self._live_ncbi_enabled():
                try:
                    search_queries = self._build_search_queries(mutations, gene)
                    raw_evidence: List[Dict[str, Any]] = []

                    for query in search_queries:
                        try:
                            raw_evidence.extend(self._search_and_fetch(query))
                        except Exception as exc:
                            self.logger.warning("Search failed for '%s': %s", query, str(exc))
                            state["warnings"].append(f"Evidence retrieval partial: {str(exc)}")

                    live_evidence = self._rank_live_evidence(raw_evidence, mutations, gene)
                except Exception as exc:
                    live_error = str(exc)
                    self.logger.warning("Live NCBI retrieval failed: %s", live_error)
                    state["warnings"].append(f"Live ClinVar retrieval unavailable: {live_error}")
            else:
                state["warnings"].append(
                    "Live ClinVar retrieval not configured; using local ClinVar fallback."
                )

            if live_evidence:
                self._set_retrieval_state(
                    state,
                    gene=gene,
                    evidence=live_evidence,
                    success=True,
                    error=None,
                )
                return state

            local_evidence = self._retrieve_from_local_clinvar(mutations, gene)
            if local_evidence:
                state["warnings"].append("Using local ClinVar fallback data.")
                self._set_retrieval_state(
                    state,
                    gene=gene,
                    evidence=local_evidence,
                    success=True,
                    error=None,
                )
                return state

            error_message = live_error or None
            self._set_retrieval_state(
                state,
                gene=gene,
                evidence=[],
                success=live_error is None,
                error=error_message,
            )
            return state

        except Exception as exc:
            self.logger.error("Retrieval error: %s", str(exc), exc_info=True)
            state["warnings"].append(f"Retrieval unavailable: {str(exc)}")
            self._set_retrieval_state(
                state,
                gene=str(state.get("gene", "")),
                evidence=[],
                success=False,
                error=str(exc),
            )
            return state

    def _live_ncbi_enabled(self) -> bool:
        """Check whether live NCBI retrieval is configured."""

        return bool(settings.use_llamaindex and settings.ncbi_email and settings.ncbi_email != "geneMutation@example.com")

    def _set_retrieval_state(
        self,
        state: Dict[str, Any],
        gene: str,
        evidence: List[ClinVarRecord],
        success: bool,
        error: Optional[str],
    ) -> None:
        """Write retrieval outputs back into state."""

        output = RetrievalOutput(
            success=success,
            total_evidence=len(evidence),
            evidence=evidence,
            database="ClinVar",
            gene=gene,
            error=error,
        )
        state["clinical_evidence"] = evidence
        state["evidence_retrieval_output"] = output

    def _build_search_queries(self, mutations: List[Any], gene: str) -> List[str]:
        """Build a small set of ClinVar search queries from the state."""

        queries = [f"{gene}[gene] AND pathogenic[clinical_significance]"]

        for mutation in mutations[:3]:
            protein_change = getattr(mutation, "protein_change", None)
            if protein_change:
                queries.append(f"{gene} {protein_change}")

            mutation_type = getattr(mutation, "type", None)
            if mutation_type is not None:
                source_value = mutation_type.value if hasattr(mutation_type, "value") else str(mutation_type)
                translated = self.mapper.translate_query(str(source_value))
                if translated:
                    _, technical_value = translated
                    queries.append(f"{gene}[gene] AND \"{technical_value}\"")

        queries.append(f"{gene}[gene] AND clinvar[filter]")
        return list(dict.fromkeys(query for query in queries if query))

    def _search_and_fetch(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search NCBI and fetch detailed variant information."""

        search_result = self.ncbi_client.search_clinvar(query, max_results)
        if not search_result.get("success") or not search_result.get("ids"):
            self.logger.debug("No results for query: %s", query)
            return []

        variant_ids = search_result["ids"][:max_results]
        return self.ncbi_client.fetch_clinvar_details(variant_ids)

    def _rank_live_evidence(
        self,
        evidence: List[Dict[str, Any]],
        mutations: List[Any],
        gene: str,
    ) -> List[ClinVarRecord]:
        """Rank live NCBI evidence and convert it to ClinVarRecord objects."""

        normalized_results = []
        for item in evidence:
            if item:
                normalized = parser.parse_variant_response(item)
                normalized["clinvar_id"] = item.get(
                    "clinvar_id",
                    item.get("uid", item.get("accession", "unknown")),
                )
                normalized["variant_type"] = item.get("variant_type", "")
                normalized_results.append(normalized)

        protein_change = None
        for mutation in mutations:
            if getattr(mutation, "protein_change", None):
                protein_change = mutation.protein_change
                break

        ranked = ranker.rank_results(
            normalized_results,
            {
                "gene": gene,
                "protein_change": protein_change,
            },
        )

        records: List[ClinVarRecord] = []
        seen_ids = set()
        for result in ranked:
            mutation_id = str(result.get("clinvar_id") or result.get("id") or "unknown")
            if mutation_id in seen_ids:
                continue
            seen_ids.add(mutation_id)

            records.append(
                ClinVarRecord(
                    mutation_id=mutation_id,
                    position=self._infer_position(mutations),
                    mutation_type=result.get("variant_type", "") or "variant",
                    clinical_significance=result.get("clinical_significance", "") or "Unknown",
                    review_status=result.get("review_status", ""),
                    condition=result.get("condition", "") or "Not specified",
                    evidence_summary=self._generate_evidence_summary(result),
                    protein_change=result.get("protein_change", ""),
                    match_quality=float(result.get("relevance_score", 0.0)),
                )
            )

        return records[:10]

    def _retrieve_from_local_clinvar(
        self,
        mutations: List[Any],
        gene: str,
    ) -> List[ClinVarRecord]:
        """Search the local ClinVar CSV as an automatic fallback."""

        if not self.local_clinvar_path.exists():
            self.logger.warning("Local ClinVar fallback file not found: %s", self.local_clinvar_path)
            return []

        try:
            records: List[ClinVarRecord] = []
            with self.local_clinvar_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    row_gene = (row.get("gene") or row.get("GeneSymbol") or "").upper()
                    if row_gene != gene.upper():
                        continue

                    score = self._score_local_match(row, mutations)
                    if score <= 0:
                        continue

                    mutation_id = (
                        row.get("mutation_id")
                        or row.get("VariationID")
                        or row.get("clinvar_id")
                        or f"{row_gene}:{row.get('position', 'unknown')}"
                    )
                    position = self._safe_int(row.get("position")) or self._infer_position(mutations)
                    mutation_type = row.get("mutation_type") or row.get("VariationType") or "variant"
                    clinical_significance = (
                        row.get("clinical_significance")
                        or row.get("ClinicalSignificance")
                        or "Unknown"
                    )
                    review_status = row.get("review_status") or row.get("ReviewStatus") or ""
                    condition = row.get("condition") or row.get("Condition") or "Not specified"
                    protein_change = row.get("protein_change") or row.get("Protein") or ""
                    evidence_summary = (
                        row.get("evidence_summary")
                        or row.get("assertion_method")
                        or self._generate_local_summary(row_gene, protein_change, clinical_significance, condition)
                    )

                    records.append(
                        ClinVarRecord(
                            mutation_id=str(mutation_id),
                            position=max(position, 1),
                            mutation_type=str(mutation_type),
                            clinical_significance=str(clinical_significance),
                            review_status=str(review_status),
                            condition=str(condition),
                            evidence_summary=str(evidence_summary),
                            protein_change=str(protein_change),
                            match_quality=float(min(score, 1.0)),
                        )
                    )

            records.sort(key=lambda item: item.match_quality, reverse=True)

            unique_records: List[ClinVarRecord] = []
            seen_ids = set()
            for record in records:
                if record.mutation_id in seen_ids:
                    continue
                seen_ids.add(record.mutation_id)
                unique_records.append(record)

            return unique_records[:10]
        except Exception as exc:
            self.logger.warning("Local ClinVar fallback failed: %s", str(exc))
            return []

    def _score_local_match(self, row: Dict[str, Any], mutations: List[Any]) -> float:
        """Score how well a local CSV row matches the queried mutations."""

        row_position = self._safe_int(row.get("position"))
        row_type = (row.get("mutation_type") or row.get("VariationType") or "").lower()
        row_protein = (row.get("protein_change") or row.get("Protein") or "").lower()

        best_score = 0.2
        for mutation in mutations:
            score = 0.3
            mutation_position = getattr(mutation, "position", None)
            mutation_type = getattr(mutation, "type", None)
            mutation_type_value = (
                mutation_type.value.lower() if hasattr(mutation_type, "value") else str(mutation_type).lower()
            )
            mutation_protein = getattr(mutation, "protein_change", "") or ""

            if row_type and mutation_type_value and mutation_type_value in row_type:
                score += 0.25

            if row_position is not None and mutation_position is not None:
                distance = abs(row_position - mutation_position)
                if distance == 0:
                    score += 0.35
                elif distance <= 5:
                    score += 0.2
                elif distance <= 10:
                    score += 0.1

            if row_protein and mutation_protein and mutation_protein.lower() in row_protein:
                score += 0.2

            best_score = max(best_score, score)

        return min(best_score, 1.0)

    def _safe_int(self, value: Any) -> Optional[int]:
        """Convert a value to int when possible."""

        try:
            if value in (None, ""):
                return None
            return int(float(str(value)))
        except Exception:
            return None

    def _infer_position(self, mutations: List[Any]) -> int:
        """Infer a representative position from the current mutation list."""

        if not mutations:
            return 1
        first = mutations[0]
        position = getattr(first, "position", 1)
        return position if isinstance(position, int) and position > 0 else 1

    def _generate_evidence_summary(self, evidence: Dict[str, Any]) -> str:
        """Generate a human-readable evidence summary."""

        summary = f"{evidence.get('gene', 'Unknown gene')}: "
        if evidence.get("protein_change"):
            summary += f"{evidence['protein_change']} - "
        summary += f"Classification: {evidence.get('clinical_significance', 'Unknown')}."
        if evidence.get("condition"):
            summary += f" Associated with {evidence['condition']}."
        return summary

    def _generate_local_summary(
        self,
        gene: str,
        protein_change: str,
        clinical_significance: str,
        condition: str,
    ) -> str:
        """Generate a default summary for local fallback evidence."""

        summary = f"{gene}: "
        if protein_change:
            summary += f"{protein_change} - "
        summary += f"Classification: {clinical_significance}."
        if condition:
            summary += f" Associated with {condition}."
        return summary


def retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for retrieval.
    """

    agent = LlamaIndexRetrievalAgent(settings.ncbi_email, settings.ncbi_api_key)
    return agent.execute(state)


__all__ = [
    "LlamaIndexRetrievalAgent",
    "retrieval_node",
]
