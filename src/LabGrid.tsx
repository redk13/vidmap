import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
const {fontFamily: MONT} = loadFont();

// Original "documentary monitor wall" template — deliberately nothing like YouTube.
// Invented titles; location lines are REAL filming locations of the free clips.
const CARDS = [
  {src: 'yt1.mp4', title: "Japan's Population Is Collapsing — Here's Why", loc: 'SHIBUYA CROSSING, TOKYO — ARCHIVE FOOTAGE', t0: 13262, delay: 8},
  {src: 'yt2.mp4', title: 'Inside Tokyo: The City Swallowing a Nation', loc: 'TOKYO STATION — ARCHIVE FOOTAGE', t0: 4817, delay: 40},
  {src: 'yt3.mp4', title: "9 Million Empty Homes: Japan's Akiya Crisis", loc: 'NAKAGIN TOWER, TOKYO — ARCHIVE FOOTAGE', t0: 20521, delay: 72},
  {src: 'yt4.mp4', title: "Why Japan's Countryside Is Disappearing", loc: 'SANJO BRIDGE, KYOTO — ARCHIVE FOOTAGE', t0: 9484, delay: 104},
];

const tc = (totalFrames: number) => {
  const f = Math.floor(totalFrames % 30);
  const s = Math.floor(totalFrames / 30) % 60;
  const m = Math.floor(totalFrames / 1800) % 60;
  const h = Math.floor(totalFrames / 108000);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(h)}:${p(m)}:${p(s)}:${p(f)}`;
};

const Monitor: React.FC<(typeof CARDS)[0]> = (c) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - c.delay, fps, config: {damping: 13, stiffness: 125}});
  const scale = interpolate(s, [0, 1], [1.45, 1]);
  const opacity = frame < c.delay ? 0 : Math.min(1, (frame - c.delay) / 6);
  // power-on flash as the screen comes alive
  const flash = interpolate(frame - c.delay, [0, 4, 12], [2.8, 1.5, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{width: 780, transform: `scale(${scale})`, opacity, fontFamily: MONT}}>
      {/* metal bezel */}
      <div style={{padding: 10, borderRadius: 10, background: 'linear-gradient(180deg,#2b2e33,#15161a)', boxShadow: '0 34px 70px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.09)'}}>
        <div style={{position: 'relative', borderRadius: 5, overflow: 'hidden'}}>
          <OffthreadVideo muted src={staticFile(c.src)} style={{width: 760, height: 427, objectFit: 'cover', display: 'block', filter: `brightness(${flash})`}} />
          {/* white sticker timecode, red running dot */}
          <div style={{position: 'absolute', top: 12, right: 12, background: '#ffffff', color: '#111', borderRadius: 4, padding: '4px 9px', display: 'flex', alignItems: 'center', gap: 7, boxShadow: '0 3px 8px rgba(0,0,0,0.4)'}}>
            <div style={{width: 8, height: 8, borderRadius: 4, background: '#d62828', opacity: Math.floor(frame / 15) % 2 === 0 ? 1 : 0.25}} />
            <span style={{fontFamily: 'Courier New, monospace', fontSize: 14, fontWeight: 700, letterSpacing: 0.5}}>{tc(c.t0 + frame)}</span>
          </div>
          {/* soft screen glass sheen */}
          <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(115deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0) 28%)', pointerEvents: 'none'}} />
        </div>
      </div>
      {/* documentary lower-third */}
      <div style={{display: 'flex', alignItems: 'flex-start', gap: 14, marginTop: 14, paddingLeft: 4}}>
        <div style={{width: 7, height: 46, background: '#ffd60a', marginTop: 3}} />
        <div>
          <div style={{color: '#f3f3f3', fontSize: 23, fontWeight: 800, letterSpacing: 0.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 740}}>{c.title}</div>
          <div style={{color: '#8e949c', fontSize: 12.5, fontWeight: 700, letterSpacing: 2.2, marginTop: 5}}>{c.loc}</div>
        </div>
      </div>
    </div>
  );
};

export const LabGrid: React.FC = () => {
  const frame = useCurrentFrame();
  const cam = interpolate(frame, [0, 360], [1.0, 1.09]);
  const tx = interpolate(frame, [0, 360], [0, -14]);
  const g = interpolate(frame, [250, 284], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#0a0b0d', overflow: 'hidden'}}>
      <AbsoluteFill style={{filter: `grayscale(${g}) sepia(${0.22 * g}) contrast(${1 + 0.06 * g}) brightness(${1 - 0.12 * g})`}}>
        {/* dark studio backdrop — no photo, pure light */}
        <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 38%, #1d2127 0%, #121419 45%, #08090b 100%)'}} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,255,255,0.035) 0%, rgba(255,255,255,0) 22%)'}} />
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', perspective: 1500}}>
          <div style={{transform: `rotateX(4deg) scale(${0.84 * cam}) translateX(${tx}px)`, display: 'flex', flexDirection: 'column', gap: 44}}>
            <div style={{display: 'flex', gap: 56}}>
              <Monitor {...CARDS[0]} />
              <Monitor {...CARDS[1]} />
            </div>
            <div style={{display: 'flex', gap: 56}}>
              <Monitor {...CARDS[2]} />
              <Monitor {...CARDS[3]} />
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 50%, rgba(0,0,0,0.55) 100%)', pointerEvents: 'none'}} />
    </AbsoluteFill>
  );
};
