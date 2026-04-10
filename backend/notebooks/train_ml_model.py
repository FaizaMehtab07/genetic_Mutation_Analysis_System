"""Train an ML classifier for mutation pathogenicity using ClinVar data."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
INPUT_FILE = DATA_DIR / "clinvar_database.csv"
MODEL_PATH = MODELS_DIR / "random_forest_model.pkl"
SCALER_PATH = MODELS_DIR / "feature_scaler.pkl"
ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"

SUPPORTED_GENES = [
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

EFFECT_CATEGORIES = [
    "frameshift",
    "nonsense",
    "missense",
    "inframe_insertion",
    "inframe_deletion",
    "synonymous",
    "unknown",
]

CLASS_LABELS = ["Pathogenic", "Potentially Pathogenic", "Uncertain", "Benign"]


def load_dataset() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"ClinVar dataset not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, dtype=str)
    df = df[df["gene"].isin(SUPPORTED_GENES)].copy()
    df = df[df["clinical_significance"].isin(CLASS_LABELS)]
    df["position"] = pd.to_numeric(df["position"], errors="coerce")
    df = df[df["position"].notna()]
    df["position_norm"] = np.minimum(df["position"] / 1_000_000.0, 1.0)
    df["has_protein_change"] = df["protein_change"].notna().astype(int)

    if "number_submitters" in df.columns:
        df["number_submitters"] = pd.to_numeric(df["number_submitters"], errors="coerce").fillna(0).astype(int)
    else:
        df["number_submitters"] = 0

    if "effect" in df.columns:
        df["effect"] = df["effect"].fillna("unknown").astype(str).str.lower()
        df.loc[~df["effect"].isin(EFFECT_CATEGORIES), "effect"] = "unknown"
    else:
        df["effect"] = "unknown"

    return df


def build_features(df: pd.DataFrame) -> (np.ndarray, np.ndarray, list):
    gene_ohe = pd.get_dummies(df["gene"], prefix="gene")
    gene_ohe = gene_ohe.reindex(columns=[f"gene_{gene}" for gene in SUPPORTED_GENES], fill_value=0)

    effect_ohe = pd.get_dummies(df["effect"], prefix="effect")
    effect_ohe = effect_ohe.reindex(columns=[f"effect_{effect}" for effect in EFFECT_CATEGORIES], fill_value=0)

    feature_df = pd.concat(
        [
            gene_ohe,
            effect_ohe,
            df[["position_norm", "has_protein_change", "number_submitters"]],
        ],
        axis=1,
    )

    return feature_df.values, df["clinical_significance"].values, feature_df.columns.tolist()


def train() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    df = load_dataset()
    X, y, feature_names = build_features(df)

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train_scaled, y_train)

    predictions = clf.predict(X_test_scaled)
    report = classification_report(y_test, predictions, target_names=label_encoder.classes_)

    print("Training complete")
    print("Feature columns:", feature_names)
    print("Label classes:", label_encoder.classes_)
    print(report)

    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(label_encoder, ENCODER_PATH)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved scaler to {SCALER_PATH}")
    print(f"Saved label encoder to {ENCODER_PATH}")


if __name__ == "__main__":
    train()
