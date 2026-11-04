# Shot 11 — verified public-domain web excerpts

Verified directly on **2026-11-02** before rendering.

## Reference analysis and boundary

The four supplied references establish this visual grammar:

1. A complete website is visible inside a rounded desktop-browser window on a dark background.
2. The enlarged strip is **the same pixels/content cropped from that page**, not a newly typeset quote card. Table rules, bullets, line breaks and typography remain consistent between the page and the crop.
3. The crop becomes wider than the browser and sits above it with a thin dark edge and a soft shadow; the original page stays visible behind it and becomes slightly subdued.
4. A fluorescent yellow marker selects only the relevant row, sentence or bullet after the crop has opened. Unselected text remains plain.
5. No extra headline board, polaroid, mascot, camera shake or unrelated decoration is needed.

The supplied screenshots are used only as staging references. Their URLs, publishers, logos, claims and screenshot pixels are **not copied** into this sample.

## Asset construction

`lab11-bls-cpi.svg`, `lab11-census-construction.svg` and `lab11-eia-sectors.svg` are original, text-based page reconstructions built by `scripts/build_shot11_pages.py`. They contain verified government text and data, but no third-party screenshot pixels, website CSS, official emblems, logos, photographs or protected illustrations.

Remotion displays each SVG as the full page and then displays **the same SVG again inside a moving crop rectangle**. The crop begins exactly over its source rectangle and expands from it. The animated highlight is a separate translucent multiply layer, so the underlying letters remain visible.

## 1. U.S. Bureau of Labor Statistics — public domain

- Page: **Consumer Price Index Summary — September 2026**.
- Release: **October 14, 2026**, USDL-26-1574.
- URL: https://www.bls.gov/news.release/cpi.nr0.htm
- Reused table rows are transcribed from Table A: All items, Food, Energy, Gasoline (all types), Electricity and Shelter, including the March–September 2026 values and the 12-month column.
- The enlarged/highlighted row is **Gasoline (all types)**: March `21.2`, April `5.4`, May `7.0`, June `-9.7`, July `-2.9`, August `3.9`, September `9.1`, and 12 months ending September `34.2`.
- Copyright policy: https://www.bls.gov/bls/linksite.htm — BLS states that everything it publishes is in the public domain except previously copyrighted photographs and illustrations; citation is requested. No BLS emblem, photograph or illustration is used.

## 2. U.S. Census Bureau — U.S. government text / public-use data

- Page: **Monthly New Residential Construction, September 2026**.
- Release: **October 20, 2026**, CB26-162.
- URL: https://www.census.gov/construction/nrc/current/index.html
- The excerpt reproduces the Building Permits heading and the published sentences concerning the seasonally adjusted annual rate of **1,400,000**, the revised August rate of **1,403,000**, the September 2025 rate of **1,444,000**, and single-family authorizations of **845,000**.
- Public-use/citation policy: https://www.census.gov/about/policies/citation.html — the Census Bureau asks users to cite the original source and identifies the Census Bureau and sponsoring agencies as authors when no individual author is listed.
- Open Government statement: https://www.census.gov/about/policies/open-gov.html — Census Bureau data are published as open data for public use and reuse.
- The release is U.S. government text; only text and numerical facts are reconstructed. No Census/HUD logos, sponsor artwork, photographs, icons or site screenshots are used.

## 3. U.S. Energy Information Administration — public domain

- Page: **U.S. energy facts explained — consumption and production**.
- URL: https://www.eia.gov/energyexplained/us-energy-facts/
- The excerpt uses the published heading **“Total energy consumption by the end-use sectors includes:”** and the listed items: **Primary energy use; Purchased electricity; Electrical system energy losses; Other energy losses**. The parenthetical explanation of electrical system energy losses is also transcribed from the page.
- Reuse policy: https://www.eia.gov/about/copyrights_reuse.php — EIA states that U.S. government publications are in the public domain and asks for an acknowledgment including the publication date. Protected photographs and the registered EIA logo are explicitly excluded from this sample.

## On-screen attribution and scope

Every scene includes its agency, page title, public-domain/source status and domain in a bottom source line inside the 60px horizontal safe margins. The browser address bar carries the full source URL. The sample is silent, 1920×1080, 300 frames at 30fps (10 seconds), composition `labWebExcerpt`. It is a shot-lab sample only, not a production insertion.
