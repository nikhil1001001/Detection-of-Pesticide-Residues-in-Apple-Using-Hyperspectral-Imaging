# MTP Hyperspectral Apple Project — Notes

This file is the source of truth for project status and open questions.
Keep it updated as decisions are made — don't rely on chat history.

Last updated: 2026-09-02

---

## Status summary (plain language)

**Done:**
- Pilot subset assembled: `pilot_data\` — 4 classes (control, 50ppm, 100ppm, 150ppm) x
  (5 train + 2 test) = 28 samples, `.bil` + `.bil.hdr` pairs, all verified present.
- `venv\` set up with numpy, matplotlib, pillow, spectral, and (as of 2026-09-01)
  pandas 2.3.3 and scikit-learn 1.7.2.
- Step 2b: grayscale band + saturation-mask diagnostic images for control/50ppm/150ppm.
  **100ppm was never run through Step 2b** — no grayscale/satmask images exist for it.
  Saturation-vs-wavelength plot exists only for `control1`, not for the other 3 classes.
  (Decision: not blocking further work on finishing this — see Sudhir's session note below.)
- Step 3 (PROVISIONAL, uncalibrated): built a raw-DN feature table across all 28 pilot
  samples. Pipeline: mask out columns x >= 1290 (known fixed artifact) -> two-stage Otsu
  segmentation (removes bright equipment-frame edges, then splits apple vs. background
  wall within the chamber) -> mean raw-DN spectrum over segmented apple pixels (228 bands).
  Output: `raw_dn_spectra_PROVISIONAL_uncalibrated.csv` (28 rows x 230 cols) in project root,
  plus `scratch\step3\raw_dn_mean_spectrum_per_class_PROVISIONAL.png`.
- Step 3c (2026-09-01): investigated and fixed a corrupted pilot file, and confirmed the
  class-vs-acquisition-date confound spans the *entire* source dataset, not just the pilot
  subset. Details below under "Session log".
- Step 4 (PROVISIONAL, 2026-09-01): baseline classification (Random Forest) and regression
  (PLSR) models trained on the raw-DN feature table, using the existing 20 train / 8 test
  split. Purpose was only to prove the pipeline runs end-to-end — **not** a trustworthy
  result, given the class/session confound. See "Session log" for metrics + caveat.
- Step 3d (PROVISIONAL, 2026-09-02): added Savitzky-Golay smoothing + SNV preprocessing,
  built a second feature table (`raw_dn_spectra_PROVISIONAL_SG_SNV.csv`), and re-ran the
  Step 4 baselines on it for comparison. Still raw DN under the hood, still uncalibrated.
  See "Session log" for the comparison.

**Not started:**
- Reflectance/radiometric calibration (raw DN only so far, everywhere).
- Any hyperparameter tuning or model comparison (only one untuned baseline per task so far).
- Step 2b for the 100ppm class specifically.
- Locating/regenerating the 3 missing `.hdr` files in `Clp_cont_100ppm` (source positions
  98/99/100 — see 2026-09-02 session log entry). Doesn't block the pilot, blocks scaling
  the 100ppm class beyond it.

**Most logical next step (not yet started):** get Sudhir's input on the open questions
below — several of them (calibration reference, ppm/filename mismatch) directly affect
whether the Step 3 raw-DN table is even measuring what we think it's measuring.

---

## Open questions for Sudhir

These were not previously written down anywhere in the project folder — this is the
first time they're captured in a file rather than living only in conversation.

1. **Reference tile identity** — what white/gray reference standard (if any) was scanned
   alongside each session, and where is that data? The `.hdr` files carry a
   `reflectance scale factor = 10000` field, implying *some* calibration convention was
   intended, but no calibration/reference captures have been located in the project
   folder or identified yet. Needed before any raw-DN -> reflectance conversion.

2. **Saturation** — how much of the sensor's dynamic range is saturating (clipping at
   65535, the uint16 max) in these captures, and does it matter for the analysis?
   Step 2b's saturation-mask images exist for control/50ppm/150ppm only (not 100ppm,
   not systematically summarized yet).

3. **ppm-vs-filename mismatch** — confirmed directly from the pilot filenames (2026-09-01):
   - `50ppm` folder (`Clp_cont_50ppm` at source) contains files named `Clp_25_cont_*` — filename says 25, folder says 50.
   - `100ppm` folder (`Clp_cont_100ppm` at source) contains files named `Clp_50_cont__*` — filename says 50, folder says 100.
   - `150ppm` folder contains files named `Clp_150p_*` — filename matches folder (150).
   - `control` folder contains files named `Control_*` — no number, consistent.

   So `50ppm` and `100ppm` show a **filename = folder/2** pattern, while `150ppm` and
   `control` are self-consistent. Need Sudhir to confirm which is ground truth (folder
   name or the number embedded in the filename) before trusting the `class_label` column
   in the feature table for those two classes.

---

## Session log

### 2026-09-01 — Step 3c: corrupted-file investigation + date-confound check

**Corrupted file investigation.** `pilot_data\100ppm\train\Clp_50_cont__4.bil` was
flagged in Step 3 as an outlier: mean raw DN over segmented apple pixels was 514.7 vs.
4770-5315 for its 6 siblings, and its overlay mask showed only a broken ring instead of
a filled apple.

Checked the ORIGINAL source file at `D:\Chandan__bil\Clp_cont_100ppm\Clp_50_cont__4.bil`
(direct byte-level read, same pipeline as the pilot copy):
- Source file, same pipeline: 21.0% apple pixels, mean raw DN over apple pixels = 5013.0
  — square in the sibling range (4770-5315), overlay mask visually clean and normal.
- **Conclusion: the corruption is in the pilot_data copy, not the source.** Root cause of
  the copy-level corruption was not investigated further (file sizes matched exactly at
  583,680,000 bytes on both copies, so it wasn't a truncation — could be a bit-level
  copy error; not pursued since re-copying resolved it).

**Fix applied:** re-copied `Clp_50_cont__4.bil` and `.bil.hdr` fresh from source into
`pilot_data\100ppm\train\`, overwriting the corrupted copy. Verified via MD5 checksum
that the new pilot copy is byte-identical to the source file. Re-ran the Step 3 pipeline
on just this sample and updated its row in `raw_dn_spectra_PROVISIONAL_uncalibrated.csv`
(now 21.0% apple pixels, mean raw DN ~5013 — consistent with siblings). Regenerated
`scratch\step3\raw_dn_mean_spectrum_per_class_PROVISIONAL.png` with the corrected data.
100ppm class std (of per-sample mean raw DN) dropped from 1719 to 191 after the fix,
now in line with the other 3 classes (169-394).

**Caveat:** this incident means at least one file was silently corrupted during copying
into `pilot_data\`. The other 27 pilot files have not been independently re-verified
against source (only spot-checked via plausibility of their extracted spectra). Worth
keeping in mind if another sample ever looks anomalous.

**Date-confound check (full source folders, not just the pilot subset).** Checked
min/max file modification dates across ALL files in each of the 4 relevant source
folders under `D:\Chandan__bil\` (200 files each):

| Class | Source folder | Files | Earliest | Latest | Span |
|---|---|---|---|---|---|
| control | `Appl_samp_control` | 200 | 2025-11-12 14:50 | 2025-11-12 18:01 | same day, ~3h11m |
| 50ppm | `Clp_cont_50ppm` | 200 | 2025-12-22 15:34 | 2025-12-22 17:40 | same day, ~2h6m |
| 100ppm | `Clp_cont_100ppm` | 200 | 2025-12-26 14:40 | 2025-12-26 16:51 | same day, ~2h11m |
| 150ppm | `Clp_cont_150ppm` | 200 | 2026-01-13 14:45 | 2026-01-13 16:20 | same day, ~1h35m |

**Finding: every class was captured entirely within a single day/session, across the
FULL dataset (not just our 28-sample pilot).** Class label and acquisition date/session
are perfectly confounded across all 800 source files — there is no within-class,
cross-date variation anywhere in the dataset to help separate "ppm dose effect" from
"which day/session this was scanned" effect. This makes the reference-tile question
(open question #1 above) more important, not less: without a per-session calibration
reference, any class-level differences in raw DN (or later, reflectance) are equally
explainable by session-to-session instrument/lighting drift as by the actual treatment.

**Also noted while browsing the source drive:** `D:\Chandan__bil\` contains additional
folders not part of this pilot project — a second, larger `Control` folder (400 files,
different naming convention `cont__01.bil` etc., not used here), plus `Mxd_m+c__*` and
`Mz_cont_*` folders that appear to belong to a different experiment. Flagging only for
awareness; not investigated further.

### 2026-09-01 — Step 4: PROVISIONAL baseline models (classification + regression)

Ran on `raw_dn_spectra_PROVISIONAL_uncalibrated.csv` (28 rows, corrupted row already
fixed as of Step 3c). Used the existing train/test split recovered from the
`pilot_data\<class>\{train,test}\` folder structure — 20 train / 8 test, not re-split.
One untuned baseline model per task, no hyperparameter search. Purpose was solely to
prove the classification/regression pipeline runs end-to-end, not to produce a
trustworthy result.

**Classification** — Random Forest (`n_estimators=200`), predicting `class_label` from
all 228 raw-DN bands:
- Test accuracy: 0.875 (7/8)
- Confusion matrix (rows=true, cols=pred): control 2/0/0/0; 50ppm 1/1/0/0 (one 50ppm
  test sample misclassified as control); 100ppm 0/0/2/0; 150ppm 0/0/0/2
- Per-class precision/recall: control 0.67/1.00, 50ppm 1.00/0.50, 100ppm 1.00/1.00,
  150ppm 1.00/1.00

**Regression** — PLSR (`n_components=5`, not tuned), mapping `class_label` to nominal
ppm (0/50/100/150) and predicting from all 228 raw-DN bands:
- Test R²: 0.874
- Test RMSE: 19.8 ppm
- Predictions were directionally correct but with sizeable per-sample error (e.g. one
  control test sample predicted at 35.6 ppm, one 100ppm sample at 76.6 ppm).

**Caveat (applies to both results above):** These metrics are expected to be inflated
by the class/session date confound documented above — each class was captured on a
different single day, so the model may be learning acquisition-session differences
rather than true pesticide signal. Do not interpret these numbers as real detection
performance until calibration is resolved and/or a session-balanced dataset is
available.

Full console output saved to `scratch\step4\step4_baseline_results.txt`.

### 2026-09-02 — Step 3d: Savitzky-Golay + SNV preprocessing, and re-run of Step 4 baselines

Added two preprocessing functions to `step3_raw_dn_feature_table.py`:
- `savgol_smooth(spectrum, window_length=15, polyorder=2)` — scipy Savitzky-Golay
  smoothing; window/polyorder are reasonable starting defaults for a 228-band
  spectrum, not tuned.
- `snv_transform(spectrum)` — Standard Normal Variate: `(spectrum - mean) / std`.

Rebuilt the feature table (`step3d_sg_snv_preprocessing.py`), applying smoothing
first then SNV to each of the 28 samples' mean raw-DN spectra (using the
already-corrected data from Step 3c). Saved as a **new** file,
`raw_dn_spectra_PROVISIONAL_SG_SNV.csv` — the original
`raw_dn_spectra_PROVISIONAL_uncalibrated.csv` was NOT overwritten, both are kept.

**Visual comparison** (`scratch\step3\raw_dn_mean_spectrum_per_class_PROVISIONAL_SG_SNV.png`
vs. the original class-mean plot): SNV removed most of the raw amplitude offset
between classes — the 4 curves now overlap almost perfectly in the flat regions
(~400-600nm and ~700-750nm), where before SNV there was a clear amplitude
ordering (control brightest, then 50ppm, then 100ppm/150ppm). What's left after
SNV is real shape differences: a shoulder around 640-680nm where 50ppm/100ppm sit
higher than control/150ppm, and a trough near 950-1000nm where 50ppm sits
noticeably lower than the other 3 classes. Whether these shape differences are a
real spectral signature or still an artifact of the class/session confound is
unresolved — SNV normalizes amplitude, it does not fix the confound.

**Step 4 baseline re-run on the SG+SNV table** (`step4c_sg_snv_baseline_comparison.py`),
same 20/8 split, same untuned Random Forest / PLSR baselines:

| metric | raw DN | SG+SNV |
|---|---|---|
| Classification accuracy | 0.875 (7/8) | 0.875 (7/8) |
| Regression R² | 0.874 | 0.848 |
| Regression RMSE | 19.8 ppm | 21.8 ppm |

Classification accuracy was identical, but which sample was misclassified changed:
raw DN misclassified one 50ppm sample as control; SG+SNV instead misclassified one
control sample as 150ppm. Regression got slightly worse on SG+SNV (both R² down and
RMSE up), though still in a similar range. Preprocessing did not meaningfully change
the headline numbers either direction.

**Caveat (applies to both raw-DN and SG+SNV results above, unchanged from Step 4):**
These metrics are expected to be inflated by the class/session date confound
documented above — each class was captured on a different single day, so the model
may be learning acquisition-session differences rather than true pesticide signal.
Do not interpret these numbers as real detection performance until calibration is
resolved and/or a session-balanced dataset is available. SG+SNV preprocessing does
not address this confound — it only normalizes per-sample amplitude/baseline, not
session-to-session systematic differences.

Full console output saved to `scratch\step4\step4_baseline_results.txt` (raw DN,
re-verified identical to the 2026-09-01 run) and `scratch\step4\step4_sg_snv_baseline_results.txt` (SG+SNV).

### 2026-09-02 — Interview-prep audit: missing .hdr files found in Clp_cont_100ppm

While re-reading every project file from scratch to write an interview-prep
document (documentation only, no pipeline changes), found a file-pairing gap in
the source data that hadn't been logged anywhere: `D:\Chandan__bil\Clp_cont_100ppm\`
has 100 `.bil` files but only 97 `.hdr` files. The 3 missing headers are for
`Clp_50_cont__98.bil`, `Clp_50_cont__99.bil`, and `Clp_50_cont__100.bil` — none
have a matching `.bil.hdr`, so none of the three can currently be loaded by
`load_raw_dn_cube()` (the `spectral` library needs the header for cube
dimensions/dtype).

**Impact on the current pilot: none.** The 28-sample pilot draws from positions
1, 4, 7, 10, 13 (train) and 16, 19 (test) per class — none of the missing
positions (98/99/100) are in it. **Action needed before scaling the 100ppm class
up**: locate or regenerate headers for these 3 source files, or exclude them,
before they'd be pulled into any larger run past the pilot.

**Process note — why this wasn't caught earlier:** the IoU-style spatial overlap
metric referenced when discussing the Step 2b saturation masks (control/50ppm/
150ppm) turned out not to exist anywhere as a saved number — only the PNG masks
themselves, no computed value ever written to a file. Same root cause here: easy
to lose a number that only ever lived in console output or memory. **Going
forward, every computed metric (counts, percentages, thresholds, IoU/overlap
values, anything derived from data) should be saved to a results file
(`scratch\stepN\...`) at the time it's computed, not just printed to console or
left implicit in a plot** — so a later audit like this one doesn't have to
re-derive or guess at numbers that were already calculated once.

---

## File/output locations

- `pilot_data\` — pilot subset (28 `.bil`/`.hdr` pairs)
- `scratch\step2b\` — grayscale/saturation-mask diagnostics (control/50ppm/150ppm only)
- `scratch\step3\` — Step 3 diagnostic images (segmentation sanity checks, class-mean plot)
- `raw_dn_spectra_PROVISIONAL_uncalibrated.csv` — project root, current feature table
- `step3_raw_dn_feature_table.py` — core pipeline functions (loader, masking, segmentation, extraction)
- `step3a_sanity_check_segmentation.py` — visual sanity-check script (3 samples)
- `step3b_build_feature_table.py` — full 28-sample extraction + plot
- `step4_baseline_models.py` — PROVISIONAL baseline classification (Random Forest) + regression (PLSR); exposes reusable `run_baseline()`
- `raw_dn_spectra_PROVISIONAL_SG_SNV.csv` — project root, SG-smoothed + SNV-transformed feature table (Step 3d)
- `step3d_sg_snv_preprocessing.py` — builds the SG+SNV feature table + class-mean plot
- `step4c_sg_snv_baseline_comparison.py` — re-runs Step 4 baselines on raw DN and SG+SNV side by side
- `scratch\step4\` — Step 4 results output (`step4_baseline_results.txt`, `step4_sg_snv_baseline_results.txt`)
