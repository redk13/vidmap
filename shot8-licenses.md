# Shot 08 — fully generated dense papers, relighting and highlight

Prepared for the short sample on 2026-11-02.

## Original production imagery

No user-supplied reference image, reference pixels or reference-derived image is used. The production sources were generated independently without an input reference image:

- `lab8-desk-source.png`: original dark walnut desk.
- `lab8-full-paper-a-source.png`: a complete generated printed report, including its chart, dense body text, numerical labels and source line.
- `lab8-full-paper-b-source.png`: a complete generated printed article, including its dense paragraphs and the selected sentence.

Both sheets are flat rectangles with square corners. Neither has a folded, curled or dog-eared lower corner. The paper, typography, chart and article layout are part of the generated images; they are not programmatically constructed or typeset.

`scripts/prepare_lab8_generated.py` only cuts the finished sheets out of their chroma backgrounds, scales them without distortion, bakes a soft multiplicative exposure change into the second sheet, and prepares the separate yellow marker effect. It does not draw a paper, chart, paragraph or selected sentence.

## Verified data visible in the generated pages

The pages use the fact-checked MIC Statistics Bureau, Housing and Land Survey 2023 values:

- Japan vacant homes: **9.002 million**.
- Rental units: **4.436 million**.
- Other/abandoned: **3.856 million**.
- Second homes: **384,000**.
- For sale: **326,000**.
- Tokyo: about **898,000 vacant homes**, or **10.9%** of its housing stock.

The highlighted sentence generated into the second sheet is: **“Tokyo’s vacancy rate was 10.9% in 2023.”** Both sheets carry the MIC source line. No third-party report scan is redistributed.

## Output assets

- `lab8-desk.webp`
- `lab8-paper1.png`
- `lab8-paper2-clean.png`
- `lab8-paper2-lit.png`
- `lab8-highlight-stroke.png`
- `lab8-highlight-content.png`

The transparent highlight-content asset contains the yellow stroke and the original generated dark ink, so the sweep does not wash out the selected sentence.

## Animation scope

A silent 10-second Remotion composition. The first printed sheet is thrown onto the desk; the second then falls over it. Only after both land do the surroundings dim and the baked paper illumination rise. The yellow marker sweeps left-to-right after the illumination and remains for reading. There is no camera shake, tearing, floating data card, platform branding or reference-derived compositing.

The user permits different verified data and different data-graphic elements in future productions.
