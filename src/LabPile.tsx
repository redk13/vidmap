import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, spring, Easing, delayRender, continueRender, cancelRender} from 'remotion';
const registerLocalFont = (family: string, file: string, weight = '400 900') => {
  const handle = delayRender(`Loading local font: ${family}`);
  const face = new FontFace(family, `url("${staticFile(file)}")`, {style: 'normal', weight});
  face.load().then((loaded) => {
    document.fonts.add(loaded);
    continueRender(handle);
  }).catch(cancelRender);
};

registerLocalFont('Playfair Display', 'PlayfairDisplay-Variable.ttf');
registerLocalFont('Montserrat', 'Montserrat-Variable.ttf');
const PLAY = 'Playfair Display';
const MONT = 'Montserrat';
const FPS = 30;

type Strip = {
  img: string;
  flip?: boolean;
  x: number; y: number; w: number; h: number; rot: number; delay: number;
  source: string; headline: string; hero?: boolean; fs: number;
  bannerLeft?: number;
};

// REAL verified headlines (text-only attribution; no logos — trademark rule)
const STRIPS: Strip[] = [
  {img: 'strip2.png', x: 330, y: 60, w: 1260, h: 180, rot: 3.5, delay: 8, fs: 42,
   source: 'THE JAPAN TIMES', headline: "Japan's 2025 census reflects steepest fall in population on record", bannerLeft: 470},
  {img: 'strip1.png', x: 190, y: 255, w: 1530, h: 215, rot: -2.6, delay: 53, fs: 56, hero: true,
   source: 'The Asahi Shimbun', headline: "Japan's plunging population defies forecasts with new low in 2025"},
  {img: 'strip3.png', x: 90, y: 485, w: 1240, h: 165, rot: 2.2, delay: 98, fs: 34,
   source: 'THE JAPAN NEWS', headline: "Japan's Birth Rate Remains Stubbornly Low Despite Efforts", bannerLeft: 460},
  {img: 'strip1.png', flip: true, x: 370, y: 665, w: 1330, h: 170, rot: -4, delay: 143, fs: 40,
   source: 'THE ASAHI SHIMBUN', headline: "Japan's births mark record low in 2024, plummet below 700,000", bannerLeft: 495},
  {img: 'strip2.png', flip: true, x: 280, y: 850, w: 1370, h: 175, rot: 2.8, delay: 188, fs: 42,
   source: 'THE JAPAN TIMES', headline: "Japan's fertility rate hits record low despite government push", bannerLeft: 515},

];

const StripCard: React.FC<{s: Strip; f: number}> = ({s, f}) => {
  const sp = spring({frame: f - s.delay, fps: FPS, config: {damping: 13, stiffness: 125}});
  if (f < s.delay - 2) return null;
  const sc = interpolate(sp, [0, 1], [1.4, 1]);
  const rot = interpolate(sp, [0, 1], [s.rot * 2.2, s.rot]);
  const op = interpolate(f, [s.delay, s.delay + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const sh = interpolate(sp, [0, 1], [55, 20]);
  return (
    <div style={{position: 'absolute', left: s.x, top: s.y, width: s.w, height: s.h, opacity: op, transform: `scale(${sc}) rotate(${rot}deg)`, transformOrigin: '50% 45%', filter: `drop-shadow(0 ${sh}px ${sh}px rgba(0,0,0,0.45))`}}>
      <Img src={staticFile(s.img)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', transform: s.flip ? 'scaleX(-1)' : undefined}} />
      {s.hero ? (
        <div style={{position: 'absolute', inset: 0, textAlign: 'center', mixBlendMode: 'multiply', padding: '26px 70px 0 70px'}}>
          <div style={{fontFamily: PLAY, fontWeight: 700, fontStyle: 'italic', fontSize: 34, color: '#1d1d1f'}}>{s.source}</div>
          <div style={{fontFamily: PLAY, fontWeight: 900, fontSize: s.fs, lineHeight: 1.08, color: '#131416', letterSpacing: -0.5, marginTop: 8}}>{s.headline}</div>
        </div>
      ) : (
        <>
          <div style={{position: 'absolute', left: s.bannerLeft, top: -16, padding: '7px 26px', background: 'linear-gradient(180deg,#1d3b31,#122a22)', borderRadius: 3, boxShadow: '0 4px 10px rgba(0,0,0,0.35)'}}>
            <span style={{fontFamily: MONT, fontWeight: 800, fontSize: 25, color: '#f3f5f4', letterSpacing: 1.5}}>{s.source}</span>
          </div>
          <div style={{position: 'absolute', left: 50, right: 50, top: 56, textAlign: 'center', mixBlendMode: 'multiply'}}>
            <span style={{fontFamily: PLAY, fontWeight: 700, fontSize: s.fs, lineHeight: 1.12, color: '#17181a'}}>{s.headline}</span>
          </div>
        </>
      )}
    </div>
  );
};

export const LabPile: React.FC = () => {
  const f = useCurrentFrame();
  const cam = interpolate(f, [0, 359], [1.0, 1.02], {easing: Easing.linear});
  return (
    <AbsoluteFill style={{background: '#2b241c', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${cam})`, transformOrigin: '50% 44%'}}>
        <Img src={staticFile('desk-bg.jpg')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, objectFit: 'cover', filter: 'brightness(0.92)'}} />
        {/* strips render in landing order; hero lands 2nd but sits visually mid-pile */}
        {STRIPS.map((s) => (
          <StripCard key={s.source + s.delay} s={s} f={f} />
        ))}
        <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 52%, rgba(0,0,0,0.38) 100%)'}} />
      </div>
    </AbsoluteFill>
  );
};
