"""Prepare a filtered ClinVar dataset for the gene mutation detection project.

This script reads `variant_summary.txt` in streaming mode and writes a cleaned,
gene-filtered ClinVar CSV file for the backend retrieval and ML training pipeline.
"""

import csv
import re
from pathlib import Path
from typing import Optional

SUPPORTED_GENES = {
    "TP53",
    "BRCA1",
    "BRCA2",
    "EGFR",
    "APP",
    "PSEN1",
    "TCF7L2",
    "PPARG",
    "FTO",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_FILE = DATA_DIR / "variant_summary.txt"
OUTPUT_FILE = DATA_DIR / "clinvar_database.csv"

EFFECT_PATTERNS = [
    (r"fs|frameshift", "frameshift"),
    (r"ter|\*|stop codon|nonsense", "nonsense"),
    (r"delins", "inframe_deletion"),
    (r"ins(?![ert])", "inframe_insertion"),
    (r"del(?!ins)", "inframe_deletion"),
    (r"synonymous|silent", "synonymous"),
    (r"p\.[A-Za-z]\d+[A-Za-z]", "missense"),
]


def normalize_significance(raw: Optional[str]) -> str:
    if raw is None:
        return "Uncertain"

    value = str(raw).strip().lower()
    if any(x in value for x in ["pathogenic", "likely pathogenic"]) and not any(
        x in value for x in ["risk factor", "other", "drug response", "protective"]
    ):
        return "Pathogenic"
    if any(x in value for x in ["benign", "likely benign"]) and "risk factor" not in value:
        return "Benign"
    if any(x in value for x in ["uncertain", "conflicting", "not provided"]):
        return "Uncertain"
    if any(x in value for x in ["risk factor", "other", "drug response", "protective", "association"]):
        return "Potentially Pathogenic"
    return "Uncertain"


def parse_protein_change(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    match = re.search(r"\((p\.[^)]+)\)", str(name))
    return match.group(1) if match else None


def infer_effect(name: Optional[str], mutation_type: Optional[str]) -> str:
    raw = " ".join(filter(None, [str(name), str(mutation_type)])).lower()
    for pattern, effect in EFFECT_PATTERNS:
        if re.search(pattern, raw):
            return effect
    return "unknown"


def clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


def format_condition(phenotype_list: Optional[str]) -> str:
    if not phenotype_list:
        return ""
    return str(phenotype_list).replace("|", "; ").strip()


def select_position(row: dict) -> Optional[int]:
    for field in ["PositionVCF", "Start", "Stop"]:
        value = row.get(field)
        if not value or value.strip() in {"", "na", "-"}:
            continue
        try:
            position = int(float(value.strip()))
            if position > 0:
                return position
        except Exception:
            continue
    return None


def prepare_dataset() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Could not find {INPUT_FILE}")

    print(f"Streaming ClinVar variant summary from {INPUT_FILE}")
    with INPUT_FILE.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = [
            "variation_id",
            "allele_id",
            "gene",
            "hgnc_id",
            "clinical_significance",
            "review_status",
            "number_submitters",
            "origin",
            "assembly",
            "chromosome",
            "position",
            "mutation_type",
            "protein_change",
            "effect",
            "condition",
            "evidence_summary",
            "Name",
        ]

        with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output_handle:
            writer = csv.DictWriter(output_handle, fieldnames=fieldnames)
            writer.writeheader()

            total = 0
            written = 0

            for row in reader:
                total += 1
                gene = clean_text(row.get("GeneSymbol")).upper()
                if gene not in SUPPORTED_GENES:
                    continue

                variation_id = clean_text(row.get("VariationID") or row.get("AlleleID"))
                position = select_position(row)
                writer.writerow(
                    {
                        "variation_id": variation_id,
                        "allele_id": clean_text(row.get("AlleleID")),
                        "gene": gene,
                        "hgnc_id": clean_text(row.get("HGNC_ID")),
                        "clinical_significance": normalize_significance(row.get("ClinicalSignificance")),
                        "review_status": clean_text(row.get("ReviewStatus")),
                        "number_submitters": clean_text(row.get("NumberSubmitters")) or "0",
                        "origin": clean_text(row.get("OriginSimple")),
                        "assembly": clean_text(row.get("Assembly")),
                        "chromosome": clean_text(row.get("Chromosome")),
                        "position": position or "",
                        "mutation_type": clean_text(row.get("Type")),
                        "protein_change": parse_protein_change(row.get("Name")) or "",
                        "effect": infer_effect(row.get("Name"), row.get("Type")),
                        "condition": format_condition(row.get("PhenotypeList")),
                        "evidence_summary": format_condition(row.get("PhenotypeList")),
                        "Name": clean_text(row.get("Name")),
                    }
                )
                written += 1

                if total % 250000 == 0:
                    print(f"Processed {total:,} lines, wrote {written:,} ClinVar rows")

    print(f"Processed {total:,} lines from variant_summary.txt")
    print(f"Wrote {written:,} filtered ClinVar rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    prepare_dataset()
