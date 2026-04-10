"""
Pytest configuration and fixtures
"""

import pytest # pyright: ignore[reportMissingImports]
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

@pytest.fixture
def sample_sequence():
    """Sample DNA sequence for testing"""
    return "ATGCGATAA" * 100

@pytest.fixture
def valid_gene():
    """Valid gene name for testing"""
    return "TP53"
