"""
Classification Agent - Classifies mutations as pathogenic or benign.

Uses a combination of:
1. Rule-based classification
2. Optional ML-based classification
3. Ensemble selection when both are available
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.core.config import settings
from backend.models.pydantic_models import (
    ClassificationEnum,
    ClassificationOutput,
    ConfidenceEnum,
    MutationEffectEnum,
    RiskLevelEnum,
)

logger = logging.getLogger(__name__)


class ClassificationAgent:
    """
    Agent for classifying mutation pathogenicity.

    Input State:
        - annotations: AnnotationOutput

    Output State:
        - classification_result: ClassificationOutput
    """

    RULE_BASED_CLASSIFICATIONS = {
        MutationEffectEnum.FRAMESHIFT: ClassificationEnum.PATHOGENIC,
        MutationEffectEnum.NONSENSE: ClassificationEnum.PATHOGENIC,
        MutationEffectEnum.MISSENSE: ClassificationEnum.POTENTIALLY_PATHOGENIC,
        MutationEffectEnum.INFRAME_INSERTION: ClassificationEnum.POTENTIALLY_PATHOGENIC,
        MutationEffectEnum.INFRAME_DELETION: ClassificationEnum.POTENTIALLY_PATHOGENIC,
        MutationEffectEnum.SYNONYMOUS: ClassificationEnum.BENIGN,
        MutationEffectEnum.UNKNOWN: ClassificationEnum.UNCERTAIN,
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger("agents.classification")
        self.ml_model = None
        self.ml_scaler = None
        self.ml_label_encoder = None
        self.use_ml = bool(settings.use_ml_classifier)
        self._load_ml_model()

    def _load_ml_model(self) -> None:
        """Load a pre-trained ML model if one is configured and present."""

        if not self.use_ml:
            self.logger.info("ML classifier disabled")
            return

        try:
            import joblib

            model_path = Path(settings.ml_model_path)
            scaler_path = Path(settings.ml_scaler_path)
            label_encoder_path = Path(settings.ml_label_encoder_path)

            if model_path.exists() and scaler_path.exists() and label_encoder_path.exists():
                self.ml_model = joblib.load(model_path)
                self.ml_scaler = joblib.load(scaler_path)
                self.ml_label_encoder = joblib.load(label_encoder_path)
                self.logger.info("ML model and label encoder loaded successfully")
            else:
                self.logger.warning(
                    "ML model files not found: model=%s scaler=%s encoder=%s",
                    model_path.exists(),
                    scaler_path.exists(),
                    label_encoder_path.exists(),
                )
                self.use_ml = False
        except ImportError:
            self.logger.warning("joblib not installed - ML classification disabled")
            self.use_ml = False
        except Exception as exc:
            self.logger.warning("Failed to load ML model: %s", str(exc))
            self.use_ml = False

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify annotated mutations and write results into workflow state.
        """

        self.logger.info("Classification Agent: Starting classification")

        state.setdefault("errors", [])
        state.setdefault("warnings", [])

        try:
            annotations = state.get("annotations")

            if not annotations or not annotations.annotated_mutations:
                result = ClassificationOutput(
                    overall_classification=ClassificationEnum.UNCERTAIN,
                    risk_level=RiskLevelEnum.LOW,
                    confidence=ConfidenceEnum.LOW,
                    rationale="No mutations to classify",
                    classified_mutations=[],
                    summary={},
                    recommendation="No pathogenic variants detected",
                )
                state["classification_result"] = result
                return state

            classified_mutations: List[Dict[str, Any]] = []
            classification_counts = {
                ClassificationEnum.PATHOGENIC.value: 0,
                ClassificationEnum.POTENTIALLY_PATHOGENIC.value: 0,
                ClassificationEnum.UNCERTAIN.value: 0,
                ClassificationEnum.BENIGN.value: 0,
            }

            for mutation in annotations.annotated_mutations:
                rule_classification = self.RULE_BASED_CLASSIFICATIONS.get(
                    mutation.effect,
                    ClassificationEnum.UNCERTAIN,
                )

                ml_classification: Optional[ClassificationEnum] = None
                ml_probability: Optional[float] = None

                if self.use_ml and self.ml_model is not None:
                    try:
                        ml_classification, ml_probability = self._get_ml_classification(
                            mutation,
                            str(state.get("gene", "")),
                        )
                    except Exception as exc:
                        self.logger.warning("ML classification failed: %s", str(exc))

                final_classification = self._ensemble_classification(
                    rule_classification,
                    ml_classification,
                    ml_probability,
                )
                risk_level = self._get_risk_level(final_classification)
                confidence = self._get_confidence(ml_classification, ml_probability)

                classified_mutation = {
                    "effect": mutation.effect.value,
                    "protein_change": mutation.protein_change,
                    "position": mutation.position,
                    "rule_based_classification": rule_classification.value,
                    "ml_classification": ml_classification.value if ml_classification else None,
                    "ml_probability": ml_probability,
                    "final_classification": final_classification.value,
                    "risk_level": risk_level.value,
                    "confidence": confidence.value,
                    "rationale": self._generate_rationale(
                        mutation,
                        rule_classification,
                        ml_classification,
                        ml_probability,
                    ),
                }

                classified_mutations.append(classified_mutation)
                classification_counts[final_classification.value] += 1

            overall_classification = self._determine_overall_classification(
                classification_counts
            )
            overall_risk = self._get_risk_level(overall_classification)
            overall_confidence = (
                ConfidenceEnum.HIGH if self.use_ml else ConfidenceEnum.MODERATE
            )

            result = ClassificationOutput(
                overall_classification=overall_classification,
                risk_level=overall_risk,
                confidence=overall_confidence,
                rationale=self._generate_overall_rationale(
                    classification_counts,
                    self.use_ml,
                ),
                classified_mutations=classified_mutations,
                summary=classification_counts,
                recommendation=self._generate_recommendation(overall_classification),
            )

            state["classification_result"] = result
            state["classified_mutations"] = classified_mutations

            self.logger.info(
                "Classification complete: %s, risk=%s",
                overall_classification.value,
                overall_risk.value,
            )
            return state

        except Exception as exc:
            self.logger.error("Classification error: %s", str(exc), exc_info=True)
            state["errors"].append(f"Classification failed: {str(exc)}")
            state["classification_result"] = ClassificationOutput(
                overall_classification=ClassificationEnum.UNCERTAIN,
                risk_level=RiskLevelEnum.MODERATE,
                confidence=ConfidenceEnum.LOW,
                rationale="Classification failed",
                classified_mutations=[],
                summary={},
                recommendation="Manual review recommended",
            )
            return state

    def _get_ml_classification(
        self,
        mutation: Any,
        gene: str,
    ) -> Tuple[Optional[ClassificationEnum], Optional[float]]:
        """
        Get ML-based classification for a single mutation.
        """

        if self.ml_model is None or self.ml_scaler is None or self.ml_label_encoder is None:
            return None, None

        features = self._extract_ml_features(mutation, gene)
        features_scaled = self.ml_scaler.transform([features])

        prediction = self.ml_model.predict(features_scaled)[0]
        probability_vector = self.ml_model.predict_proba(features_scaled)[0]
        probability = float(max(probability_vector))

        label = self.ml_label_encoder.inverse_transform([prediction])[0]
        classification_map = {
            "Pathogenic": ClassificationEnum.PATHOGENIC,
            "Potentially Pathogenic": ClassificationEnum.POTENTIALLY_PATHOGENIC,
            "Uncertain": ClassificationEnum.UNCERTAIN,
            "Benign": ClassificationEnum.BENIGN,
        }

        classification = classification_map.get(label, ClassificationEnum.UNCERTAIN)
        return classification, probability

    def _extract_ml_features(self, mutation: Any, gene: str) -> List[float]:
        """
        Build a small feature vector for the optional ML classifier.
        """

        effect_encoding = {
            MutationEffectEnum.FRAMESHIFT: [1, 0, 0, 0, 0, 0],
            MutationEffectEnum.NONSENSE: [0, 1, 0, 0, 0, 0],
            MutationEffectEnum.MISSENSE: [0, 0, 1, 0, 0, 0],
            MutationEffectEnum.INFRAME_INSERTION: [0, 0, 0, 1, 0, 0],
            MutationEffectEnum.INFRAME_DELETION: [0, 0, 0, 0, 1, 0],
            MutationEffectEnum.SYNONYMOUS: [0, 0, 0, 0, 0, 1],
        }

        features: List[float] = []
        features.extend(effect_encoding.get(mutation.effect, [0, 0, 0, 0, 0, 0]))

        gene_order = [
            "TP53",
            "BRCA1",
            "BRCA2",
            "EGFR",
            "APP",
            "PSEN1",
            "TCF7L2",
            "PPARG",
            "FTO",
        ]

        for known_gene in gene_order:
            features.append(1.0 if gene.upper() == known_gene else 0.0)

        features.append(min(mutation.position / 1_000_000, 1.0) if mutation.position else 0.0)
        features.append(1.0 if getattr(mutation, "protein_change", None) else 0.0)
        return features

    def _ensemble_classification(
        self,
        rule_classification: ClassificationEnum,
        ml_classification: Optional[ClassificationEnum],
        ml_probability: Optional[float],
    ) -> ClassificationEnum:
        """
        Combine rule-based and ML classifications.
        """

        if ml_classification is None:
            return rule_classification

        if ml_classification == rule_classification:
            return ml_classification

        if ml_probability is not None and (ml_probability > 0.8 or ml_probability < 0.2):
            return ml_classification

        return rule_classification

    def _get_risk_level(self, classification: ClassificationEnum) -> RiskLevelEnum:
        """Map a classification to risk level."""

        return {
            ClassificationEnum.PATHOGENIC: RiskLevelEnum.HIGH,
            ClassificationEnum.POTENTIALLY_PATHOGENIC: RiskLevelEnum.MODERATE,
            ClassificationEnum.UNCERTAIN: RiskLevelEnum.MODERATE,
            ClassificationEnum.BENIGN: RiskLevelEnum.LOW,
        }.get(classification, RiskLevelEnum.MODERATE)

    def _get_confidence(
        self,
        ml_classification: Optional[ClassificationEnum],
        ml_probability: Optional[float],
    ) -> ConfidenceEnum:
        """Estimate confidence for a classified mutation."""

        if ml_classification is None or ml_probability is None:
            return ConfidenceEnum.MODERATE
        if ml_probability > 0.85 or ml_probability < 0.15:
            return ConfidenceEnum.HIGH
        if 0.4 <= ml_probability <= 0.6:
            return ConfidenceEnum.LOW
        return ConfidenceEnum.MODERATE

    def _determine_overall_classification(
        self,
        counts: Dict[str, int],
    ) -> ClassificationEnum:
        """Determine overall sample classification from mutation counts."""

        if counts.get(ClassificationEnum.PATHOGENIC.value, 0) > 0:
            return ClassificationEnum.PATHOGENIC
        if counts.get(ClassificationEnum.POTENTIALLY_PATHOGENIC.value, 0) > 0:
            return ClassificationEnum.POTENTIALLY_PATHOGENIC
        if counts.get(ClassificationEnum.UNCERTAIN.value, 0) > 0:
            return ClassificationEnum.UNCERTAIN
        return ClassificationEnum.BENIGN

    def _generate_rationale(
        self,
        mutation: Any,
        rule_classification: ClassificationEnum,
        ml_classification: Optional[ClassificationEnum],
        ml_probability: Optional[float],
    ) -> str:
        """Generate a rationale for a single mutation classification."""

        rationale = f"Effect: {mutation.effect.value} -> {rule_classification.value}"
        if ml_classification is not None and ml_probability is not None:
            rationale += f" (ML: {ml_classification.value} @ {ml_probability:.1%})"
        return rationale

    def _generate_overall_rationale(
        self,
        counts: Dict[str, int],
        use_ml: bool,
    ) -> str:
        """Generate a summary rationale for the overall result."""

        total = sum(counts.values())
        rationale = (
            f"Classification based on {total} mutation(s): "
            f"{counts.get(ClassificationEnum.PATHOGENIC.value, 0)} pathogenic, "
            f"{counts.get(ClassificationEnum.POTENTIALLY_PATHOGENIC.value, 0)} potentially pathogenic, "
            f"{counts.get(ClassificationEnum.UNCERTAIN.value, 0)} uncertain, "
            f"{counts.get(ClassificationEnum.BENIGN.value, 0)} benign"
        )
        if use_ml:
            rationale += " (ML-enhanced)"
        return rationale

    def _generate_recommendation(self, classification: ClassificationEnum) -> str:
        """Generate a clinical recommendation for the overall classification."""

        recommendations = {
            ClassificationEnum.PATHOGENIC: (
                "HIGH RISK: Mutation likely pathogenic. Recommended: genetic counseling, "
                "family screening, and clinical correlation."
            ),
            ClassificationEnum.POTENTIALLY_PATHOGENIC: (
                "MODERATE RISK: Mutation possibly pathogenic. Recommended: further evaluation, "
                "ClinVar review, and functional studies."
            ),
            ClassificationEnum.UNCERTAIN: (
                "UNCERTAIN SIGNIFICANCE: Classification unclear. Recommended: monitor the "
                "literature and reassess with new evidence."
            ),
            ClassificationEnum.BENIGN: (
                "LOW RISK: Mutation appears benign. Recommended: standard clinical care."
            ),
        }
        return recommendations.get(
            classification,
            "Consult with a genetic counselor for interpretation.",
        )


def classification_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for classification."""

    agent = ClassificationAgent()
    return agent.execute(state)
