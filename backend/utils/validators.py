"""
Custom validation functions
"""

from ..core.constants import SUPPORTED_GENES, MUTATION_EFFECTS

def validate_gene(gene: str) -> bool:
    """Check if gene is supported"""
    if not isinstance(gene, str) or not gene:
        return False
    return gene.upper() in SUPPORTED_GENES

def validate_sequence(sequence: str) -> bool:
    """Check if sequence contains only ATCG"""
    if not isinstance(sequence, str) or not sequence:
        return False
    valid_chars = set('ATCG')
    return all(c.upper() in valid_chars for c in sequence)

def validate_sequence_length(sequence: str, min_len: int = 10, max_len: int = 50000) -> bool:
    """Check if sequence length is valid"""
    if not isinstance(sequence, str):
        return False
    return min_len <= len(sequence) <= max_len
