"""
Alignment Agent - Aligns sequences using Biopython.

Uses Biopython local alignment to align the query sequence against
the selected reference gene sequence.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from backend.core.config import settings
from backend.core.constants import SUPPORTED_GENES
from backend.models.pydantic_models import AlignmentOutput, GeneEnum

try:
    from Bio import pairwise2

    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("Biopython not installed - alignment disabled")

logger = logging.getLogger(__name__)


class AlignmentAgent:
    """
    Agent for sequence alignment using Biopython.

    Input State:
        - cleaned_sequence: str
        - gene: str

    Output State (adds):
        - alignment_result: AlignmentOutput
        - aligned_reference: str
        - aligned_query: str
        - reference_sequence: str
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("agents.alignment")
        self.reference_sequences: Dict[str, str] = {}
        self._load_reference_sequences()

    def _load_reference_sequences(self) -> None:
        """Load reference sequences from FASTA files into memory."""

        try:
            data_dir = Path(settings.data_dir)

            for gene in sorted(SUPPORTED_GENES):
                fasta_file = data_dir / f"{gene.lower()}_reference.fasta"
                if not fasta_file.exists():
                    self.logger.warning("Reference file not found: %s", fasta_file)
                    continue

                try:
                    sequence = self._read_fasta(fasta_file)
                    self.reference_sequences[gene] = sequence
                    self.logger.debug("Loaded reference for %s: %s bp", gene, len(sequence))
                except Exception as exc:
                    self.logger.warning("Failed to load %s: %s", gene, str(exc))
        except Exception as exc:
            self.logger.error("Error loading reference sequences: %s", str(exc))

    def _read_fasta(self, filepath: Path) -> str:
        """Read a FASTA file and return the concatenated sequence."""

        sequence = ""
        try:
            with filepath.open("r", encoding="utf-8") as file_handle:
                for line in file_handle:
                    line = line.strip()
                    if not line or line.startswith(">"):
                        continue
                    sequence += line.upper()
            return sequence
        except Exception as exc:
            raise RuntimeError(f"Error reading FASTA: {str(exc)}") from exc

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Align the cleaned query sequence against the selected reference."""

        self.logger.info("Alignment Agent: Starting alignment")

        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            if not BIOPYTHON_AVAILABLE:
                raise RuntimeError("Biopython not installed")

            query_sequence = state.get("cleaned_sequence", "") or ""
            gene = state.get("gene", "")

            if isinstance(gene, GeneEnum):
                gene_key = gene.value.upper()
            else:
                gene_key = str(gene).upper() if gene else ""

            if not query_sequence:
                raise ValueError("No cleaned sequence found in state")

            if not gene_key:
                raise ValueError("No gene specified in state")

            reference_sequence = self.reference_sequences.get(gene_key)
            if not reference_sequence:
                raise ValueError(f"Reference sequence not found for gene {gene_key}")

            self.logger.debug(
                "Aligning %s bp query against %s bp reference",
                len(query_sequence),
                len(reference_sequence),
            )

            alignments = pairwise2.align.localms(
                reference_sequence,
                query_sequence,
                match=2,
                mismatch=-1,
                open=-0.5,
                extend=-0.1,
            )

            if not alignments:
                raise ValueError("No alignment found")

            best_alignment = alignments[0]
            aligned_ref = best_alignment[0]
            aligned_query = best_alignment[1]
            score = float(best_alignment[2])

            matches = sum(
                1 for ref_base, query_base in zip(aligned_ref, aligned_query)
                if ref_base == query_base and ref_base != "-"
            )
            mismatches = sum(
                1 for ref_base, query_base in zip(aligned_ref, aligned_query)
                if ref_base != query_base and ref_base != "-" and query_base != "-"
            )
            gaps = sum(
                1 for ref_base, query_base in zip(aligned_ref, aligned_query)
                if ref_base == "-" or query_base == "-"
            )

            ungapped_positions = len(reference_sequence)
            identity = (matches / ungapped_positions * 100) if ungapped_positions > 0 else 0.0

            alignment_result = AlignmentOutput(
                success=True,
                aligned_reference=aligned_ref,
                aligned_query=aligned_query,
                score=score,
                matches=matches,
                mismatches=mismatches,
                gaps=gaps,
                identity_percent=identity,
                reference_length=len(reference_sequence),
                query_length=len(query_sequence),
                alignment_visual=None,
                error=None,
            )

            state["alignment_result"] = alignment_result
            state["aligned_reference"] = aligned_ref
            state["aligned_query"] = aligned_query
            state["reference_sequence"] = reference_sequence
            state["gene"] = gene_key

            self.logger.info(
                "Alignment complete: matches=%s, mismatches=%s, gaps=%s, identity=%.1f%%",
                matches,
                mismatches,
                gaps,
                identity,
            )

            return state

        except Exception as exc:
            self.logger.error("Alignment error: %s", str(exc), exc_info=True)
            state["status"] = "failed"
            state["errors"].append(f"Alignment failed: {str(exc)}")
            state["alignment_result"] = AlignmentOutput(success=False, error=str(exc))
            return state


def alignment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node wrapper for alignment.
    """

    agent = AlignmentAgent()
    return agent.execute(state)
