"""
Step 3d -- Savitzky-Golay smoothing + SNV preprocessing, applied on top of
the already-corrected raw-DN feature table from Step 3c.

Still raw DN, still uncalibrated -- this is a spectral preprocessing step,
independent of the reflectance-calibration question.

Order: smooth first (savgol_smooth), then SNV (snv_transform), applied to
each sample's mean raw-DN spectrum (228 bands) independently.

Output: raw_dn_spectra_PROVISIONAL_SG_SNV.csv (new file -- does NOT
overwrite raw_dn_spectra_PROVISIONAL_uncalibrated.csv; both are kept).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from step3_raw_dn_feature_table import (
    CLASS_FOLDERS,
    PROJECT_ROOT,
    SCRATCH_STEP3_DIR,
    discover_pilot_samples,
    get_wavelengths,
    savgol_smooth,
    snv_transform,
)


def main() -> None:
    src_csv = PROJECT_ROOT / "raw_dn_spectra_PROVISIONAL_uncalibrated.csv"
    df = pd.read_csv(src_csv)
    band_cols = [c for c in df.columns if c.startswith("band_")]
    assert len(band_cols) == 228
    assert len(df) == 28

    processed = df.copy()
    for i, row in df.iterrows():
        spectrum = row[band_cols].to_numpy(dtype=float)
        smoothed = savgol_smooth(spectrum)
        transformed = snv_transform(smoothed)
        processed.loc[i, band_cols] = transformed

    out_csv = PROJECT_ROOT / "raw_dn_spectra_PROVISIONAL_SG_SNV.csv"
    processed.to_csv(out_csv, index=False)
    print(f"saved {out_csv}  shape={processed.shape}")

    samples = discover_pilot_samples()
    wavelengths = get_wavelengths(samples[0]["hdr_path"])

    fig, ax = plt.subplots(figsize=(10, 6))
    for class_name in CLASS_FOLDERS:
        rows = processed[processed["class_label"] == class_name]
        mean_spectrum = rows[band_cols].mean(axis=0).to_numpy(dtype=float)
        ax.plot(wavelengths, mean_spectrum, label=f"{class_name} (n={len(rows)})")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("SNV-transformed raw DN (after Savitzky-Golay smoothing)")
    ax.set_title("PROVISIONAL SG+SNV-preprocessed mean spectrum per class (still uncalibrated)")
    ax.legend()
    fig.tight_layout()
    plot_path = SCRATCH_STEP3_DIR / "raw_dn_mean_spectrum_per_class_PROVISIONAL_SG_SNV.png"
    fig.savefig(plot_path, dpi=150)
    print(f"saved {plot_path}")


if __name__ == "__main__":
    main()
