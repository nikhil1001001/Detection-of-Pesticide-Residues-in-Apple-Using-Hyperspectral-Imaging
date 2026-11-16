import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "NEW LEARNING NOTES: Hyperspectral AI & Chemometrics")
            self.drawRightString(558, 750, "Interview Preparation Guide")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer
        self.setFont("Helvetica", 8)
        self.drawString(54, 36, "Confidential — Placement & Interview Defense Notes")
        self.drawRightString(558, 36, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def build_pdf(filename="new_learning_notes.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A365D"),
        alignment=1, # Center
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'CVBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=6
    )

    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    ans_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    story = []

    # Title Banner
    story.append(Paragraph("NEW LEARNING NOTES", title_style))
    story.append(Paragraph("Hyperspectral Imaging (HSI) & Chemometrics Machine Learning Pipeline<br/><b>CV Bullet Defense & Comprehensive 30 Interview Q&A</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=12))

    # SECTION 1: Resume Overview & Bullet Points
    story.append(Paragraph("1. Final CV Pointers & Resume Highlighting Strategy", h1_style))
    
    obj_text = "Engineered automated hyperspectral imaging and chemometrics framework for non-destructive agro-chemical residue quantification on fruit."
    overview_text = f"<b>One-Liner Project Objective / Overview ({len(obj_text)} chars):</b><br/>" \
                    f"<i>{obj_text}</i>"
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 4))

    # Table of CV Points
    b1_text = "Architected HSI processing pipeline using 2-stage Otsu segmentation and SNV/SG filtering across 228 bands, reducing noise variance by 42%."
    b2_text = "Trained PLSR and Random Forest chemometric models with CARS wavelength selection, achieving 94.8% accuracy across 4 pesticide classes."
    b3_text = "Constructed a spatial-spectral 1D-CNN regression model for chemical residue quantification, reaching an R2 of 0.93 and 12% lower RMSE."

    table_data = [
        [Paragraph("<b>Bullet Focus</b>", body_style), Paragraph("<b>Exact Resume Bullet (133–138 Characters)</b>", body_style), Paragraph("<b>Chars</b>", body_style)],
        [
            Paragraph("<b>1. Data & Preprocessing</b>", body_style),
            Paragraph(f"• {b1_text}", bullet_style),
            Paragraph(f"<b>{len(b1_text)}</b>", body_style)
        ],
        [
            Paragraph("<b>2. Feature Sel. & ML</b>", body_style),
            Paragraph(f"• {b2_text}", bullet_style),
            Paragraph(f"<b>{len(b2_text)}</b>", body_style)
        ],
        [
            Paragraph("<b>3. Deep Learning & Reg.</b>", body_style),
            Paragraph(f"• {b3_text}", bullet_style),
            Paragraph(f"<b>{len(b3_text)}</b>", body_style)
        ],
    ]

    t = Table(table_data, colWidths=[120, 330, 45])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Highlighting Instructions
    highlight_box = [
        [Paragraph("<b>Where and How to Highlight on Your CV:</b>", body_style)],
        [Paragraph("• <b>Bullet 1:</b> <b>Architected HSI processing pipeline</b> using <b>2-stage Otsu segmentation</b> and <b>SNV/SG filtering</b> across 228 bands, reducing noise variance by <b>42%</b>.<br/>"
                   "• <b>Bullet 2:</b> Trained <b>PLSR</b> and <b>Random Forest</b> chemometric models with <b>CARS wavelength selection</b>, achieving <b>94.8% accuracy</b> across 4 pesticide classes.<br/>"
                   "• <b>Bullet 3:</b> Constructed a <b>spatial-spectral 1D-CNN</b> regression model for <b>chemical residue quantification</b>, reaching an <b>R² of 0.93</b> and <b>12% lower RMSE</b>.<br/>"
                   "<i>Tip: Bold only the core architecture/technique names and the quantifiable impact metrics. This allows recruiters to visually parse your skills in under 6 seconds while keeping ATS compatibility 100% clean.</i>", body_style)]
    ]
    hb_table = Table(highlight_box, colWidths=[495])
    hb_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#4299E1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(hb_table)
    story.append(Spacer(1, 10))

    # SECTION 2: Project Blueprint
    story.append(Paragraph("2. Project Architecture & Technical Foundations", h1_style))
    story.append(Paragraph(
        "<b>A. Hyperspectral Imaging (HSI) Fundamentals:</b> Unlike standard RGB images with 3 broad color channels, HSI collects a continuous spectral curve for every spatial pixel across hundreds of narrow, contiguous wavelength bands (e.g., 400 nm – 1000 nm in VNIR). This captures subtle chemical absorption signatures (molecular vibration overtones of C-H, O-H, P=O bonds in pesticides).<br/>"
        "<b>B. Data Cube:</b> Represented as a 3D tensor $X \\in \\mathbb{R}^{H \\times W \\times B}$ where $H, W$ are spatial dimensions and $B=228$ spectral bands.<br/>"
        "<b>C. Dual-Stage Otsu Segmentation:</b> Eliminates camera frame vignetting and bright equipment edges in Stage 1, followed by precise fruit-vs-conveyor thresholding in Stage 2 to isolate Region-of-Interest (ROI) spectral pixels.<br/>"
        "<b>D. Spectral Preprocessing:</b><br/>"
        "&nbsp;&nbsp;• <b>Savitzky-Golay (SG):</b> Polynomial least-squares smoothing and numerical 1st/2nd derivatives to remove random sensor noise and separate overlapping chemical absorption peaks.<br/>"
        "&nbsp;&nbsp;• <b>Standard Normal Variate (SNV):</b> $x_{snv} = (x - \\mu) / \\sigma$ centered per individual spectrum to normalize physical light scattering caused by fruit surface curvature and particle sizes.<br/>"
        "<b>E. Chemometric & ML Modeling:</b><br/>"
        "&nbsp;&nbsp;• <b>CARS (Competitive Adaptive Reweighted Sampling):</b> Monte Carlo sampling + exponentially decreasing function (EDF) selects the top 15–25% most informative spectral bands, pruning collinear noise.<br/>"
        "&nbsp;&nbsp;• <b>PLSR & Random Forest:</b> Latent variable projection and non-linear tree ensembles for 4-class multi-ppm discrimination.<br/>"
        "&nbsp;&nbsp;• <b>1D-CNN Regression:</b> Multi-layer convolutional filters extracting hierarchical spectral features to predict continuous ppm concentration.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # SECTION 3: Top 30 Interview Questions
    story.append(Paragraph("3. Top 30 Interview Questions & Defenses", h1_style))
    story.append(Paragraph("Categorized into 6 core domains: Hyperspectral Physics, Computer Vision, Signal Preprocessing, Feature Selection, ML/DL Modeling, and Validation/Deployment.", body_style))
    story.append(Spacer(1, 6))

    qa_list = [
        # Domain 1: HSI & Physics (1-5)
        ("Q1: What is the fundamental difference between RGB, Multispectral, and Hyperspectral Imaging?",
         "RGB captures 3 broad spectral bands (Red, Green, Blue). Multispectral captures 5 to 10 discrete, spaced bands. Hyperspectral captures hundreds of continuous, narrow bands (often 200+ with 2-5nm resolution), producing a complete spectral reflectance curve per pixel that identifies specific chemical bond absorptions."),

        ("Q2: Why can Hyperspectral Imaging detect pesticide residues that are invisible to RGB cameras?",
         "Chemicals like organophosphates or pyrethroids have characteristic vibrational and electronic absorption signatures in the Near-Infrared (NIR) region (700-1000 nm), corresponding to C-H stretch overtones and P=O / P-S bonds. RGB cannot resolve these narrow spectral dips, whereas HSI captures them across contiguous bands."),

        ("Q3: What is a Raw Digital Number (DN) versus Calibrated Reflectance?",
         "Raw DN represents raw integer sensor counts output by the detector (e.g., 0 to 65535 for 16-bit sensors), affected by non-uniform light intensity, dark current, and sensor gain. Calibrated Reflectance ($R = \\frac{DN_{raw} - DN_{dark}}{DN_{white} - DN_{dark}}$) standardizes the signal to true physical reflectance (0.0 to 1.0) independent of illumination."),

        ("Q4: What causes physical scattering and baseline shift in agricultural spectroscopy?",
         "Curvature of the fruit, surface roughness, skin wax, and non-uniform distance from the light source cause Rayleigh/Mie scattering. This shifts the entire spectral curve vertically or introduces multiplicative slope drift, requiring scatter-correction techniques like SNV or MSC."),

        ("Q5: What are the primary trade-offs of Hyperspectral Imaging in production environments?",
         "High data volume (gigabytes per scan), slower acquisition speeds (pushbroom line-scanning), high sensor cost, and high computational latency for 3D tensor processing. Mitigated by dimensionality reduction (CARS) to enable multispectral hardware deployment."),

        # Domain 2: CV & Segmentation (6-10)
        ("Q6: Why did you use a 2-stage Otsu segmentation instead of a standard single-threshold Otsu?",
         "The imaging chamber contains 3 distinct illumination zones: extremely bright reflective metal equipment frames, the fruit sample, and the dark chamber background. A single global threshold conflates the frame and fruit; 2-stage Otsu first isolates the sample chamber, then segments fruit pixels with 99%+ clean ROI boundaries."),

        ("Q7: How did you handle spatial border artifacts and sensor dead-pixel columns?",
         "Pushbroom line-scan cameras frequently have sensor-edge vignetting or stuck columns (e.g., columns x >= 1290). We applied hard spatial coordinate masking to eliminate defective edge sensor arrays prior to morphological cleaning and segmentation."),

        ("Q8: How do you extract representative sample features from segmented spatial pixels?",
         "After applying binary ROI masks, we compute the spatial mean spectrum across all valid fruit pixels to form a 1D feature vector of length 228, while also retaining pixel-wise variance to capture localized residue hotspots."),

        ("Q9: What morphological operations did you use to refine the segmented masks?",
         "Binary morphological opening (erosion followed by dilation) using a disk structuring element to remove isolated specks/dust, followed by hole filling to ensure a contiguous fruit silhouette."),

        ("Q10: Can spatial deep learning (e.g., 2D U-Net) replace Otsu segmentation here?",
         "Yes, a U-Net or Mask R-CNN can segment complex overlapping objects. However, for controlled conveyor/chamber setups, dual-stage Otsu executes in <5ms on CPU with zero annotation overhead, making it far more computationally efficient for production preprocessing."),

        # Domain 3: Preprocessing & Signal Cleaning (11-15)
        ("Q11: How does Savitzky-Golay (SG) filtering work mathematically, and why is it superior to moving average?",
         "SG fits a low-degree polynomial (e.g., degree 2 or 3) across a local sliding window using linear least squares. Unlike a moving average which blurs and flattens narrow chemical absorption peaks, SG preserves peak height, width, and shape while eliminating high-frequency stochastic noise."),

        ("Q12: Why apply the 1st or 2nd derivative in Savitzky-Golay filtering?",
         "The 1st derivative eliminates constant baseline drift across samples; the 2nd derivative eliminates linear slope variation and enhances overlapping chemical absorption peaks, making subtle pesticide signals linearly separable."),

        ("Q13: What is Standard Normal Variate (SNV) transformation and how is it calculated?",
         "SNV calculates the mean $\\mu$ and standard deviation $\\sigma$ of an individual spectrum across all bands and normalizes it: $x_{snv} = (x - \\mu) / \\sigma$. It removes sample-to-sample multiplicative scaling variations caused by fruit curvature and distance."),

        ("Q14: What is the difference between SNV and Multiplicative Scatter Correction (MSC)?",
         "SNV standardizes each spectrum independently without needing a reference spectrum. MSC fits each spectrum via linear regression against the mean spectrum of the training set ($x_i = a + b \\cdot \\bar{x} + e$). SNV is preferred in production because it avoids reference dependency."),

        ("Q15: How did you quantify the '42% spectral noise reduction' mentioned in your CV?",
         "Calculated using the high-frequency spectral variance and Signal-to-Noise Ratio (SNR) in dark/flat baseline bands before and after SG smoothing + SNV ($SNR = 10 \\log_{10}(\\mu_{signal}^2 / \\sigma_{noise}^2)$)."),

        # Domain 4: Feature Selection & Chemometrics (16-20)
        ("Q16: What is the 'Curse of Dimensionality' in Hyperspectral data?",
         "With 228 contiguous bands and limited physical fruit samples, adjacent bands are highly collinear (multicollinearity). This leads to severe overfitting, ill-conditioned covariance matrices in linear models, and inflated computational complexity."),

        ("Q17: How does Competitive Adaptive Reweighted Sampling (CARS) select informative wavelengths?",
         "CARS treats wavelength selection iteratively: 1) Builds PLS models on bootstrap samples; 2) Enforces an Exponentially Decreasing Function (EDF) to aggressively prune low-weight bands; 3) Uses Adaptive Reweighted Sampling (ARS) to keep bands with highest regression coefficients; 4) Selects the subset with lowest cross-validation RMSECV."),

        ("Q18: How does Successive Projections Algorithm (SPA) differ from CARS?",
         "SPA is a forward selection technique that uses vector projections in spectral space to minimize collinearity, selecting wavelengths that share minimal mutual information. CARS is randomized and weight-based; SPA is deterministic and orthogonal."),

        ("Q19: Why use Partial Least Squares Regression (PLSR) instead of standard Multiple Linear Regression (MLR)?",
         "MLR fails when features are collinear because $(X^T X)^{-1}$ cannot be inverted stably. PLSR projects both features $X$ and targets $Y$ into low-dimensional orthogonal latent variables that maximize the covariance between $X$ and $Y$."),

        ("Q20: How do you choose the optimal number of Latent Variables (LVs) in PLSR?",
         "Using $K$-fold cross-validation, plotting Root Mean Square Error of Cross-Validation (RMSECV) against number of LVs. The optimal number is chosen at the minimum RMSECV or using the 1-standard-error rule to prevent overfitting."),

        # Domain 5: ML & Deep Learning (21-25)
        ("Q21: Why use a 1D-CNN over classical machine learning models for spectral regression?",
         "1D-CNNs apply local convolutional kernels directly across adjacent spectral bands, capturing localized multi-band absorption shapes regardless of slight wavelength shifts. They learn hierarchical non-linear feature representations without manual feature engineering."),

        ("Q22: Describe the architecture of your 1D-CNN regression model.",
         "Input tensor: $(B, 228, 1)$. Layer 1: Conv1D (16 filters, kernel 7, ReLU) + BatchNorm + MaxPool; Layer 2: Conv1D (32 filters, kernel 5, ReLU) + BatchNorm + MaxPool; Layer 3: Conv1D (64 filters, kernel 3, ReLU) + GlobalAveragePooling; Dense(64, ReLU) + Dropout(0.3) -> Dense(1, Linear) output."),

        ("Q23: How does Random Forest perform on chemometric spectral classification?",
         "Random Forest handles high-dimensional non-linear interactions and outputs feature importances (Gini importance/Mean Decrease Impurity). When paired with CARS band selection, it provides robust classification across discrete pesticide dosage classes (0, 50, 100, 150 ppm)."),

        ("Q24: What loss function and optimizer did you use for continuous chemical concentration regression?",
         "Smooth L1 Loss (Huber Loss) with Adam optimizer (learning rate $1e-3$ with cosine annealing decay). Huber Loss is robust to extreme spectral outlier noise compared to Mean Squared Error (MSE)."),

        ("Q25: What is a 3D-CNN / Spatial-Spectral Transformer in HSI, and when is it necessary?",
         "A 3D-CNN applies volumetric kernels across both spatial dimensions $(H, W)$ and the spectral dimension $(B)$ simultaneously. It is essential when spatial distribution patterns (e.g., droplet residue patches) correlate with contamination severity."),

        # Domain 6: Validation, Metrics & Deployment (26-30)
        ("Q26: What is data leakage in hyperspectral datasets, and how did you prevent it?",
         "Data leakage occurs if pixel spectra from the same apple scan appear in both train and test sets, or if calibration/scaling parameters are computed over the full dataset before splitting. We used Group K-Fold / Sample-level splitting, fitting SNV and scalers strictly on training folds."),

        ("Q27: How do you evaluate regression performance in Chemometrics? Define $R^2$ and RMSEP.",
         "$R^2$ (Coefficient of Determination) measures the proportion of variance explained by the model ($1 - SS_{res}/SS_{tot}$). RMSEP (Root Mean Square Error of Prediction) quantifies average ppm error on the unseen test set: $\\sqrt{\\frac{1}{N}\\sum(y_i - \\hat{y}_i)^2}$."),

        ("Q28: What is the Residual Predictive Deviation (RPD) metric?",
         "$RPD = SD / RMSEP$, where $SD$ is standard deviation of target values. An $RPD > 2.5$ indicates an excellent quantitative chemometric model suitable for industrial screening."),

        ("Q29: How would you optimize this model for real-time edge deployment on an industrial sorting conveyor?",
         "1) Prune bands down to 10-15 key wavelengths identified by CARS; 2) Quantize the 1D-CNN to INT8 via TensorRT/ONNX Runtime; 3) Run batched inference on edge GPU/NPU achieving <15ms total latency per fruit."),

        ("Q30: How would you handle domain shift caused by different apple varieties or ambient temperature changes?",
         "Apply Domain Adaptation / Transfer Learning: 1) Collect calibration transfer standards; 2) Apply Piecewise Direct Standardization (PDS) or External Parameter Orthogonalization (EPO) to project out ambient temperature subspace drift; 3) Fine-tune the CNN head with small target-variety samples.")
    ]

    for i, (q, a) in enumerate(qa_list, 1):
        # Keep each Q&A item together if possible
        item = []
        item.append(Paragraph(f"<b>{q}</b>", q_style))
        item.append(Paragraph(f"<b>Answer:</b> {a}", ans_style))
        item.append(Spacer(1, 4))
        story.append(KeepTogether(item))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename} ({len(qa_list)} questions included).")

if __name__ == "__main__":
    build_pdf("new_learning_notes.pdf")
