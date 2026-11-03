# Shot Lab 05R — paper morph return: assets and method

## Scope
- A new small-sample return to the previously rejected crumpled-paper experiment.
- **No Blender, no Three.js, no cloth simulation and no mathematical-noise crumpling** are used in the new composition or its render path.
- The old rejected `LabCrumple` remains only as history; the new composition is `LabPaperMorph` and the old Three.js composition is removed from the active Root.

## Printed paper and background
- `crump-paper-2d.png` and `crump-strip-2d.png` derive from the original frozen Tokyo sample textures recovered from `public/crump-paper.png` and `public/crump-strip.png` on the `shot-lab` branch.
- `city-bg.jpg` is the original sample background already present in the project.
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
- `crumple-morph.wav` is original deterministic synthesis: quiet ambience, converging fiber ticks, paper unfurl/whoosh and mirrored closing/exit textures.
- No narration, sampled music, third-party SFX or platform audio.

## Technical
- Sample: 1920×1080, 30 fps, 240 frames / 8 seconds.
- Sample only; not approved and not part of the approved-shot vault unless the user explicitly approves after viewing.
