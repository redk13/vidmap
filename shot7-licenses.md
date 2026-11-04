# Shot 07 — moving city data: source and license gate

Updated for the varied-data-elements sample on 2026-11-01.

## Aerial footage used

- Title: **Drone Footage of City of Tokyo** — aerial view of Tokyo Skytree and cityscape.
- Creator: **ITO JUNICHI**.
- Publication date: **May 29, 2020**.
- Source page: https://www.pexels.com/video/drone-footage-of-city-of-tokyo-4511374/
- License: **Pexels License** — photos/videos are free to use and modify; attribution is not required. Credit is nevertheless kept on-screen and in this document.
- License text: https://www.pexels.com/license/
- Direct asset used for the fetch/cut step: https://videos.pexels.com/video-files/4511374/4511374-hd_1920_1080_30fps.mp4
- Excerpt: **16–28 seconds**, resized to 1920×1080, muted, 30fps. No original full-length file is retained in the workspace.
- Candidate rejected after preview: Pexels 4511381, because its camera leaves the city and looks at the river for most of the candidate interval.

## Data and graphic forms displayed

Values come from the fact-checked canonical `/home/user/Tokyo-SCRIPT.md`. No curve/line-chart element was added; the user's curve was explicitly only an example of variety, not a request to implement one.

1. **Large number — 0.96: Tokyo fertility, 2025.** MHLW via nippon.com and Jiji/PNA; canonical source section 3.
2. **Two-column comparison — Japan population 126.15M in 2020 and 87.0M in 2070.** IPSS Population Projections for Japan, 2023 revision, medium scenario; canonical source section 9. The 2070 column has a dotted treatment and the label **2070 SCENARIO**. Heights use the ratio 87/126.15.
3. **Dot-ratio matrix — 1.3 working-age people per senior in 2070.** Same IPSS medium scenario; canonical source section 9. Thirteen cyan dots and ten amber dots represent the equivalent ratio **13:10**; the graphic is labeled **2070 SCENARIO** and uses dotted treatment.
4. **Position gauge — 31.0: average age of first-time mother in Japan, 2025.** MHLW; canonical source section 11. The 28–34 axis is only a display scale; the marker enters at 31 without implying a time trend.
5. **Flow arrows — +65,219: Tokyo net migration, 2025.** MIC Basic Resident Register migration report; canonical source section 5. Animated chevrons flow toward a dotted Tokyo circle.

On-screen source line: **DATA: MHLW 2025 · MIC 2025 · IPSS 2023 MEDIUM SCENARIO** plus **AERIAL: ITO JUNICHI / PEXELS · 2020**.

## Visual scope

Original typographic title only; no real company logos or third-party branded logo artwork. The sample is a silent 12-second Remotion composition. Five different data-graphic forms appear in succession rather than accumulating as repeated number cards. All use reduced CSS 3D tilt, spring entrances, continuous diagonal drift and a moving exit. No curve element, decorative emoji, platform branding or production-video integration.

## Montserrat font

- File: `Montserrat-Variable.ttf`, loaded locally through `FontFace`; no Google Fonts/CDN request is made by the composition.
- Source: https://github.com/google/fonts/tree/main/ofl/montserrat
- License: **SIL Open Font License 1.1**. Full notice: `Montserrat-OFL.txt`, archived beside the font.
