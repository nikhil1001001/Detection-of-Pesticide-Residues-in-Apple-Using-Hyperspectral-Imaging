"""
Step 3a -- visual sanity check of the Otsu apple/background segmentation
on a few samples BEFORE running it across all 28 pilot samples.

Saves, per sanity sample, into scratch/step3/:
  <sample_id>_grayscale.png   -- mid-band grayscale (masked region only)
  <sample_id>_apple_mask.png  -- binary segmentation mask
  <sample_id>_overlay.png     -- mask overlay on grayscale for quick eyeballing
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from step3_raw_dn_feature_table import (
    PILOT_DATA_DIR,
    SCRATCH_STEP3_DIR,
    load_raw_dn_cube,
    mask_edge_artifact,
    segment_apple_pixels,
)

SANITY_SAMPLES = [
    ("control", "train", "Control_1"),
    ("100ppm", "train", "Clp_50_cont__1"),
    ("150ppm", "test", "Clp_150p_Cont_16"),
]

MID_BAND = 95  # same band used for the step2b grayscale diagnostics


def to_uint8(img: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(img, [1, 99])
    scaled = np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1)
    return (scaled * 255).astype(np.uint8)


def main() -> None:
    SCRATCH_STEP3_DIR.mkdir(parents=True, exist_ok=True)

    for class_name, split, sample_id in SANITY_SAMPLES:
        bil_path = PILOT_DATA_DIR / class_name / split / f"{sample_id}.bil"
        hdr_path = PILOT_DATA_DIR / class_name / split / f"{sample_id}.bil.hdr"

        cube = load_raw_dn_cube(bil_path, hdr_path)
        cube = mask_edge_artifact(cube)
        apple_mask = segment_apple_pixels(cube)

        gray = to_uint8(cube[:, :, MID_BAND])
        Image.fromarray(gray, mode="L").save(SCRATCH_STEP3_DIR / f"{sample_id}_grayscale.png")

        mask_img = (apple_mask.astype(np.uint8) * 255)
        Image.fromarray(mask_img, mode="L").save(SCRATCH_STEP3_DIR / f"{sample_id}_apple_mask.png")

        overlay = np.stack([gray, gray, gray], axis=-1).astype(np.uint8)
        overlay[apple_mask] = (
            0.5 * overlay[apple_mask] + 0.5 * np.array([255, 60, 60])
        ).astype(np.uint8)
        Image.fromarray(overlay, mode="RGB").save(SCRATCH_STEP3_DIR / f"{sample_id}_overlay.png")

        n_apple = int(apple_mask.sum())
        n_total = int(apple_mask.size)
        print(
            f"{class_name}/{split}/{sample_id}: "
            f"apple pixels = {n_apple} / {n_total} ({100 * n_apple / n_total:.1f}%)"
        )


if __name__ == "__main__":
    main()
