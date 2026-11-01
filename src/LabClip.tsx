import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, spring, Easing} from 'remotion';
import {loadFont as loadPlayfair} from '@remotion/google-fonts/PlayfairDisplay';
import {loadFont as loadPT} from '@remotion/google-fonts/PTSerif';

const {fontFamily: PLAY} = loadPlayfair('normal', {weights: ['700', '900']});
const {fontFamily: PTS} = loadPT('normal', {weights: ['400', '700']});
const FPS = 30;

// deterministic jitter
const mkRng = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
};

// torn-edge polygon for a W×H sheet
const tornPath = (W: number, H: number, seed: number, jag: number) => {
  const r = mkRng(seed);
  const pts: string[] = [];
  const step = 26;
  for (let x = 0; x <= W; x += step) pts.push(`${x},${(r() - 0.5) * jag}`);
  for (let y = 0; y <= H; y += step) pts.push(`${W + (r() - 0.5) * jag},${y}`);
  for (let x = W; x >= 0; x -= step) pts.push(`${x},${H + (r() - 0.5) * (jag * 1.6)}`);
  for (let y = H; y >= 0; y -= step) pts.push(`${(r() - 0.5) * jag},${y}`);
  return `M ${pts.join(' L ')} Z`;
};

// ---------- cutting mat ----------
const Mat: React.FC = () => (
  <AbsoluteFill>
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 45% 40%, #2ea184 0%, #238f74 55%, #15705a 100%)'}} />
    {/* fine grid */}
    <div style={{position: 'absolute', inset: 0, background: 'repeating-linear-gradient(90deg, rgba(255,255,255,0.14) 0 2px, rgba(0,0,0,0) 2px 72px), repeating-linear-gradient(0deg, rgba(255,255,255,0.14) 0 2px, rgba(0,0,0,0) 2px 72px)'}} />
    {/* major grid */}
    <div style={{position: 'absolute', inset: 0, background: 'repeating-linear-gradient(90deg, rgba(255,255,255,0.28) 0 3px, rgba(0,0,0,0) 3px 288px), repeating-linear-gradient(0deg, rgba(255,255,255,0.28) 0 3px, rgba(0,0,0,0) 3px 288px)'}} />
    {/* ruler tick strips on edges */}
    <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: 34, background: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.55) 0 2px, rgba(0,0,0,0) 2px 24px)', opacity: 0.6}} />
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 34, background: 'repeating-linear-gradient(90deg, rgba(255,255,255,0.55) 0 2px, rgba(0,0,0,0) 2px 24px)', opacity: 0.6}} />
    {/* scuffs */}
    <div style={{position: 'absolute', left: '20%', top: '30%', width: 500, height: 2, background: 'rgba(255,255,255,0.08)', transform: 'rotate(14deg)'}} />
    <div style={{position: 'absolute', left: '55%', top: '70%', width: 380, height: 2, background: 'rgba(0,0,0,0.12)', transform: 'rotate(-9deg)'}} />
    {/* laptop edge prop (top) */}
    <div style={{position: 'absolute', left: 430, top: -60, width: 900, height: 140, background: 'linear-gradient(180deg,#3b4044,#23272a)', borderRadius: 18, transform: 'rotate(-2deg)', boxShadow: '0 14px 30px rgba(0,0,0,0.45)'}}>
      <div style={{position: 'absolute', left: 390, top: 86, width: 120, height: 34, borderRadius: 17, background: '#2fa868', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.3)'}} />
    </div>
    {/* stapled corner prop (bottom right) */}
    <div style={{position: 'absolute', right: 60, bottom: -30, width: 150, height: 110, background: 'linear-gradient(135deg,#6d7378,#4a4f54)', borderRadius: 10, transform: 'rotate(8deg)', boxShadow: '0 10px 22px rgba(0,0,0,0.4)'}}>
      {[18, 46, 74].map((t) => (
        <div key={t} style={{position: 'absolute', left: 14, top: t, width: 34, height: 6, background: '#c9ced2', borderRadius: 2}} />
      ))}
    </div>
    {/* vignette */}
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 48%, rgba(0,0,0,0.42) 100%)'}} />
  </AbsoluteFill>
);

// ---------- the clipping ----------
const W = 1430;
const H = 587;

export const LabClip: React.FC = () => {
  const f = useCurrentFrame();
  // camera: one slow push
  const cam = interpolate(f, [0, 239], [1.0, 1.065], {easing: Easing.linear});

  // red scrap enters (slide from top-left, settles)
  const sRed = spring({frame: f - 12, fps: FPS, config: {damping: 15, stiffness: 110}});
  // clipping slaps down (scale from above + rotation settle)
  const sClip = spring({frame: f - 24, fps: FPS, config: {damping: 13, stiffness: 130}});
  const clipScale = interpolate(sClip, [0, 1], [1.45, 1]);
  const clipRot = interpolate(sClip, [0, 1], [-15, -7.5]);
  const clipOp = interpolate(f, [24, 30], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const shad = interpolate(sClip, [0, 1], [60, 22]);

  // highlighter swipe over the number (after landing)
  const hl = interpolate(f, [78, 112], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.3, 0, 0.4, 1)});

  return (
    <AbsoluteFill style={{background: '#1a6b57', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${cam})`, transformOrigin: '52% 46%'}}>
        <Mat />

        {/* red scrap underneath */}
        <div style={{position: 'absolute', left: 170, top: 120, width: 760, height: 420, opacity: interpolate(sRed, [0, 0.2], [0, 1], {extrapolateRight: 'clamp'}), transform: `translate(${(1 - sRed) * -160}px, ${(1 - sRed) * -90}px) rotate(${interpolate(sRed, [0, 1], [-24, -13])}deg)`, filter: 'drop-shadow(0 14px 18px rgba(0,0,0,0.38))'}}>
          <Img src={staticFile('clip-red.png')} style={{width: 780, height: 370}} />
        </div>

        {/* newspaper clipping */}
        <div style={{position: 'absolute', left: 245, top: 230, width: W, height: H, opacity: clipOp, transform: `scale(${clipScale}) rotate(${clipRot}deg)`, transformOrigin: '50% 40%', filter: `drop-shadow(0 ${shad}px ${shad * 1.1}px rgba(0,0,0,0.5))`}}>
          <Img src={staticFile('clip-paper.png')} style={{position: 'absolute', left: 0, top: 0, width: W, height: H}} />

          {/* printed content */}
          <div style={{position: 'absolute', inset: 0, padding: '52px 100px 0 100px', textAlign: 'center', mixBlendMode: 'multiply'}}>
            {/* masthead */}
            <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 14}}>
              <div style={{fontFamily: PLAY, fontWeight: 900, fontSize: 34, color: '#141414', border: '3px solid #141414', lineHeight: 1, padding: '2px 7px'}}>TL</div>
              <div style={{fontFamily: PLAY, fontWeight: 700, fontSize: 32, color: '#1c1c1c', letterSpacing: 0.5}}>The Tokyo Ledger · Finance</div>
            </div>
            {/* headline */}
            <div style={{fontFamily: PLAY, fontWeight: 900, fontSize: 77, lineHeight: 1.06, color: '#17181a', marginTop: 18, letterSpacing: -0.5}}>
              Japan is vanishing —<br />except in Tokyo
            </div>
            {/* subhead with highlighter */}
            <div style={{fontFamily: PTS, fontWeight: 400, fontSize: 40, lineHeight: 1.3, color: '#26272a', marginTop: 22}}>
              The nation lost{' '}
              <span style={{position: 'relative', whiteSpace: 'nowrap', fontWeight: 700}}>
                <span style={{position: 'absolute', left: '-2%', top: '6%', bottom: '-2%', width: `${hl * 104}%`, background: '#f8e224', opacity: 0.85, transform: 'skewX(-6deg) rotate(-0.5deg)', borderRadius: 6, mixBlendMode: 'multiply'}} />
                <span style={{position: 'relative'}}>918,253 people</span>
              </span>{' '}
              to natural decline in 2025, while the capital alone gained 65,219 new residents
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
