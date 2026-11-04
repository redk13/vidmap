# Shot Lab 14B — online line sample: data, sources and licenses

## Purpose
A second, deliberately different use of the shot: a new subject, a line/area chart instead of a stacked bar, new labels, new color palette and a new static paper background. The shared visual family is bright dotted paper, restrained marginal pencil gestures and progressively drawn data.

## Verified data
- Indicator: **Individuals using the Internet (% of population)**.
- Geography: **World**.
- Series: **IT.NET.USER.ZS**, annual observations **2005–2025** used in this sample.
- Source: **World Telecommunication/ICT Indicators Database, International Telecommunication Union (ITU), via World Bank World Development Indicators**.
- API URL: https://api.worldbank.org/v2/country/WLD/indicator/IT.NET.USER.ZS?format=json&per_page=100
- Metadata: https://databank.worldbank.org/metadataglossary/world-development-indicators/series/IT.NET.USER.ZS
- The API response retrieved for this sample reports **lastupdated: 2026-10-08** and is preserved as `shot14-online-data.json`.
- Selected values: **2005 15.6%, 2010 28.4%, 2015 39.9%, 2020 60.1%, 2025 73.6%**. The line also uses every annual observation from 2005 through 2025.
- Final statement **73.6% of the world online in 2025** is the published rounded World Bank/ITU value, not a forecast.

## Reference and graphics
- No publisher chart, logo or screenshot is embedded.
- `lab14-online-paper.png` is a newly generated static cool-ivory dotted-paper background with faint marginal network/globe gestures. It differs from the first sample but preserves the same familiar paper-explainer flavor.
- The line, area, axes, labels, point markers and final callout are original Remotion/SVG graphics based on the saved data.

## Font
- **Montserrat**, Google Fonts / The Montserrat Project Authors, **SIL Open Font License 1.1**.
- Source: https://github.com/google/fonts/tree/main/ofl/montserrat
- Full license notice is carried forward from `shot13-Montserrat-OFL.txt` and will be included as `Montserrat-OFL.txt` in the independent archive.
- Local file: `lab14-Montserrat-Variable.ttf`; no network font request during rendering.

## Audio
- `lab14-online.wav` is original deterministic synthesis: quiet ambient bed, line-drawing texture and soft data-point tones.
- No narration, third-party music, sampled SFX or platform audio.

## Technical and reuse
- Sample: 1920×1080, 30 fps, 300 frames / 10 seconds.
- Static background; only data graphics and text animate. No camera shake.
- Future uses should derive the chart type, elements, labels, palette and background variation from the approved subject and script while retaining the familiar bright dotted-paper flavor.
