# Shot Lab 13 — assets, fonts and licenses

## Reference
- User-provided `Screenshot_20261101-122622.png` was used only as a visual reference for composition, materials and text.
- The reference screenshot is not embedded in the rendered sample.

## Paper and chalkboard assets
- `lab13-chalkboard.png`: newly AI-generated photorealistic empty chalkboard for this shot.
- `lab13-note-cutout.png`: physical-looking notebook paper, tape and three index marks extracted from a newly AI-generated scene for this shot.
- Editing was limited to image cropping, removal of blank middle grid rows, masking/cutout and recomposition. No paper, tape, grid, holes, torn edges or chalkboard are drawn programmatically in the Remotion component.
- No external stock photograph, platform logo or third-party artwork is used.

## Fonts
- **Kalam Bold**, Google Fonts / Indian Type Foundry. Source: https://github.com/google/fonts/tree/main/ofl/kalam
- **Montserrat Italic**, Google Fonts / Julieta Ulanovsky. Source: https://github.com/google/fonts/tree/main/ofl/montserrat
- Both are distributed under the **SIL Open Font License 1.1**. License texts: https://openfontlicense.org/open-font-license-official-text/
- Local font files are bundled so rendering does not depend on system fonts or a font CDN.
- Full copyright and license notices are included in `shot13-Kalam-OFL.txt` and `shot13-Montserrat-OFL.txt`.

## Audio
- `lab13-writing.wav` is an original deterministic synthesis: soft paper placement, filtered pencil-writing texture and a very quiet ambient bed.
- No sampled music, third-party SFX, narration, or platform audio.

## Technical
- Sample: 1920×1080, 30 fps, 300 frames / 10 seconds.
- Animation: subtle paper settle → left-to-right title writing → left-to-right subtitle writing. Static camera; no programmatic paper construction.
