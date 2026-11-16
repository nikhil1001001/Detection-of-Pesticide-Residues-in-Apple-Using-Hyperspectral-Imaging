# Interview Prep — MTP Hyperspectral Apple Pesticide-Residue Pilot

Everything in this document is traceable to a real file in this project folder
(`C:\Documenten\A_Placement\CV pointers\INTERN\MTP`), primarily `PROJECT_NOTES.md`,
the `step3*.py` / `step4*.py` scripts, the two feature-table CSVs, the two Step 4
results `.txt` files, and the PNGs under `scratch\`. Where a claim in my resume
draft isn't backed by a file, I say so explicitly in Part 3 rather than smoothing
it over.

**One framing note to hold onto throughout:** this is a *provisional, uncalibrated*
pilot. Every number in this document is a raw-digital-number (raw DN) result, not
reflectance, and every model metric is a proof-that-the-pipeline-runs result, not a
real detection-performance claim, because of a class/acquisition-date confound
documented below. I say this once here so I don't have to caveat every sentence —
but if asked "is this a real result," the honest answer is always "not yet."

---

## PART 1 — Project Narrative

### 0. What this project actually is

The lab has a hyperspectral imaging (HSI) setup that scans apples treated with
different concentrations of a compound (0/control, 50ppm, 100ppm, 150ppm) and
saves each scan as a `.bil` (band-interleaved-by-line) cube: 800 lines × 1600
samples × 228 spectral bands, stored as unsigned 16-bit integers, covering
roughly 396.6nm to 1003.7nm. The eventual goal is to see whether the reflectance
spectrum of an apple's skin carries a detectable signature of pesticide
concentration. My work so far has been entirely on a **pilot subset** — 28 of the
roughly 400 relevant scans — to shake out the data-quality and pipeline problems
cheaply before scaling up.

### 1. Auditing the raw data — assumptions vs. reality

Before touching the pipeline, I audited the actual folder/file structure on the
source drive (`D:\Chandan__bil\`) instead of trusting my mental model of it. This
turned up several real discrepancies:

**The ppm-vs-filename mismatch.** The pilot folder names (`50ppm`, `100ppm`,
`150ppm`, `control`) don't always match the number embedded in the filenames
inside them:
- The `50ppm` folder (`Clp_cont_50ppm` at source) contains files named
  `Clp_25_cont_*` — filename says 25, folder says 50.
- The `100ppm` folder (`Clp_cont_100ppm`) contains files named `Clp_50_cont__*`
  — filename says 50, folder says 100.
- The `150ppm` and `control` folders are internally consistent (`Clp_150p_*` and
  `Control_*` respectively).

So two of the four classes show a clean "filename = folder-label / 2" pattern
while the other two don't. I don't know yet which number is ground truth — this
is Sudhir open question #3 in `PROJECT_NOTES.md`, still unresolved.

**A file-pairing issue.** Every `.bil` cube needs a matching `.bil.hdr` header
(wavelengths, dimensions, dtype) to be readable. Checking all 400 relevant source
files pair-by-pair, `Clp_cont_100ppm` has 100 `.bil` files but only 97 `.hdr`
files — `Clp_50_cont__98.bil`, `_99.bil`, and `_100.bil` have no header at all.
Those three specific source samples currently can't be loaded by my pipeline
(the `spectral` library needs the header to know cube dimensions and dtype).
None of the three happened to fall into my 28-sample pilot, so it didn't block
Step 3, but it will need to be resolved before scaling past the pilot.

**A naming-convention split within a single class.** Inside `Clp_cont_150ppm`
(100 source files), 90 files are named `Clp_150p_Cont_N` and 10 are named
`Clp_150p__N` (e.g. `Clp_150p__01` through roughly `_10`). This shows up in my
own 7-sample pilot for that class: `Clp_150p__01/04/07/10` alongside
`Clp_150p_Cont_13/16/19`. It looks like the first ~10 scans of that session used
one naming convention and the rest used another — a small thing, but it means
"grep the filename for a pattern" isn't a fully reliable way to enumerate a
class, which matters once I automate ingestion past the pilot.

**Folders beyond what I assumed existed.** The source drive has more than the 4
folders I expected. There's a *second*, unrelated `Control` folder (400 files,
`cont__01.bil` naming — different from `Appl_samp_control`, the one my pilot
`control` class actually draws from, which has 200 files / 100 pairs named
`Control_N`), plus `Mxd_m+c__hg/lw/md` and `Mz_cont_320/400/480ppm` folders that
look like a completely different experiment. I flagged these for awareness in
`PROJECT_NOTES.md` but didn't investigate them — they're out of scope for this
pilot.

**Scale of what's actually been touched.** The full source drive
(`D:\Chandan__bil\`) is 653GB; the 4 folders actually relevant to this project
total 220GB (55GB each); my pilot subset that's gone through the pipeline is
16GB. That's about 7% of the relevant 220GB, or 2.4% of the full 653GB drive.
This matters directly for the resume fact-check in Part 3.

### 2. Building the pilot subset

For each of the 4 classes I selected 7 samples out of the ~100 available:
5 for train, 2 for test, using a systematic (not random) pick — roughly every
third sample by index (e.g. `_1, _4, _7, _10, _13` for train, `_16, _19` for
test). This is a deliberately small, cheap-to-iterate-on slice meant to validate
the pipeline end-to-end before committing to a full run across ~400 samples.
`pilot_data\<class>\{train,test}\*.bil(+.hdr)` is the resulting layout, and that
folder structure is what defines the train/test split used everywhere downstream
— I never re-split randomly, I recover the split from which folder a sample
physically lives in (`discover_pilot_samples()` in
`step3_raw_dn_feature_table.py`).

### 3. Step 2b — grayscale bands, saturation masks, and the saturation argument

Before I picked up this project in earnest, some diagnostic work had already been
done and left in `scratch\step2b\`: a mid-band (band 95, 650.7nm) grayscale image
and a saturation mask for one sample each in control, 50ppm, and 150ppm (100ppm
was never run through this step — still an open gap), plus a saturation-vs-
wavelength plot for one control sample (`control1_saturation_vs_wavelength.png`).

I inspected these directly rather than trusting a prior summary. The saturation
mask (white = pixel value exactly 65535, the uint16 max — i.e. hard-clipped) shows
a narrow, consistent vertical strip on the right edge of the frame that's fully
saturated, in essentially the same spatial location across all three classes I
checked. I did not find or compute a formal spatial-overlap number (no IoU value
exists anywhere in the project files) — what I can honestly say is that the three
saturation masks I looked at are *visually* very similar in location and extent,
consistent with a fixed piece of equipment (not the apple) being responsible.

The saturation-vs-wavelength plot backs this up with a spectral-shape argument:
for that fixed right-edge region, the fraction of saturated pixels is ~0% below
420nm, jumps to ~100% between roughly 440-500nm, stays elevated (50-90%) through
most of the visible range with a dip around 750-760nm, and falls back to 0% above
~930nm. That wavelength-dependent shape (rather than "saturated at every
wavelength" or "random noise") reads like a real optical effect — something
reflective in that fixed strip overwhelming the sensor mostly in the visible
range — rather than a data-corruption artifact. This is exactly the region Step 3
excludes by masking `x >= 1290`.

**Important nuance I only fully worked out in Step 3's own sanity check:** this
saturated strip is *not* the same thing as the "equipment frame" I later found
fooling my Otsu segmentation (see below). The saturated strip sits right at/beyond
`x ≈ 1290` and is a hard clip at 65535. The equipment-frame brightness I found in
Step 3 shows up on *both* edges of the retained region (`x < 1290`) — including
the far left, which the saturation mask shows is *not* clipped — and it's just
relatively bright, non-saturated material. Two distinct phenomena, easy to
conflate, worth being precise about if asked.

### 4. Step 3 — building the raw-DN feature table

**Masking.** First step of the pipeline: drop columns `x >= 1290` from every cube
(`mask_edge_artifact()`), removing the known saturated strip described above,
before doing anything else.

**Segmentation — where I hit the first real problem.** The plan was to separate
apple pixels from background using Otsu's threshold on per-pixel mean intensity
across all 228 bands, then sanity-check the result on 2-3 samples before trusting
it on all 28 (deliberately, precisely because a threshold method like this can
fail silently). It did fail, immediately and instructively: a single global Otsu
split picked out the bright equipment-frame band on both edges of the field of
view as the "foreground," not the apple — because the frame-vs-chamber contrast
(chamber is ~4,000-12,000 raw DN, frame is ~40,000-53,000) is much larger than
the apple-vs-background contrast (apple ~3,800-8,500, background wall
~9,000-10,000 within the chamber). Worse, once I looked closely, the apple turned
out to be the *darker* region relative to the chamber wall — the opposite of what
I'd assumed going in.

I fixed this with a two-stage Otsu (`segment_apple_pixels()` in
`step3_raw_dn_feature_table.py`): stage 1 does a global Otsu to strip out the
bright frame and keep only the chamber interior; stage 2 re-runs Otsu restricted
to just that interior, and takes the *darker* cluster as apple. I re-validated
visually on the same 3 samples (plus later the corrupted-file investigation gave
me a 4th, described below) before trusting it on the full 28 — clean, correctly
shaped apple masks each time, with one small consistent artifact: a tiny bright
hole near the center gets excluded from every mask (visible in
`scratch\step3\*_apple_mask.png`), most likely a sticker or reference mark rather
than tissue.

**The other real bug — silent auto-scaling.** While debugging the segmentation
failure, I noticed the loaded pixel values looked wrong — maxing out around 6.55
instead of the tens-of-thousands I expected from a 16-bit sensor. Tracing it down,
the `spectral` Python library's `.load()` method silently divides every value by
the header's `reflectance scale factor` field (10000, present in every `.hdr`)
unless you explicitly pass `scale=False`. I'd been loading pre-divided values
while believing — and labeling everything as — raw DN. I verified the fix by
reading the `.bil` file directly as raw bytes with `numpy.fromfile(..., dtype="<u2")`
(bypassing the library entirely) and confirming the true min/max/mean (1048 /
65535 / 26842.7) matched `load(scale=False)` exactly. This is documented as a code
comment directly in `load_raw_dn_cube()`.

### 5. Step 3c — the corrupted-file investigation and the date/session confound

**Corrupted file.** After building the full 28-sample feature table, one sample —
`Clp_50_cont__4.bil` (100ppm, train) — stood out: its mean raw DN over segmented
apple pixels was 514.7 versus 4,770-5,315 for its six siblings, and its
segmentation mask showed only a broken ring instead of a filled apple. I checked
the *original* source file at `D:\Chandan__bil\Clp_cont_100ppm\Clp_50_cont__4.bil`
using the same pipeline: 21.0% apple pixels, mean raw DN 5,013.0 — squarely in the
sibling range, with a clean, normal-looking mask. Both copies were exactly
583,680,000 bytes (the correct size for this cube shape), so it wasn't a
truncation — the corruption happened somewhere in the copy step, root cause not
pursued further since re-copying resolved it. I overwrote the pilot copy with a
fresh copy from source, verified the new copy was byte-identical via MD5
checksum, and re-ran just that one sample through the pipeline to update its row
in the CSV. That class's per-sample standard deviation (of mean raw DN) dropped
from 1,719 to 191 after the fix — back in line with the other three classes
(169-394).

**Date/session confound.** This was the more consequential finding. Checking file
modification timestamps across *all* files in each of the 4 source folders (not
just my 28-sample pilot), every class was captured entirely within a single day:
control on 2025-11-12 (~3h11m), 50ppm on 2025-12-22 (~2h6m), 100ppm on
2025-12-26 (~2h11m), 150ppm on 2026-01-13 (~1h35m). Class label and acquisition
session are perfectly confounded across the *entire* 400-sample relevant dataset
— there's no within-class variation across different days anywhere in the data to
help separate "dose effect" from "which day this was scanned" effect (lighting
drift, sensor warm-up, apple batch, humidity, etc.). This directly limits what any
model trained on this data can prove, and it's the single most important caveat
attached to every result from here on.

### 6. Step 4 — baseline models (proof-of-pipeline, not a real result)

With the corrected feature table, I ran one untuned baseline per task, using the
existing 20-train/8-test split (never re-split):
- **Classification** — Random Forest (`n_estimators=200`), predicting
  `class_label` from all 228 raw-DN bands: 87.5% test accuracy (7/8), one 50ppm
  sample misclassified as control.
- **Regression** — PLSR (`n_components=5`), mapping class to nominal ppm
  (0/50/100/150) and predicting from the same 228 bands: R²=0.874, RMSE=19.8ppm.

Every result was printed and saved alongside an explicit caveat: given the
date/session confound above, these numbers are expected to be inflated because
the model may be learning "which day was this scanned" rather than "how much
pesticide is on this apple." High accuracy here is not good news — it's exactly
what you'd expect a model to produce even with zero real signal, if session
identity leaks through the raw DN amplitude.

### 7. Step 3d — Savitzky-Golay + SNV preprocessing

To see whether standard spectral preprocessing changed anything, I added
Savitzky-Golay smoothing (`window_length=15, polyorder=2` — reasonable
un-tuned defaults for a 228-band spectrum) followed by Standard Normal Variate
(SNV) normalization (`(spectrum - mean) / std`, per sample), applied to the
already-corrected raw-DN spectra. Saved as a new CSV
(`raw_dn_spectra_PROVISIONAL_SG_SNV.csv`), not overwriting the original.

Visually, SNV removed most of the raw amplitude offset between classes — where
the raw-DN plot showed a clear brightness ordering (control > 50ppm > 100/150ppm)
across the whole spectrum, the SNV plot has all 4 class-mean curves nearly
overlapping in the flat regions (~400-600nm, ~700-750nm). What's left after SNV
is shape, not amplitude: a shoulder around 640-680nm where 50ppm/100ppm sit above
control/150ppm, and a trough near 950-1000nm where 50ppm sits below the rest.
Whether that residual shape difference is a real spectral signature or still an
artifact of the confound is unresolved — SNV normalizes per-sample amplitude, it
does nothing to fix a session-level confound.

Re-running the same Step 4 baselines on this preprocessed table gave nearly
identical classification accuracy (87.5%, but a *different* sample misclassified
— a control sample as 150ppm this time) and slightly worse regression (R²=0.848,
RMSE=21.8ppm vs. 0.874/19.8ppm on raw DN). Preprocessing didn't meaningfully move
the headline numbers in either direction, and the same confound caveat applies to
both.

### 8. Current status and what's still open

**Done:** pilot subset assembled and verified; raw-DN extraction pipeline
(masking, two-stage segmentation, spectral extraction) validated and run on all
28 samples; one corrupted file found, traced, and fixed; SG+SNV preprocessing
added and compared; baseline classification and regression run on both the raw
and preprocessed tables, with confound caveats attached everywhere.

**Explicitly not done:** any reflectance/radiometric calibration — everything is
raw DN; no white/dark reference files have even been located yet. No
hyperparameter tuning or model comparison — one untuned baseline per task. Step
2b diagnostics for the 100ppm class. Independent re-verification of the other 27
pilot files against source (only the one flagged outlier was checked). Anything
beyond the 28-sample pilot — the other ~372 relevant source samples haven't been
touched by this pipeline at all.

**Open questions pending the lab (Sudhir):** what white/gray reference standard
was used, if any, and where that data lives (needed before any raw-DN →
reflectance conversion can happen); how much the saturation issue actually
matters for downstream analysis; which number is ground truth for the 50ppm/
100ppm classes (folder label or filename). All three are written down in
`PROJECT_NOTES.md` and none are resolved yet.

---

## PART 2 — Top 20 Interview Questions & Answers

### A. Technical / Methodology

**1. Why raw digital numbers (DN) instead of reflectance, this whole project?**
Because I don't have a validated way to get to reflectance yet. The `.hdr` files
carry a `reflectance scale factor = 10000` field, which implies someone intended
a specific calibration convention, but I haven't found any white/dark reference
captures anywhere in the project or source folders to actually calibrate against.
Rather than guess or silently apply that scale factor (which, as it turns out, is
exactly the bug I caught — see question B4/D2 below), I built the entire pipeline
explicitly on raw DN, labeled everything `raw_dn` in code and filenames, and
structured the loader (`load_raw_dn_cube()`) as the single, isolated function
that gets swapped out once calibration is sorted — everything downstream
(masking, segmentation, extraction, modeling) is written to be agnostic to
whether the cube holds raw counts or calibrated reflectance.

**2. Walk me through the segmentation approach and why it's two-stage.**
The naive approach — one global Otsu threshold on per-pixel mean intensity across
all 228 bands — fails on this data because there are three intensity populations
in the frame, not two: a bright equipment frame at both edges (~40,000-53,000 raw
DN), a chamber-wall background (~9,000-10,000), and the apple itself, which is
actually *darker* than the wall (~3,800-8,500). A single Otsu split finds the
largest bimodal separation, which is frame-vs-everything, not apple-vs-background.
I fixed it with two Otsu passes: first strip the frame (keep chamber interior via
threshold 1), then re-threshold just the interior and take the darker cluster as
apple. I caught this by doing exactly what I'd planned to do anyway — visually
sanity-checking the mask on a few real samples before trusting it on all 28 —
rather than assuming a standard technique would just work on data I hadn't looked
at yet.

**3. Why PLSR for the regression baseline instead of something like linear
regression or random forest regression?**
228 highly collinear spectral bands and only 20 training samples is a classic
small-n, high-p, collinear-features setup — ordinary least squares would be
badly underdetermined, and PLSR is the standard chemometrics tool for exactly
this situation because it projects onto a small number of latent components that
maximize covariance with the target, rather than trying to fit 228 independent
coefficients. I used `n_components=5` as a reasonable un-tuned default, not a
searched value — I was explicit in the code and in `PROJECT_NOTES.md` that no
hyperparameter tuning happened at this stage.

**4. Why Random Forest for the classification baseline?**
Mainly because it needed no feature scaling, handles the high-dimensional/
small-sample regime reasonably out of the box, and is easy to explain and defend
as a first baseline without hyperparameter search — which is exactly what this
step called for ("prove the pipeline runs end-to-end," not "find the best
model"). I did not compare it against alternatives at this stage; that's
explicitly listed as not-yet-done in `PROJECT_NOTES.md`.

**5. Why smoothing before SNV, and not the other way around?**
Savitzky-Golay smoothing reduces high-frequency noise per-band; SNV then
normalizes each *sample's* spectrum by its own mean and standard deviation to
remove multiplicative scaling/baseline effects. If you SNV first, you're
computing a sample's mean/std from noisy data, so smoothing first gives SNV a
cleaner signal to normalize. This is also the conventional order in
chemometrics preprocessing pipelines.

**6. How did you handle the train/test split, and why?**
I didn't create one — I recovered the existing one from the pilot's folder
structure (`pilot_data\<class>\{train,test}\`), which was set up before I got to
Step 4, at 5 train / 2 test per class (20/8 total). I explicitly did not re-split
randomly, both because the task called for reusing the existing split and because
with only 28 samples and a hard class/session confound, a different random split
wouldn't meaningfully change what the numbers can or can't tell you.

### B. Weaknesses & Hard Questions

**1. Your accuracy is 87.5% and R² is 0.87 — isn't that a strong result?**
No, and I'd push back on calling it a result at all yet. Every class in this
28-sample pilot was scanned entirely on one single day — control on Nov 12,
50ppm on Dec 22, 100ppm on Dec 26, 150ppm on Jan 13 — verified across all ~400
relevant source files, not just my pilot. Class label and acquisition session are
perfectly confounded: there's no way, with this data, to distinguish a model that
learned "pesticide spectral signature" from one that learned "which day's
lighting/sensor drift this was." High accuracy is exactly what I'd expect a model
to produce purely from session leakage, with zero real pesticide signal. I
attached that exact caveat to every printed and saved result specifically so it
can't be quoted out of context.

**2. Then why report the metrics at all?**
Because the goal of that step was explicitly to prove the classification/
regression pipeline runs end-to-end on real data — not to produce a trustworthy
number. That's a legitimate and separate thing to verify before investing in a
larger run: does the feature table load correctly, does the split reconstruct
correctly, do the models fit and predict without error, do the metrics compute
sensibly. It would have been just as useful, in a different way, if accuracy had
come back at chance level with everything running cleanly — I'd have learned the
plumbing works even though I didn't get that outcome.

**3. 28 samples is a tiny dataset. Why not wait until you have more before
modeling?**
Two reasons. First, the point of a pilot is to find integration problems cheaply
— and it worked: I found a corrupted file, an inverted segmentation assumption,
and a silent scaling bug, all of which would have been far more expensive to
debug at 400+ samples with a multi-hour-per-sample processing cost. Second, small
and confounded is actually the *more* important condition to test the pipeline
under, not less — if the code has bugs that only show up with more data (edge
cases in file discovery, memory issues, whatever), I'd rather find that after
fixing the cheaper bugs I already know about, not simultaneously with them.

**4. What would you actually need before you'd trust these numbers?**
Two things, and I have them written down as explicit open questions. First, a
resolved calibration path — a white/dark reference so I can convert raw DN to
reflectance and remove sensor/illumination-level differences directly, rather
than only partially normalizing them post-hoc with SNV. Second, and more
important: a session-balanced dataset, meaning each class needs to be represented
across multiple independent acquisition sessions/days, so a model can't trivially
separate classes by session artifacts. Without that second one specifically, no
amount of calibration or preprocessing fully closes the confound — you need the
experimental design itself to break the collinearity between "class" and "day."

**5. You found a corrupted file and a scaling bug — how do you know there
aren't more?**
I don't, and I said so directly in `PROJECT_NOTES.md`: only the one file that
produced an obviously anomalous result (mean raw DN an order of magnitude off
its siblings) was independently re-verified against source via checksum. The
other 27 pilot files were only plausibility-checked — their extracted spectra
looked reasonable relative to their class, which isn't the same as verifying
byte-for-byte fidelity to source. If I were scaling this past the pilot, I'd
want a systematic per-file checksum or statistical outlier pass before trusting
any of it, rather than relying on a human noticing one 10x-off number.

### C. "Walk me through this resume bullet"

**1. Overview — "Built an end-to-end ML pipeline (image segmentation, PLSR
regression, Random Forest) to detect pesticide residue on apples using HSI."**
The pipeline itself is real and does run end-to-end: raw `.bil` cube in, through
masking, two-stage Otsu segmentation, spectral extraction, optional SG+SNV
preprocessing, into a Random Forest classifier and a PLSR regressor, out to
metrics. What I'd be careful to clarify if pushed: it's "end-to-end" for the
28-sample provisional pilot specifically, not calibrated, and "detect pesticide
residue" slightly overstates it — the models predict which of 4 known,
experimenter-controlled treatment groups a sample belongs to (a supervised
classification/regression problem with ground-truth labels from the experimental
design), not detect an unknown residue level on an arbitrary apple. I'd reframe
it in conversation as "built and validated the pipeline architecture end-to-end
on a pilot subset; detection-performance claims are pending calibration and a
larger, session-balanced dataset."

**2. Bullet 1 — "Built an image segmentation pipeline (Otsu thresholding) in
Python, processing 600GB of raw 228-band hyperspectral apple sensor data."**
The segmentation pipeline is real, but "Otsu thresholding" understates it —
it's specifically a *two-stage* Otsu, and the reason it's two-stage is itself a
good story (a single global threshold picks up the equipment frame, not the
apple — see Part 1, Step 4 / Part 2 B). The "600GB" figure is the one I'd flag
hardest: the full source drive is 653GB, but that includes experiment folders
unrelated to this project. The 4 folders actually relevant to this pesticide
study total 220GB, and what I've actually run through the pipeline so far is the
28-sample pilot — 16GB, about 7% of the relevant 220GB or 2.4% of the full
653GB. "Processing 600GB" reads as a completed-scale claim; what's true today is
that the pipeline is validated on 16GB and designed to scale to the rest.

**3. Bullet 2 — "Achieved 87.5% classification accuracy (Random Forest) and
R2=0.87 (PLSR regression) predicting pesticide concentration from spectra."**
The numbers themselves are accurate — 0.875 test accuracy and R²=0.874 are
exactly what's in `scratch\step4\step4_baseline_results.txt`. What's missing
from the bullet is the confound caveat that's attached to those numbers
everywhere else in the project: each class was scanned on a single distinct day,
so these metrics are expected to be inflated by session leakage rather than
reflecting real pesticide-detection performance. Stated bare, on a resume or out
loud without that context, this bullet reads as a stronger claim than the data
supports. I'd either pair it verbally with the caveat every time or reframe as
"established a baseline modeling pipeline (RF/PLSR) achieving 87.5%/R²=0.87 on
a small provisional pilot — flagged as likely inflated pending a
session-balanced dataset."

**4. Bullet 3 — "Identified a data-quality issue across 800 samples and 4
acquisition sessions, informing redesign of lab's data-collection protocol."**
Two things to fix here. "800 samples" appears to double-count files-per-sample:
each sample is a `.bil` + `.bil.hdr` pair, so 200 files per class × 4 classes =
800 *files*, but 400 actual *samples* (100 per class). "4 acquisition sessions"
is accurate and well-supported — that's the exact, verified date-confound
finding. The bigger issue is "informing redesign of lab's data-collection
protocol" — nothing in this project's files shows the lab has redesigned
anything yet. The open questions (calibration reference, saturation, ppm/
filename mismatch) are written down in `PROJECT_NOTES.md` as pending Sudhir's
input, not as adopted changes. I'd reframe this as "identified and documented
data-quality issues across 400 samples and 4 single-day acquisition sessions —
including a session/class confound, missing header files, and a filename/label
mismatch — flagged for the lab's review," which is what actually happened.

### D. Process / Behavioral

**1. Tell me about a bug you found and how you found it.**
While debugging why my Otsu segmentation was picking out the wrong region, I
noticed the loaded pixel values looked wrong — capped around 6.5 instead of the
tens-of-thousands I'd expect from a 16-bit sensor. I traced it to the `spectral`
Python library's `.load()` silently dividing every value by the header's
`reflectance scale factor` field (10000) unless you pass `scale=False`
explicitly — undocumented-enough behavior that I'd missed it on first use. I
didn't just fix it and move on; I verified the fix independently by reading the
raw file as bytes with `numpy.fromfile(..., dtype="<u2")`, bypassing the library
completely, and confirmed the true min/max/mean matched what `load(scale=False)`
now returned. That verification step mattered — it's the difference between
"I think this is fixed" and "I confirmed against ground truth this is fixed."

**2. Tell me about a time an assumption you made turned out to be wrong.**
I assumed apple pixels would be brighter than the background — a reasonable
prior for a matte apple against what I expected to be a dark backdrop — and
built the first version of segmentation around that (threshold, keep everything
above it). The sanity-check step I'd planned specifically to catch this kind of
mistake did its job: on the very first sample I looked at, the "apple" mask was
highlighting the equipment frame around the edges, not the fruit. Looking more
carefully, the apple in this setup is actually darker than the surrounding
chamber wall. I didn't just flip a sign — I restructured the whole segmentation
into two stages once I understood there were three brightness populations in the
frame, not two.

**3. Describe a situation where you found a data-quality problem others might
have missed.**
One pilot sample (`Clp_50_cont__4.bil`, 100ppm) produced a mean raw DN an order
of magnitude below its six siblings, with a segmentation mask that looked broken
rather than apple-shaped. Instead of dropping it as an outlier or assuming my
code was wrong, I went back to the original source file on a different drive,
ran the identical pipeline on it, and got a completely normal result — proving
the corruption happened during the copy into my working folder, not at
acquisition. I fixed it properly: re-copied fresh, verified byte-for-byte
identity with an MD5 checksum against source, and re-ran the pipeline on just
that sample to update the table — rather than either silently dropping the row
or silently "fixing" the numbers by hand.

**4. How do you decide when a result is trustworthy enough to act on?**
I try to separate "did the code run correctly" from "does the result mean what
I want it to mean," and I don't let a clean run of the first stand in for the
second. The Step 4 baseline models ran without errors and produced strong-
looking metrics (87.5% accuracy, R²=0.87) — by the first standard, that's a
success. But I already knew, from the date-confound investigation two steps
earlier, that class and acquisition session are perfectly collinear in this
data, so I know the second standard isn't met. I reported the numbers anyway,
because "the pipeline runs" was genuinely the goal of that step, but I attached
the confound explanation to every place the numbers appear so nobody downstream
mistakes one kind of success for the other.

**5. How do you keep track of decisions and findings on a project like this?**
I keep a single `PROJECT_NOTES.md` file as the source of truth instead of
relying on memory or chat history — a running status summary, a list of open
questions actually pending someone else's input (not questions I've silently
resolved myself), and a dated session log of what was run and what was found,
including numbers, not just descriptions. When I was asked to write this very
interview-prep document, the instruction was explicitly not to rely on memory of
prior conversations — I re-read every script and re-opened every output file
fresh rather than trusting my own summary, and it's exactly how I caught two
more real findings (the missing `.hdr` files, the 150ppm naming split) that
weren't written down anywhere yet.

---

## PART 3 — Resume Bullet Fact-Check

### Overview: "Built an end-to-end ML pipeline (image segmentation, PLSR
regression, Random Forest) to detect pesticide residue on apples using HSI."

**Backed by:** `step3_raw_dn_feature_table.py` (segmentation), `step4_baseline_models.py`
(PLSR + Random Forest) — the pipeline genuinely runs cube-in to prediction-out.

**Imprecise/overstated:** "detect pesticide residue" implies real-world residue
detection; what's actually built is classification/regression against known,
experimenter-assigned treatment groups on a small uncalibrated pilot. "End-to-end"
is true only for the 28-sample pilot, not the full dataset.

**Honest reframe:** "Built and validated an end-to-end HSI analysis pipeline
(segmentation → PLSR/Random Forest) on a pilot subset, predicting known pesticide
treatment groups from raw spectra; calibration and real detection-performance
validation still pending."

### Bullet 1: "Built an image segmentation pipeline (Otsu thresholding) in
Python, processing 600GB of raw 228-band hyperspectral apple sensor data."

**Backed by:** `segment_apple_pixels()` in `step3_raw_dn_feature_table.py`
(genuinely Otsu-based); `.hdr` files confirm 228 bands.

**Imprecise/overstated:**
- "Otsu thresholding" undersells it — it's a two-stage Otsu, built specifically
  because single-stage Otsu failed (picked up equipment frame, not fruit).
- **"600GB" does not hold up.** Full source drive: 653GB (includes unrelated
  experiments). The 4 relevant class folders: 220GB. **What's actually been
  processed: 16GB (the 28-sample pilot) — about 7% of the relevant data, 2.4% of
  the full drive.** This is the single most overstated number across all four
  bullets.

**Honest reframe:** "Built a two-stage Otsu segmentation pipeline in Python for
228-band hyperspectral apple cubes; validated on a 16GB pilot subset drawn from a
~220GB relevant source dataset (653GB including unrelated experiments)."

### Bullet 2: "Achieved 87.5% classification accuracy (Random Forest) and
R2=0.87 (PLSR regression) predicting pesticide concentration from spectra."

**Backed by:** `scratch\step4\step4_baseline_results.txt` — accuracy 0.875,
R²=0.874, exact match.

**Imprecise/overstated:** Not the numbers themselves — the *absence* of the
confound caveat that's attached to these exact numbers everywhere else in the
project (`PROJECT_NOTES.md`, both results `.txt` files). Each class was scanned
on a single distinct day; these metrics are expected to be inflated by
session-level differences rather than real pesticide signal, and are explicitly
labeled provisional/not-trustworthy in every place they're recorded.

**Honest reframe:** "Established RF/PLSR baselines (87.5% accuracy, R²=0.87) on
a small provisional pilot — flagged as likely inflated by an acquisition-session
confound, pending a session-balanced dataset for a real performance claim."

### Bullet 3: "Identified a data-quality issue across 800 samples and 4
acquisition sessions, informing redesign of lab's data-collection protocol."

**Backed by:** date-confound table in `PROJECT_NOTES.md` — 4 classes, 4 distinct
single-day sessions, verified across all relevant source files.

**Imprecise/overstated:**
- "800 samples" appears to be file-count (200 files = 100 `.bil` + 100 `.hdr`
  pairs, ×4 classes = 800 files), not sample count. **Actual sample count: 400**
  (100 per class).
- "Informing redesign of lab's data-collection protocol" is not supported by
  anything in the project files — the findings are open questions logged for
  Sudhir's review in `PROJECT_NOTES.md`, not adopted protocol changes. No file
  documents any redesign having happened.

**Honest reframe:** "Identified and documented data-quality issues across 400
samples and 4 single-day acquisition sessions — including a class/session
confound, missing header files for 3 samples, and a filename/label mismatch —
flagged for the lab's review."

### Summary table

| Bullet | Core claim accurate? | Main issue |
|---|---|---|
| Overview | Mostly | "detect pesticide residue" overstates; it's treatment-group classification on an uncalibrated pilot |
| Bullet 1 | Partially | "600GB" — only 16GB (2.4% of the 653GB drive) has actually been processed |
| Bullet 2 | Numbers yes, framing no | Missing the confound caveat attached everywhere else to these exact numbers |
| Bullet 3 | Partially | "800" should be ~400 samples; "informing redesign" isn't documented as having happened |
