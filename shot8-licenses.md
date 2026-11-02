# Shot 08 — original paper throw, relighting and highlight

Prepared for the short sample on 2026-11-02.

## Original production imagery

No user-supplied reference image, reference pixels or reference-derived image is used in this version. The three production sources were generated independently from text prompts without an input image:

- `lab8-desk-source.png`: original dark walnut desk.
- `lab8-paper-a-source.png`: original blank curled sheet on a chroma background.
- `lab8-paper-b-source.png`: original blank bent sheet on a chroma background.

`scripts/build_lab8_papers.py` removes the chroma backgrounds, rasterizes original page layouts onto the two sheets and bakes a soft multiplicative exposure change into the second sheet. It does not add a white lighting stripe or screen-blended overlay.

## Verified data and original page content

The two original pages use the fact-checked MIC Statistics Bureau, Housing and Land Survey 2023 values:

- Japan vacant homes: **9.002 million**.
- Rental units: **4.436 million**.
- Other/abandoned: **3.856 million**.
- Second homes: **384,000**.
- For sale: **326,000**.
- Tokyo: about **898,000 vacant homes**, or **10.9%** of its housing stock.

The first sheet contains the proportional category chart and source line. The second sheet explains that vacancy is not necessarily abandonment. The highlighted sentence is original wording: **“Tokyo’s vacancy rate was 10.9% in 2023.”** Text faces rasterized into the sheets are DejaVu Serif and Montserrat. No third-party report scan is redistributed.

## Output assets

- `lab8-desk.webp`
- `lab8-paper1.png`
- `lab8-paper2-clean.png`
- `lab8-paper2-lit.png`
- `lab8-highlight-stroke.png`
- `lab8-highlight-content.png`

The transparent highlight-content asset contains the yellow stroke and original dark ink, so the sweep never washes out the selected sentence.

## Animation scope

A silent 10-second Remotion composition. The first printed sheet is thrown onto the desk; the second then falls over it. Only after both land do the surroundings dim and the baked paper illumination rise. The yellow marker sweeps left-to-right after the illumination and remains for reading. There is no camera shake, tearing, floating data card, platform branding or reference-derived compositing.

The user permits different verified data and different data-graphic elements in future productions.
