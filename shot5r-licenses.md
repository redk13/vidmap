# Shot Lab 05R — paper morph return: assets and method

## Scope
- A new small-sample return to the previously rejected crumpled-paper experiment.
- **No Blender, no Three.js, no cloth simulation and no mathematical-noise crumpling** are used in the new composition or its render path.
- The old rejected `LabCrumple` remains only as history; the new composition is `LabPaperMorph` and the old Three.js composition is removed from the active Root.

## Printed paper and background
- `crump-paper-2d.png` and `crump-strip-2d.png` derive from the original Shot Lab production textures `public/crump-paper.png` and `public/crump-strip.png`; the derivatives only key, crop and resize those pixels.
- `city-bg.jpg` is the original Shot Lab production background. These three source images were created for this project, not downloaded as stock photographs or scanned from third-party publications. Small newspaper-like marks in the generated paper texture are visual texture, not a reproduced real article.
- Original creator/production record: **Shot Lab**, first archived by commit author `lab <lab@local>` on 2026-11-01 in commit [`f22a5ad3a44fb92e03fa12c69b7094a07850aa7b`](https://github.com/redk13/vidmap/commit/f22a5ad3a44fb92e03fa12c69b7094a07850aa7b).
- Archived source files: [`crump-paper.png`](https://github.com/redk13/vidmap/blob/f22a5ad3a44fb92e03fa12c69b7094a07850aa7b/public/crump-paper.png), [`crump-strip.png`](https://github.com/redk13/vidmap/blob/f22a5ad3a44fb92e03fa12c69b7094a07850aa7b/public/crump-strip.png), and [`city-bg.jpg`](https://github.com/redk13/vidmap/blob/f22a5ad3a44fb92e03fa12c69b7094a07850aa7b/public/city-bg.jpg).
- Rights basis: original project production artwork; no external stock, photograph, publication scan, or third-party media license is part of this asset chain.
- The V8 script and Tokyo script are untouched. No new factual claim or narration is introduced.

## New generated transition assets
- `crump-wad-2d.png`: a newly generated photorealistic single wad using both original printed sheets as visual references, then externally keyed from black and cropped with its dark creases preserved.
- `crump-half-2d.png`: a newly generated halfway-unfurled connected object using the wad and both printed sheets as references, likewise keyed and cropped.
- These are controlled transition stills, not a claim of physical cloth simulation.

## Animation method
- Original Remotion/CSS 2.5D only: a direct three-frame materialization, circular wad reveal, a short half-open bridge, then eight vertical image strips per printed sheet unfolding with CSS perspective from the center outward. Revision 2 removes the converging flecks, entrance rotation and drift; Chapter 2 is above and the question sheet below.
- Timing: appear frames 0–3; fast open 8–34; readable hold; exact reverse close 196–222; fast vanish 222–225; 240 frames total.
- No camera shake, flying wad, tumble, slow opening or third-party animation library.

## Audio
- `crumple-morph.wav` is original deterministic synthesis: quiet ambience, a short materialization snap, paper unfurl/whoosh and mirrored closing/exit textures.
- No narration, sampled music, third-party SFX or platform audio.

## Technical
- Sample: 1920×1080, 30 fps, 240 frames / 8 seconds.
- Revision 2 was explicitly approved by the user for the shot library and Drive archive.
- Reuse rule confirmed by the user: all writing inside the papers must change to suit the approved information, narration and topic; the sample's Chapter 2 title and question are examples only.
