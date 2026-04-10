"""
Application constants - With type hints for clarity
"""

from typing import Set, Dict, Any

# Supported genes
SUPPORTED_GENES: Set[str] = {
    'TP53', 'BRCA1', 'BRCA2', 'EGFR',
    'APP', 'PSEN1', 'TCF7L2', 'PPARG', 'FTO'
}

# Gene metadata
GENE_INFO: Dict[str, Dict[str, str]] = {
    'TP53': {
        'full_name': 'Tumor Protein P53',
        'category': 'Cancer',
        'chromosome': '17',
        'description': 'Tumor suppressor, guardian of the genome'
    },
    'BRCA1': {
        'full_name': 'Breast Cancer 1',
        'category': 'Cancer',
        'chromosome': '17',
        'description': 'DNA repair protein, hereditary breast cancer'
    },
    'BRCA2': {
        'full_name': 'Breast Cancer 2',
        'category': 'Cancer',
        'chromosome': '13',
        'description': 'DNA repair protein, hereditary breast/ovarian cancer'
    },
    'EGFR': {
        'full_name': 'Epidermal Growth Factor Receptor',
        'category': 'Cancer',
        'chromosome': '7',
        'description': 'Tyrosine kinase, driver mutations in lung cancer'
    },
    'APP': {
        'full_name': 'Amyloid Beta Precursor Protein',
        'category': 'Neurological',
        'chromosome': '21',
        'description': 'Alzheimer\'s disease related protein'
    },
    'PSEN1': {
        'full_name': 'Presenilin 1',
        'category': 'Neurological',
        'chromosome': '14',
        'description': 'Early-onset Alzheimer\'s disease'
    },
    'TCF7L2': {
        'full_name': 'Transcription Factor 7 Like 2',
        'category': 'Metabolic',
        'chromosome': '10',
        'description': 'Type 2 diabetes susceptibility'
    },
    'PPARG': {
        'full_name': 'Peroxisome Proliferator-Activated Receptor Gamma',
        'category': 'Metabolic',
        'chromosome': '3',
        'description': 'Insulin sensitivity, metabolic disease'
    },
    'FTO': {
        'full_name': 'Fat Mass and Obesity Associated',
        'category': 'Metabolic',
        'chromosome': '16',
        'description': 'Obesity risk loci'
    },
}

# Valid mutation types
MUTATION_TYPES: Set[str] = {'substitution', 'insertion', 'deletion'}

# Valid mutation effects
MUTATION_EFFECTS: Set[str] = {
    'frameshift', 'missense', 'nonsense',
    'synonymous', 'inframe_insertion', 'inframe_deletion'
}

# Clinical classifications
CLASSIFICATIONS: Set[str] = {'Pathogenic', 'Potentially Pathogenic', 'Uncertain', 'Benign'}

# Risk levels
RISK_LEVELS: Set[str] = {'HIGH', 'MODERATE', 'LOW'}

# Nucleotide codes
NUCLEOTIDES: Set[str] = {'A', 'T', 'C', 'G'}

# Amino acid codes
AMINO_ACIDS: Set[str] = {'A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
                         'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y', '*'}

__all__ = [
    'SUPPORTED_GENES',
    'GENE_INFO',
    'MUTATION_TYPES',
    'MUTATION_EFFECTS',
    'CLASSIFICATIONS',
    'RISK_LEVELS',
    'NUCLEOTIDES',
    'AMINO_ACIDS',
]