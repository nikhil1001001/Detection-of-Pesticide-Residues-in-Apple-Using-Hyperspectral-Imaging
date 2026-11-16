"""
Step 4 -- PROVISIONAL baseline models on raw_dn_spectra_PROVISIONAL_uncalibrated.csv.

Purpose: prove the classification/regression pipeline runs end-to-end.
NOT a trustworthy accuracy/R^2 result -- see CAVEAT below and PROJECT_NOTES.md.
Still raw DN, still uncalibrated. No hyperparameter tuning, one baseline
model per task.

Uses the EXISTING train/test split (5 train + 2 test per class, defined by
which pilot_data/<class>/{train,test}/ folder each sample came from) --
does not re-split.

run_baseline() is reusable so the same pipeline can be run on a different
feature-table CSV (e.g. step4c_sg_snv_baseline_comparison.py runs it again
on the SG+SNV-preprocessed table for comparison).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_squared_error,
    r2_score,
)

from step3_raw_dn_feature_table import PROJECT_ROOT, discover_pilot_samples

SCRATCH_STEP4_DIR = PROJECT_ROOT / "scratch" / "step4"

CLASS_TO_PPM = {"control": 0, "50ppm": 50, "100ppm": 100, "150ppm": 150}
CLASS_ORDER = ["control", "50ppm", "100ppm", "150ppm"]

CAVEAT = (
    "These metrics are expected to be inflated by the class/session date confound "
    "documented in PROJECT_NOTES.md -- each class was captured on a different single "
    "day, so the model may be learning acquisition-session differences rather than "
    "true pesticide signal. Do not interpret these numbers as real detection "
    "performance until calibration is resolved and/or a session-balanced dataset is "
    "available."
)


def run_baseline(csv_path, dataset_label: str, results_filename: str) -> dict:
    """
    Run the Step 4 baseline classification (Random Forest) + regression (PLSR)
    pipeline on the given feature-table CSV. Writes a results text file to
    scratch/step4/<results_filename> and returns a dict of headline metrics.
    """
    SCRATCH_STEP4_DIR.mkdir(parents=True, exist_ok=True)
    out_lines = []

    def log(line: str = "") -> None:
        print(line)
        out_lines.append(line)

    log(f"### {dataset_label} -- {csv_path.name} ###")

    df = pd.read_csv(csv_path)
    split_lookup = {s["sample_id"]: s["split"] for s in discover_pilot_samples()}
    df["split"] = df["sample_id"].map(split_lookup)
    assert df["split"].isna().sum() == 0, "some sample_ids in the CSV had no matching pilot_data file"
    assert len(df) == 28, f"expected 28 rows, got {len(df)}"

    band_cols = [c for c in df.columns if c.startswith("band_")]
    assert len(band_cols) == 228

    train_df = df[df["split"] == "train"].reset_index(drop=True)
    test_df = df[df["split"] == "test"].reset_index(drop=True)
    log(f"train samples: {len(train_df)}, test samples: {len(test_df)}")
    assert len(train_df) == 20 and len(test_df) == 8

    X_train, X_test = train_df[band_cols].values, test_df[band_cols].values
    y_class_train, y_class_test = train_df["class_label"].values, test_df["class_label"].values

    # ================= CLASSIFICATION =================
    log("\n" + "=" * 60)
    log(f"CLASSIFICATION -- Random Forest, predicting class_label from 228 bands ({dataset_label})")
    log("=" * 60)

    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_class_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_class_test, y_pred)
    log(f"\nTest accuracy: {acc:.3f}  ({int(round(acc * len(y_class_test)))}/{len(y_class_test)})")

    cm = confusion_matrix(y_class_test, y_pred, labels=CLASS_ORDER)
    cm_df = pd.DataFrame(cm, index=[f"true_{c}" for c in CLASS_ORDER], columns=[f"pred_{c}" for c in CLASS_ORDER])
    log("\nConfusion matrix (rows=true, cols=predicted):")
    log(cm_df.to_string())

    log("\nPer-class precision/recall/F1:")
    log(classification_report(y_class_test, y_pred, labels=CLASS_ORDER, zero_division=0))

    log("\nCAVEAT: " + CAVEAT)

    # ================= REGRESSION =================
    log("\n" + "=" * 60)
    log(f"REGRESSION -- PLSR, predicting nominal ppm from 228 bands ({dataset_label})")
    log("=" * 60)

    y_ppm_train = train_df["class_label"].map(CLASS_TO_PPM).values.astype(float)
    y_ppm_test = test_df["class_label"].map(CLASS_TO_PPM).values.astype(float)

    n_components = 5  # standard small default for PLSR on spectral data; not tuned
    reg = PLSRegression(n_components=n_components)
    reg.fit(X_train, y_ppm_train)
    y_ppm_pred = reg.predict(X_test).ravel()

    r2 = r2_score(y_ppm_test, y_ppm_pred)
    rmse = np.sqrt(mean_squared_error(y_ppm_test, y_ppm_pred))
    log(f"\nPLSR (n_components={n_components})")
    log(f"Test R^2:   {r2:.3f}")
    log(f"Test RMSE:  {rmse:.1f} ppm")

    log("\nPer-sample predictions (test set):")
    pred_df = pd.DataFrame(
        {
            "sample_id": test_df["sample_id"].values,
            "class_label": test_df["class_label"].values,
            "true_ppm": y_ppm_test,
            "predicted_ppm": np.round(y_ppm_pred, 1),
        }
    )
    log(pred_df.to_string(index=False))

    log("\nCAVEAT: " + CAVEAT)

    results_path = SCRATCH_STEP4_DIR / results_filename
    results_path.write_text("\n".join(out_lines), encoding="utf-8")
    log(f"\nsaved results to {results_path}")

    return {
        "dataset_label": dataset_label,
        "accuracy": acc,
        "r2": r2,
        "rmse": rmse,
    }


def main() -> None:
    csv_path = PROJECT_ROOT / "raw_dn_spectra_PROVISIONAL_uncalibrated.csv"
    run_baseline(csv_path, "raw DN (uncalibrated)", "step4_baseline_results.txt")


if __name__ == "__main__":
    main()
