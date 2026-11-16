"""
Step 3 (PROVISIONAL, UNCALIBRATED) -- raw-DN feature table for the pilot dataset.

Everything here operates on raw sensor counts (raw_dn), NOT reflectance.
No radiometric/reflectance calibration has been applied or confirmed yet.
Do not rename raw_dn outputs to "reflectance" until calibration is verified.

Pipeline (see module docstring of each function for the swap point):
    1. load_raw_dn_cube()      -- raw-DN cube loader. THIS is the only piece
                                   that gets replaced once calibration is
                                   confirmed (swap for a reflectance loader
                                   that returns a calibrated cube of the same
                                   shape/dtype contract).
    2. mask_edge_artifact()    -- drops the known fixed artifact (x >= 1290).
    3. segment_apple_pixels()  -- Otsu threshold on per-pixel mean intensity,
                                   apple vs. near-black background. Cube-format
                                   agnostic: works the same on raw DN or on
                                   calibrated reflectance later.
    4. extract_mean_spectrum() -- mean spectrum over the segmented pixels.
    5. build_feature_table()   -- assembles the sample_id/class_label/band_*
                                   table across all pilot samples.

Steps 2-5 are intended to stay unchanged after calibration lands; only
load_raw_dn_cube() (step 1) should need replacing.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from spectral.io import envi

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
PILOT_DATA_DIR = PROJECT_ROOT / "pilot_data"
SCRATCH_STEP3_DIR = PROJECT_ROOT / "scratch" / "step3"

CLASS_FOLDERS = ["control", "50ppm", "100ppm", "150ppm"]
EDGE_ARTIFACT_X_MAX = 1290  # exclude columns x >= 1290 (fixed sensor artifact + safety margin)


def discover_pilot_samples() -> list[dict]:
    """Walk pilot_data/<class>/{train,test}/*.bil and return sample records."""
    samples = []
    for class_name in CLASS_FOLDERS:
        class_dir = PILOT_DATA_DIR / class_name
        for split in ("train", "test"):
            split_dir = class_dir / split
            if not split_dir.is_dir():
                continue
            for bil_path in sorted(split_dir.glob("*.bil")):
                hdr_path = bil_path.with_suffix(".bil.hdr")
                if not hdr_path.exists():
                    hdr_path = pathlib.Path(str(bil_path) + ".hdr")
                samples.append(
                    {
                        "sample_id": bil_path.stem,
                        "class_label": class_name,
                        "split": split,
                        "bil_path": bil_path,
                        "hdr_path": hdr_path,
                    }
                )
    return samples


def load_raw_dn_cube(bil_path: pathlib.Path, hdr_path: pathlib.Path) -> np.ndarray:
    """
    PROVISIONAL raw-DN loader -- swap point for future reflectance calibration.

    Returns raw sensor counts as float32, shape (lines, samples, bands).
    No radiometric correction, dark/white referencing, or scaling is applied
    here -- these are the untouched raw digital numbers straight off the
    sensor. A future calibrated loader must return the same shape/dtype
    contract (lines, samples, bands) float array so nothing downstream needs
    to change.
    """
    img = envi.open(str(hdr_path), str(bil_path))
    # scale=False is required: spectral silently divides by the header's
    # "reflectance scale factor" (10000 here) on load unless told not to.
    # We want the untouched raw digital numbers, not that pre-scaled value.
    cube = img.load(scale=False)  # (lines, samples, bands)
    return np.asarray(cube, dtype=np.float32)


def mask_edge_artifact(cube: np.ndarray, x_max: int = EDGE_ARTIFACT_X_MAX) -> np.ndarray:
    """Drop columns x >= x_max (known fixed sensor artifact). cube: (lines, samples, bands)."""
    return cube[:, :x_max, :]


def otsu_threshold(values: np.ndarray, n_bins: int = 256) -> float:
    """Minimal Otsu's-method threshold on a 1D array of values."""
    hist, bin_edges = np.histogram(values, bins=n_bins)
    hist = hist.astype(np.float64)
    bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    weight1 = np.cumsum(hist)
    weight2 = np.cumsum(hist[::-1])[::-1]

    # avoid div-by-zero on empty cumulative bins
    with np.errstate(invalid="ignore", divide="ignore"):
        mean1 = np.cumsum(hist * bin_mids) / weight1
        mean2 = (np.cumsum((hist * bin_mids)[::-1])[::-1]) / weight2
        inter_class_variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2

    idx = int(np.nanargmax(inter_class_variance))
    return float(bin_mids[idx])


def segment_apple_pixels(cube: np.ndarray) -> np.ndarray:
    """
    Two-stage Otsu threshold on per-pixel mean intensity across bands.

    Sanity-check on real samples (scratch/step3) showed the frame of the
    imaging chamber is visible as a bright vertical band on both edges of
    the field of view (well inside x < 1290, so it is NOT the artifact
    excluded by mask_edge_artifact) and is much brighter than anything
    inside the chamber. Inside the chamber, the apple is actually the
    *darker* region relative to the (lighter, near-uniform) chamber wall
    background -- so a single global Otsu split just separates
    frame-vs-chamber, not apple-vs-background.

    Stage 1: global Otsu on the whole frame separates the bright outer
             frame from the chamber interior (keep interior = "<= thr1").
    Stage 2: Otsu restricted to the chamber interior separates the
             brighter wall background from the darker apple pixels
             (apple = "< thr2").

    cube: (lines, samples, bands) -- works the same regardless of whether
    the cube holds raw DN or (later) calibrated reflectance.
    Returns a boolean mask of shape (lines, samples), True = apple pixel.
    """
    mean_intensity = cube.mean(axis=2)  # (lines, samples)

    threshold1 = otsu_threshold(mean_intensity.ravel())
    chamber_interior = mean_intensity <= threshold1

    threshold2 = otsu_threshold(mean_intensity[chamber_interior])
    apple_mask = chamber_interior & (mean_intensity < threshold2)
    return apple_mask


def extract_mean_spectrum(cube: np.ndarray, apple_mask: np.ndarray) -> np.ndarray:
    """Mean raw-DN spectrum over the segmented apple pixels. Returns (bands,)."""
    pixels = cube[apple_mask]  # (n_apple_pixels, bands)
    return pixels.mean(axis=0)


def process_sample(bil_path: pathlib.Path, hdr_path: pathlib.Path) -> dict:
    """Full per-sample pipeline: load -> mask artifact -> segment -> mean spectrum."""
    cube = load_raw_dn_cube(bil_path, hdr_path)
    cube = mask_edge_artifact(cube)
    apple_mask = segment_apple_pixels(cube)
    spectrum = extract_mean_spectrum(cube, apple_mask)
    return {
        "cube": cube,
        "apple_mask": apple_mask,
        "spectrum": spectrum,
        "n_apple_pixels": int(apple_mask.sum()),
        "n_total_pixels": int(apple_mask.size),
    }


def get_wavelengths(hdr_path: pathlib.Path) -> np.ndarray:
    img = envi.open(str(hdr_path))
    return np.array([float(w) for w in img.bands.centers])


def savgol_smooth(spectrum: np.ndarray, window_length: int = 15, polyorder: int = 2) -> np.ndarray:
    """
    Savitzky-Golay smoothing on a single sample's mean spectrum (228 bands).

    window_length=15, polyorder=2 are reasonable starting defaults for a
    228-band spectrum (window covers ~6.6% of the band range) -- not tuned,
    could be revisited later once calibration is settled.
    """
    return savgol_filter(spectrum, window_length=window_length, polyorder=polyorder)


def snv_transform(spectrum: np.ndarray) -> np.ndarray:
    """Standard Normal Variate: per-spectrum mean-center + scale to unit std."""
    return (spectrum - spectrum.mean()) / spectrum.std()
