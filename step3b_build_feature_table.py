"""
Step 3b -- build the PROVISIONAL raw-DN feature table across all 28 pilot
samples (4 classes x 5 train + 2 test), using the pipeline validated in
step3a_sanity_check_segmentation.py.

Outputs:
  raw_dn_spectra_PROVISIONAL_uncalibrated.csv   (project root)
  scratch/step3/raw_dn_mean_spectrum_per_class_PROVISIONAL.png
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from step3_raw_dn_feature_table import (
    CLASS_FOLDERS,
    PROJECT_ROOT,
    SCRATCH_STEP3_DIR,
    discover_pilot_samples,
    get_wavelengths,
    process_sample,
)

N_BANDS = 228


def main() -> None:
    SCRATCH_STEP3_DIR.mkdir(parents=True, exist_ok=True)
    samples = discover_pilot_samples()
    print(f"discovered {len(samples)} samples")

    wavelengths = get_wavelengths(samples[0]["hdr_path"])
    assert len(wavelengths) == N_BANDS

    rows = []
    for s in samples:
        result = process_sample(s["bil_path"], s["hdr_path"])
        pct_apple = 100 * result["n_apple_pixels"] / result["n_total_pixels"]
        print(
            f"  {s['class_label']:8s} {s['split']:5s} {s['sample_id']:20s} "
            f"apple px = {result['n_apple_pixels']:7d} ({pct_apple:4.1f}%)"
        )
        row = {"sample_id": s["sample_id"], "class_label": s["class_label"]}
        row.update({f"band_{i+1}": v for i, v in enumerate(result["spectrum"])})
        rows.append(row)

    table = pd.DataFrame(rows)
    band_cols = [f"band_{i+1}" for i in range(N_BANDS)]
    assert list(table.columns) == ["sample_id", "class_label"] + band_cols
    assert len(table) == 28, f"expected 28 samples, got {len(table)}"

    csv_path = PROJECT_ROOT / "raw_dn_spectra_PROVISIONAL_uncalibrated.csv"
    table.to_csv(csv_path, index=False)
    print(f"\nsaved feature table: {csv_path}  shape={table.shape}")

    # mean spectrum per class, raw DN, provisional/uncalibrated
    fig, ax = plt.subplots(figsize=(10, 6))
    for class_name in CLASS_FOLDERS:
        class_rows = table[table["class_label"] == class_name]
        mean_spectrum = class_rows[band_cols].mean(axis=0).values
        ax.plot(wavelengths, mean_spectrum, label=f"{class_name} (n={len(class_rows)})")

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Mean raw DN (uncalibrated)")
    ax.set_title("PROVISIONAL raw-DN mean spectrum per class (uncalibrated)")
    ax.legend()
    fig.tight_layout()
    plot_path = SCRATCH_STEP3_DIR / "raw_dn_mean_spectrum_per_class_PROVISIONAL.png"
    fig.savefig(plot_path, dpi=150)
    print(f"saved plot: {plot_path}")


if __name__ == "__main__":
    main()
