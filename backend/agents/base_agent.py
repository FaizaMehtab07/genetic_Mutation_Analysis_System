"""
Base Agent class - Interface for all agents in the system

Each agent:
1. Receives current state
2. Performs its task
3. Updates state with results
4. Returns modified state
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class Agent(ABC):
    """
    Abstract base class for all agents in the pipeline

    Agents follow a simple interface:
    - Input: State (contains all accumulated results)
    - Process: Do the agent's work
    - Output: Modified state with results added

    This allows:
    - Easy composition into LangGraph
    - Clear contracts between agents
    - Testability
    - State management
    """

    def __init__(self, name: str):
        """
        Initialize agent

        Args:
            name: Agent name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"agents.{name}")

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this agent

        Args:
            state: Current workflow state (dict-like)

        Returns:
            Modified state with agent results added

        Example:
            >>> state = {
            ...     'sequence': 'ATGCGATAA',
            ...     'gene': 'TP53'
            ... }
            >>> agent = ValidationAgent()
            >>> result_state = agent.execute(state)
            >>> print(result_state['validation_result'])
        """
        pass

    def log_start(self):
        """Log agent start"""
        self.logger.info(f"{self.name} agent starting")

    def log_end(self):
        """Log agent completion"""
        self.logger.info(f"{self.name} agent completed")

    def log_error(self, error: str):
        """Log agent error"""
        self.logger.error(f"{self.name} agent error: {error}")


class ValidationAgent(Agent):
    """
    Validation Agent - Checks sequence validity

    Input State:
        - sequence: str (raw sequence)
        - gene: str (gene name)

    Output State (adds):
        - validation_result: ValidationOutput

    Errors:
        - Invalid nucleotides
        - Length out of range
        - Invalid gene
    """

    def __init__(self):
        super().__init__("Validation")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sequence"""
        self.log_start()

        try:
            # TODO: Implement in Phase 3
            # Import: from backend.agents.validation_agent import ValidationAgent as ValidationImpl
            # Call: result = ValidationImpl().validate(state['sequence'])

            self.log_end()
            return state

        except Exception as e:
            self.log_error(str(e))
            state['errors'].append(f"Validation failed: {str(e)}")
            return state


class AlignmentAgent(Agent):
    """
    Alignment Agent - Aligns sequences using Biopython

    Input State:
        - cleaned_sequence: str (from validation)
        - gene: str

    Output State (adds):
        - alignment_result: AlignmentOutput

    Dependency:
        - Biopython
        - Reference sequence file
    """

    def __init__(self):
        super().__init__("Alignment")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Align sequences"""
        self.log_start()

        try:
            # TODO: Implement in Phase 3
            self.log_end()
            return state

        except Exception as e:
            self.log_error(str(e))
            state['errors'].append(f"Alignment failed: {str(e)}")
            return state


class MutationDetectionAgent(Agent):
    """
    Mutation Detection Agent - Finds mutations

    Input State:
        - aligned_reference: str
        - aligned_query: str

    Output State (adds):
        - mutations: List[Mutation]
    """

    def __init__(self):
        super().__init__("MutationDetection")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect mutations"""
        self.log_start()

        try:
            # TODO: Implement in Phase 3
            self.log_end()
            return state

        except Exception as e:
            self.log_error(str(e))
            state['errors'].append(f"Mutation detection failed: {str(e)}")
            return state


class AnnotationAgent(Agent):
    """
    Annotation Agent - Translates DNA changes to protein effects

    Input State:
        - mutations: List[Mutation]
        - reference_sequence: str

    Output State (adds):
        - annotations: List[Annotation]

    Task:
        - Determine codon position
        - Translate codon
        - Identify effect (missense, nonsense, etc.)
    """

    def __init__(self):
        super().__init__("Annotation")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Annotate mutations"""
        self.log_start()

        try:
            # TODO: Implement in Phase 3
            self.log_end()
            return state

        except Exception as e:
            self.log_error(str(e))
            state['errors'].append(f"Annotation failed: {str(e)}")
            return state


class ClassificationAgent(Agent):
    """
    Classification Agent - Classifies mutation pathogenicity

    Input State:
        - annotations: List[Annotation]

    Output State (adds):
        - classification_result: ClassificationOutput

    Methods:
        - Rule-based classification
        - ML-based classification (optional)
        - Ensemble approach
    """

    def __init__(self):
        super().__init__("Classification")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify mutations"""
        self.log_start()

        try:
            # TODO: Implement in Phase 3
            self.log_end()
            return state

        except Exception as e:
            self.log_error(str(e))
            state['errors'].append(f"Classification failed: {str(e)}")
            return state


class RetrievalAgent(Agent):
    """
    Retrieval Agent - Finds clinical evidence from ClinVar

    Input State:
        - mutations: List[Mutation]
        - gene: str

    Output State (adds):
        - clinical_evidence: List[ClinVarRecord]

    Uses:
        - LlamaIndex for RAG
        - Vector similarity search
        - Ranking and filtering
    """

    def __init__(self):
        super().__init__("Retrieval")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve clinical evidence"""
        self.log_start()

        try:
            # TODO: Implement in Phase 4
            self.log_end()
            return state

        except Exception as e:
            self.log_error(str(e))
            state['errors'].append(f"Retrieval failed: {str(e)}")
            return state


__all__ = [
    'Agent',
    'ValidationAgent',
    'AlignmentAgent',
    'MutationDetectionAgent',
    'AnnotationAgent',
    'ClassificationAgent',
    'RetrievalAgent',
]