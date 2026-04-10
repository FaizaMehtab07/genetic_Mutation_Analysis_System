"""
Retrieval Agent - Local ClinVar Evidence Database

This agent searches a local ClinVar database (CSV file) for evidence
about detected mutations. This provides scientific backing for our
classification by showing what is known about similar mutations.

WHAT IS CLINVAR?
- Public database maintained by NIH (National Institutes of Health)
- Contains genetic variants and their clinical significance
- Links mutations to diseases
- Includes expert reviews and evidence

HOW THIS WORKS (LOCAL, NO API):
1. Load ClinVar CSV file using pandas
2. Search for mutations matching:
   - Same gene
   - Same or nearby position
   - Same mutation type
3. Return matching records with clinical significance

This is RAG (Retrieval-Augmented Generation) without the AI generation part.
We retrieve relevant evidence to support our computational predictions.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path
from backend.models.pydantic_models import RetrievalOutput, ClinVarRecord
from backend.core.config import settings

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("Pandas not installed - evidence retrieval disabled")

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """
    Agent for retrieving clinical evidence from local ClinVar database

    Input State:
        - classified_mutations: List[ClassifiedMutation] (from classification)
        - gene: str (gene name)

    Output State (adds):
        - retrieval_result: RetrievalOutput
        - evidence_records: List[ClinVarRecord]
    """

    def __init__(self):
        """Initialize retrieval agent"""
        self.logger = logging.getLogger("agents.retrieval")
        self.clinvar_data = None
        self._load_clinvar_database()

    def _load_clinvar_database(self) -> None:
        """Load ClinVar database from CSV file"""

        if not PANDAS_AVAILABLE:
            self.logger.warning("Pandas not available - evidence retrieval disabled")
            return

        try:
            # Set default path
            data_dir = Path(settings.data_dir)
            clinvar_csv_path = data_dir / 'clinvar_database.csv'

            if clinvar_csv_path.exists():
                # Read CSV file using pandas
                self.clinvar_data = pd.read_csv(clinvar_csv_path)
                self.logger.info(f"Loaded ClinVar database: {len(self.clinvar_data)} records")

                # Verify required columns exist
                required_columns = ['gene', 'position', 'mutation_type', 'clinical_significance']
                missing = [col for col in required_columns if col not in self.clinvar_data.columns]
                if missing:
                    self.logger.warning(f"Missing columns in ClinVar CSV: {missing}")
            else:
                self.logger.warning(f"ClinVar database not found at {clinvar_csv_path}")
                self.clinvar_data = None

        except Exception as e:
            self.logger.error(f"Error loading ClinVar database: {str(e)}")
            self.clinvar_data = None

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve clinical evidence for detected mutations

        Args:
            state: Current workflow state

        Returns:
            Modified state with evidence results
        """

        self.logger.info("Retrieval Agent: Starting evidence search")

        try:
            # Extract input
            classified_mutations = state.get('classified_mutations', [])
            gene = state.get('gene', '')

            if not classified_mutations:
                self.logger.warning("No classified mutations found to search for")
                # Still create result

            if not gene:
                raise ValueError("No gene specified in state")

            self.logger.debug(f"Searching evidence for {len(classified_mutations)} mutations in {gene}")

            # ================================================================
            # RETRIEVE EVIDENCE
            # ================================================================

            evidence_records, total_evidence = self._retrieve_evidence(
                classified_mutations, gene
            )

            self.logger.info(f"Evidence retrieval complete: {total_evidence} records found")

            # ================================================================
            # CREATE RESULT
            # ================================================================

            retrieval_result = RetrievalOutput(
                success=True,
                total_evidence=total_evidence,
                evidence=evidence_records,
                database='ClinVar',
                gene=gene,
                error=None
            )

            # ================================================================
            # UPDATE STATE
            # ================================================================

            state['retrieval_result'] = retrieval_result
            state['evidence_records'] = evidence_records

            return state

        except Exception as e:
            self.logger.error(f"Retrieval error: {str(e)}", exc_info=True)
            state['errors'].append(f"Evidence retrieval failed: {str(e)}")
            state['retrieval_result'] = RetrievalOutput(
                success=False,
                error=str(e)
            )
            return state

    def _retrieve_evidence(self, classified_mutations: List, gene: str) -> tuple:
        """
        Retrieve clinical evidence for mutations

        Args:
            classified_mutations: List of classified mutations
            gene: Gene name

        Returns:
            Tuple of (evidence_records, total_count)
        """

        # Check if database is available
        if self.clinvar_data is None or self.clinvar_data.empty:
            self.logger.warning("ClinVar database not available")
            return [], 0

        # Check if we have mutations to search for
        if not classified_mutations:
            return [], 0

        # Search for evidence for each mutation
        evidence_records = []

        for mutation in classified_mutations:
            # Search ClinVar for this mutation
            matches = self._search_clinvar(mutation, gene)

            # Add each match to evidence list
            for match in matches:
                evidence_record = ClinVarRecord(
                    mutation_id=match.get('mutation_id', 'Unknown'),
                    position=getattr(mutation, 'position', 0),
                    mutation_type=getattr(mutation, 'type', ''),
                    clinical_significance=match.get('clinical_significance', 'Unknown'),
                    review_status=match.get('review_status', 'Not specified'),
                    condition=match.get('condition', 'Not specified'),
                    evidence_summary=match.get('evidence_summary', 'No summary available'),
                    protein_change=match.get('protein_change', 'N/A'),
                    match_quality=self._calculate_match_quality(mutation, match)
                )
                evidence_records.append(evidence_record)

        # Sort by match quality (best matches first)
        evidence_records = sorted(
            evidence_records,
            key=lambda x: x.match_quality,
            reverse=True  # Highest quality first
        )

        # Remove duplicate mutation IDs
        seen_ids = set()
        unique_evidence = []
        for record in evidence_records:
            mut_id = record.mutation_id
            if mut_id not in seen_ids:
                seen_ids.add(mut_id)
                unique_evidence.append(record)

        return unique_evidence, len(unique_evidence)

    def _search_clinvar(self, mutation, gene: str) -> List[Dict]:
        """
        Search ClinVar database for matching mutations

        Args:
            mutation: Mutation to search for
            gene: Gene name

        Returns:
            List of matching ClinVar records
        """
        matches = []

        # Filter database to only this gene
        gene_data = self.clinvar_data[self.clinvar_data['gene'] == gene]

        # If no data for this gene, return empty
        if gene_data.empty:
            return matches

        # Get mutation details
        mutation_type = getattr(mutation, 'type', '')
        position = getattr(mutation, 'position', 0)

        # STRATEGY 1: Exact position and type match
        if position and mutation_type:
            # Convert position to numeric for comparison
            gene_data_copy = gene_data.copy()
            gene_data_copy['position'] = pd.to_numeric(
                gene_data_copy['position'],
                errors='coerce'  # Convert invalid values to NaN
            )

            # Find exact matches
            exact_matches = gene_data_copy[
                (gene_data_copy['mutation_type'] == mutation_type) &
                (gene_data_copy['position'] == position)
            ]

            # Add to matches list
            if not exact_matches.empty:
                matches.extend(exact_matches.to_dict('records'))

        # STRATEGY 2: Proximity match (if no exact matches found)
        if not matches and position and mutation_type:
            # Search within ±5 nucleotides
            proximity_window = 5

            for _, row in gene_data.iterrows():
                # Check if mutation types match
                if row['mutation_type'] != mutation_type:
                    continue

                # Check if positions are close
                try:
                    row_position = int(row['position'])
                    distance = abs(row_position - position)

                    # Within proximity window?
                    if distance <= proximity_window:
                        matches.append(row.to_dict())

                except (ValueError, TypeError):
                    # Skip if position can't be converted to int
                    continue

        # STRATEGY 3: Type match only (if still no matches)
        if not matches and mutation_type:
            # Find any mutations of same type in this gene
            type_matches = gene_data[gene_data['mutation_type'] == mutation_type]

            # Take up to 3 examples
            if not type_matches.empty:
                matches.extend(type_matches.head(3).to_dict('records'))

        return matches

    def _calculate_match_quality(self, mutation, clinvar_record: Dict) -> float:
        """
        Calculate quality score for mutation-evidence match

        Args:
            mutation: Detected mutation
            clinvar_record: ClinVar database record

        Returns:
            Match quality score between 0.0 and 1.0
        """
        score = 0.0

        # Check position match
        mut_position = getattr(mutation, 'position', 0)
        clinvar_position = clinvar_record.get('position')

        if mut_position and clinvar_position:
            try:
                # Convert both to integers for comparison
                mut_pos_int = int(mut_position)
                clinvar_pos_int = int(clinvar_position)

                # Exact match?
                if mut_pos_int == clinvar_pos_int:
                    score += 0.5  # Highest position score
                else:
                    # Proximity score (closer = higher)
                    distance = abs(mut_pos_int - clinvar_pos_int)
                    if distance <= 10:
                        # Score decreases with distance
                        proximity_score = 0.3 * (1 - distance / 10)
                        score += proximity_score

            except (ValueError, TypeError):
                # Can't compare positions
                pass

        # Check mutation type match
        if getattr(mutation, 'type', '') == clinvar_record.get('mutation_type'):
            score += 0.3

        # Check protein change match (if available)
        mut_protein = getattr(mutation, 'protein_change', '')
        clinvar_protein = clinvar_record.get('protein_change')

        if mut_protein and clinvar_protein and mut_protein == clinvar_protein:
            score += 0.2  # Exact protein change match

        return score


def retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for evidence retrieval

    Args:
        state: Workflow state

    Returns:
        Modified state with evidence results
    """
    agent = RetrievalAgent()
    return agent.execute(state)
