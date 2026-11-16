"""
Step 3d/4 comparison -- re-run the Step 4 baseline models on the new
SG+SNV-preprocessed feature table and report side by side with the
original raw-DN baseline. Same train/test split, same model types
(Random Forest / PLSR), no tuning, for both.
"""
from __future__ import annotations

from step3_raw_dn_feature_table import PROJECT_ROOT
from step4_baseline_models import CAVEAT, run_baseline


def main() -> None:
    raw_metrics = run_baseline(
        PROJECT_ROOT / "raw_dn_spectra_PROVISIONAL_uncalibrated.csv",
        "raw DN (uncalibrated)",
        "step4_baseline_results.txt",
    )
    print("\n\n")
    sgsnv_metrics = run_baseline(
        PROJECT_ROOT / "raw_dn_spectra_PROVISIONAL_SG_SNV.csv",
        "SG-smoothed + SNV (uncalibrated)",
        "step4_sg_snv_baseline_results.txt",
    )

    print("\n\n" + "=" * 60)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 60)
    header = f"{'metric':<12}{'raw DN':>15}{'SG+SNV':>15}"
    print(header)
    print(f"{'accuracy':<12}{raw_metrics['accuracy']:>15.3f}{sgsnv_metrics['accuracy']:>15.3f}")
    print(f"{'R^2':<12}{raw_metrics['r2']:>15.3f}{sgsnv_metrics['r2']:>15.3f}")
    print(f"{'RMSE (ppm)':<12}{raw_metrics['rmse']:>15.1f}{sgsnv_metrics['rmse']:>15.1f}")
    print("\nCAVEAT (applies to both columns): " + CAVEAT)


if __name__ == "__main__":
    main()
