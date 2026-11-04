# Shot 09 — moving videos inside an original laptop screen

Prepared for the short sample on 2026-11-02.

## Original laptop and reference boundary

`lab9-laptop-source.png` was generated from a text prompt without an input image. The supplied screenshots were used only to understand the requested staging: real moving videos must play inside a laptop screen. No screenshot pixels, article layout, title, logo, thumbnail or channel branding are used in production.

`scripts/prepare_lab9_laptop.py` removes only the generated green display and preserves the laptop, bezel, keyboard and studio background. The measured 1920×1080 screen rectangle is `x=566, y=217, w=789, h=508`.

## Licensed moving footage

All three clips are new to this shot, landscape, and trimmed to four seconds / 120 frames at 30fps. The full originals were not included in the project. Pexels license: https://www.pexels.com/license/ — free use and modification; attribution is not required, but house-style on-screen credit is retained.

1. **Factory / `lab9-factory.mp4`**
   - Creator: **Pixabay** on Pexels.
   - Page: https://www.pexels.com/video/automatic-chocolate-machine-855117/
   - Description: automation in a factory with robotic arms.
   - Direct 1280×720 variant: https://videos.pexels.com/video-files/855117/855117-hd_1280_720_30fps.mp4
   - Used segment: **0.4–4.4 seconds**, resized to 1280×720, silent.
   - Page license link points to Pexels free/Creative Commons media terms.

2. **Train / `lab9-train.mp4`**
   - Creator: **Marc Curtis** on Pexels.
   - Page: https://www.pexels.com/video/train-passing-by-1089832/
   - Description: high-speed commuter train arriving at a modern station.
   - Direct 1920×1080 variant: https://videos.pexels.com/video-files/1089832/1089832-hd_1920_1080_30fps.mp4
   - Used segment: **2.0–6.0 seconds**, resized to 1280×720, silent.

3. **Solar / `lab9-solar.mp4`**
   - Creator: **K** on Pexels.
   - Page: https://www.pexels.com/video/rows-of-solar-panels-for-energy-production-2804599/
   - Description: high-angle drone footage of solar panels in a green field.
   - Direct 1280×720 variant: https://videos.pexels.com/video-files/2804599/2804599-hd_1280_720_24fps.mp4
   - Used segment: **6.0–10.0 seconds**, converted to 30fps, silent.

## Original editorial titles

The titles are descriptive sample titles, not copied headlines or claims requiring a news source:

- “Inside an Automated Factory”
- “Inside a High-Speed Rail Station”
- “Above a Field of Solar Panels”

Each episode has an on-screen footage credit. There is no social-platform logo, video-platform interface, channel name, third-party thumbnail or reference headline.

## Animation scope

A silent 12-second Remotion composition, `labLaptopVideos`, 360 frames at 30fps. Three real moving clips play inside the laptop display. Each new episode wipes over the previous one; the laptop remains visible while a subtle 1.06→1.10 camera push keeps the presentation alive. No camera shake, static screenshot substitution or production-video integration.
