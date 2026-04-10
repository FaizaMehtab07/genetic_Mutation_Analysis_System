"""
Annotation Agent - Translates DNA mutations to protein effects.

Determines the impact of mutations on the protein level:
- Missense
- Nonsense
- Synonymous
- Frameshift
"""

import logging
from typing import Any, Dict, List

from backend.models.pydantic_models import (
    Annotation,
    AnnotationOutput,
    Mutation,
    MutationEffectEnum,
    MutationTypeEnum,
)

logger = logging.getLogger(__name__)


class AnnotationAgent:
    """
    Agent for annotating mutations with protein-level effects.
    """

    GENETIC_CODE = {
        "TTT": "F",
        "TTC": "F",
        "TTA": "L",
        "TTG": "L",
        "TCT": "S",
        "TCC": "S",
        "TCA": "S",
        "TCG": "S",
        "TAT": "Y",
        "TAC": "Y",
        "TAA": "*",
        "TAG": "*",
        "TGT": "C",
        "TGC": "C",
        "TGA": "*",
        "TGG": "W",
        "CTT": "L",
        "CTC": "L",
        "CTA": "L",
        "CTG": "L",
        "CCT": "P",
        "CCC": "P",
        "CCA": "P",
        "CCG": "P",
        "CAT": "H",
        "CAC": "H",
        "CAA": "Q",
        "CAG": "Q",
        "CGT": "R",
        "CGC": "R",
        "CGA": "R",
        "CGG": "R",
        "ATT": "I",
        "ATC": "I",
        "ATA": "I",
        "ATG": "M",
        "ACT": "T",
        "ACC": "T",
        "ACA": "T",
        "ACG": "T",
        "AAT": "N",
        "AAC": "N",
        "AAA": "K",
        "AAG": "K",
        "AGT": "S",
        "AGC": "S",
        "AGA": "R",
        "AGG": "R",
        "GTT": "V",
        "GTC": "V",
        "GTA": "V",
        "GTG": "V",
        "GCT": "A",
        "GCC": "A",
        "GCA": "A",
        "GCG": "A",
        "GAT": "D",
        "GAC": "D",
        "GAA": "E",
        "GAG": "E",
        "GGT": "G",
        "GGC": "G",
        "GGA": "G",
        "GGG": "G",
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger("agents.annotation")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Annotate detected mutations with protein-level effects."""

        self.logger.info("Annotation Agent: Starting annotation")

        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            mutations = state.get("mutations", []) or []
            reference_sequence = state.get("reference_sequence", "") or ""

            if not mutations:
                result = AnnotationOutput(
                    annotated_mutations=[],
                    impact_summary={"high": 0, "moderate": 0, "low": 0},
                )
                state["annotations"] = result
                state["annotation_result"] = result
                state["annotated_mutations"] = []
                state["impact_summary"] = result.impact_summary
                if not state.get("errors"):
                    state["status"] = "completed"
                return state

            if not reference_sequence:
                raise ValueError("Reference sequence not found in state")

            annotated_mutations: List[Annotation] = []
            impact_counts = {"high": 0, "moderate": 0, "low": 0}

            for mutation in mutations:
                try:
                    annotation = self._annotate_mutation(mutation, reference_sequence)
                    annotated_mutations.append(annotation)

                    if annotation.effect in (
                        MutationEffectEnum.FRAMESHIFT,
                        MutationEffectEnum.NONSENSE,
                    ):
                        impact_counts["high"] += 1
                    elif annotation.effect in (
                        MutationEffectEnum.MISSENSE,
                        MutationEffectEnum.INFRAME_INSERTION,
                        MutationEffectEnum.INFRAME_DELETION,
                    ):
                        impact_counts["moderate"] += 1
                    else:
                        impact_counts["low"] += 1
                except Exception as exc:
                    self.logger.warning(
                        "Failed to annotate mutation at position %s: %s",
                        mutation.position,
                        str(exc),
                    )

            result = AnnotationOutput(
                annotated_mutations=annotated_mutations,
                impact_summary=impact_counts,
            )

            state["annotations"] = result
            state["annotation_result"] = result
            state["annotated_mutations"] = annotated_mutations
            state["impact_summary"] = impact_counts

            if not state.get("errors"):
                state["status"] = "completed"

            self.logger.info(
                "Annotated %s mutations: high=%s, moderate=%s, low=%s",
                len(annotated_mutations),
                impact_counts["high"],
                impact_counts["moderate"],
                impact_counts["low"],
            )

            return state

        except Exception as exc:
            self.logger.error("Annotation error: %s", str(exc), exc_info=True)
            state["status"] = "failed"
            state["errors"].append(f"Annotation failed: {str(exc)}")
            empty_result = AnnotationOutput(
                annotated_mutations=[],
                impact_summary={"high": 0, "moderate": 0, "low": 0},
            )
            state["annotations"] = empty_result
            state["annotation_result"] = empty_result
            state["annotated_mutations"] = []
            state["impact_summary"] = empty_result.impact_summary
            return state

    def _annotate_mutation(self, mutation: Mutation, reference_sequence: str) -> Annotation:
        """Annotate a single mutation."""

        position_0 = mutation.position - 1
        codon_index = position_0 // 3
        codon_position = position_0 % 3
        codon_start = codon_index * 3
        codon_end = codon_start + 3

        if codon_end > len(reference_sequence):
            raise ValueError(f"Position {mutation.position} outside sequence")

        ref_codon = reference_sequence[codon_start:codon_end]

        if mutation.type == MutationTypeEnum.SUBSTITUTION:
            mut_codon_list = list(ref_codon)
            if not mutation.alternate_base:
                raise ValueError("Substitution missing alternate base")
            mut_codon_list[codon_position] = mutation.alternate_base
            mut_codon = "".join(mut_codon_list)

            ref_aa = self.GENETIC_CODE.get(ref_codon, "?")
            mut_aa = self.GENETIC_CODE.get(mut_codon, "?")

            if ref_aa == "?" or mut_aa == "?":
                effect = MutationEffectEnum.UNKNOWN
                impact = "Unknown codon translation"
            elif ref_aa == mut_aa:
                effect = MutationEffectEnum.SYNONYMOUS
                impact = f"Silent mutation - no amino acid change ({ref_aa})"
            elif mut_aa == "*":
                effect = MutationEffectEnum.NONSENSE
                impact = f"Nonsense mutation - creates stop codon ({ref_aa}*)"
            else:
                effect = MutationEffectEnum.MISSENSE
                impact = f"Missense mutation - amino acid change {ref_aa}->{mut_aa}"

            return Annotation(
                type=mutation.type,
                position=mutation.position,
                reference_base=mutation.reference_base,
                alternate_base=mutation.alternate_base,
                protein_position=codon_index + 1,
                reference_codon=ref_codon,
                mutant_codon=mut_codon,
                reference_aa=ref_aa,
                mutant_aa=mut_aa,
                protein_change=f"{ref_aa}{codon_index + 1}{mut_aa}",
                effect=effect,
                impact=impact,
            )

        length = mutation.length or 0
        if mutation.type == MutationTypeEnum.INSERTION and length % 3 == 0:
            effect = MutationEffectEnum.INFRAME_INSERTION
            impact = "In-frame insertion - reading frame preserved"
        elif mutation.type == MutationTypeEnum.DELETION and length % 3 == 0:
            effect = MutationEffectEnum.INFRAME_DELETION
            impact = "In-frame deletion - reading frame preserved"
        else:
            effect = MutationEffectEnum.FRAMESHIFT
            impact = f"Frameshift {mutation.type.value} - reading frame disrupted"

        return Annotation(
            type=mutation.type,
            position=mutation.position,
            reference_base=mutation.reference_base,
            alternate_base=mutation.alternate_base,
            protein_position=codon_index + 1,
            effect=effect,
            impact=impact,
        )


def annotation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node wrapper for annotation.
    """

    agent = AnnotationAgent()
    return agent.execute(state)
