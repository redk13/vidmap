# Shot 06 — headline license gate

Verified on 2026-11-01 before creating the replacement sample.

## Rejected after checking

- BBC, Reuters and AP headlines: publication was verified, but no reuse license was verified. Not used.
- VOA / VOA Learning English: the general terms place exclusively VOA-produced material in the public domain, but the candidate Japan articles inspected were explicitly adapted from Associated Press reporting. Not used.
- No third-party photographs, logos, or outlet artwork are used in this shot.

## Cleared headlines

### 1 — Wikinews
- Exact headline: **Japan's population declines**
- Article date: **December 27, 2005**
- Article: https://en.wikinews.org/wiki/Japan's_population_declines
- License shown on the article: **Creative Commons Attribution 2.5**
- License: https://creativecommons.org/licenses/by/2.5/
- Reuse guidance: https://en.wikinews.org/wiki/Wikinews:Reusing_Wikinews_content
- Required on-frame attribution: **Wikinews · CC BY 2.5**
- Highlight: **population declines**
- Small newspaper columns: shortened/adapted from the licensed article text; adaptation recorded here.

### 2 — Wikinews
- Exact headline: **Asian stock markets slide; Nikkei at lowest level since '82**
- Article date: **October 27, 2008**
- Article: https://en.wikinews.org/wiki/Asian_stock_markets_slide;_Nikkei_at_lowest_level_since_'82
- License: **Creative Commons Attribution 2.5** (Wikinews articles published in this period)
- License: https://creativecommons.org/licenses/by/2.5/
- Required on-frame attribution: **Wikinews · CC BY 2.5**
- Highlight in the approved animation: **Asian stock markets slide;**
- Small newspaper columns: shortened/adapted from the licensed article text; adaptation recorded here.

### 3 — Global Voices
- Exact headline: **Go Farm, Young Man! – How Farming in Japan is Changing**
- Author: **Tomomi Sasaki**
- Article date: **May 31, 2009**
- Article: https://globalvoices.org/2009/05/31/japan-go-farm-young-man-how-farming-in-japan-is-changing/
- License: **Creative Commons Attribution 3.0**
- License: https://creativecommons.org/licenses/by/3.0/
- Attribution policy: https://globalvoices.org/about/global-voices-attribution-policy/
- Required attribution: **Tomomi Sasaki · Global Voices · CC BY 3.0**, plus the original article link preserved here.
- Highlight in the approved animation: **Go Farm, Young Man!**
- Small newspaper columns: shortened/adapted from the licensed article text; adaptation recorded here.

## Corrected layer rule after the user's clarification

The licensed headlines, dates and attribution are typeset onto a generated **wall** image. A separate generated gray **paper cover** hides that wall and uses independent top and bottom WebP image halves with real generated torn fibers. During the shot the cover halves move apart and reveal the text on the wall; the headline is not printed on the tearing paper. Remotion only moves the paper-cover images and does not procedurally create the paper or the wall.

In the approved version, the yellow highlights are **not baked into the wall**. Their exact text measurements are exported to `src/tear6-highlights.ts`; Remotion sweeps them onto the wall only after the paper has fully opened, using `#e5ed2f`, `scaleX`, and `mixBlendMode: multiply` so the letters and wall texture remain visible.

## Montserrat font notices

- Files: `Montserrat-ExtraBold.ttf` and `Montserrat-SemiBold.ttf`, used by `scripts/build_tear6_wall.py` when rebuilding the wall images.
- Source: https://github.com/google/fonts/tree/main/ofl/montserrat
- License: **SIL Open Font License 1.1**. The complete copyright and license notice is archived as `Montserrat-OFL.txt`; it must accompany redistributed font files.
- The already-built WebP walls do not require a font download during rendering.
