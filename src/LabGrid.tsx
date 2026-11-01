import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
const {fontFamily: MONT} = loadFont();

// Invented titles + generic invented channel names (NO real outlets, NO logos).
// Footage: Wikimedia Commons free-licensed clips (sources in البطاقة.md), trimmed then originals deleted.
const CARDS = [
  {src: 'yt1.mp4', title: "Japan's Population Is Collapsing — Here's Why", t0: 221, dur: 761, rot: -2.4, delay: 8},
  {src: 'yt2.mp4', title: 'Inside Tokyo: The City Swallowing a Nation', t0: 97, dur: 554, rot: 1.8, delay: 40},
  {src: 'yt3.mp4', title: "9 Million Empty Homes: Japan's Akiya Crisis", t0: 342, dur: 688, rot: 2.0, delay: 72},
  {src: 'yt4.mp4', title: "Why Japan's Countryside Is Disappearing", t0: 158, dur: 603, rot: -1.5, delay: 104},
];

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;


const Player: React.FC<(typeof CARDS)[0]> = (c) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - c.delay, fps, config: {damping: 13, stiffness: 125}});
  const scale = interpolate(s, [0, 1], [1.45, 1]);
  const opacity = frame < c.delay ? 0 : Math.min(1, (frame - c.delay) / 6);
  const cur = c.t0 + frame / 30;
  const prog = Math.min(1, cur / c.dur);
  return (
    <div style={{width: 760, borderRadius: 14, overflow: 'hidden', background: '#0f0f0f', boxShadow: '0 30px 70px rgba(0,0,0,0.6)', transform: `rotate(${c.rot}deg) scale(${scale})`, opacity, fontFamily: MONT}}>
      {/* generic chrome bar — no platform branding at all */}
      <div style={{height: 40, background: '#1c1c1c', display: 'flex', alignItems: 'center', padding: '0 14px', gap: 7}}>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{width: 10, height: 10, borderRadius: 5, background: '#3a3a3a'}} />
        ))}
        <div style={{flex: 1, margin: '0 60px', height: 24, borderRadius: 12, background: '#121212', border: '1px solid #313131', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 10px'}}>
          <span style={{color: '#7a7a7a', fontSize: 11.5}}>Search</span>
          <svg width="12" height="12" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" fill="none" stroke="#8a8a8a" strokeWidth="2.6" /><line x1="15.5" y1="15.5" x2="21" y2="21" stroke="#8a8a8a" strokeWidth="2.6" /></svg>
        </div>
      </div>
      <OffthreadVideo muted src={staticFile(c.src)} style={{width: 760, height: 427, objectFit: 'cover', display: 'block'}} />
      {/* player control bar: red progress + pause + live time counter + volume + fullscreen — nothing verifiable */}
      <div style={{padding: '0 0 14px'}}>
        <div style={{height: 5, background: '#3d3d3d', position: 'relative'}}>
          <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${prog * 100}%`, background: '#f22'}} />
          <div style={{position: 'absolute', left: `calc(${prog * 100}% - 7px)`, top: -4.5, width: 14, height: 14, borderRadius: 7, background: '#f22'}} />
        </div>
        <div style={{display: 'flex', alignItems: 'center', padding: '10px 16px 0', gap: 14}}>
          <svg width="17" height="17" viewBox="0 0 24 24"><rect x="4" y="3" width="5.5" height="18" fill="#f1f1f1" /><rect x="14.5" y="3" width="5.5" height="18" fill="#f1f1f1" /></svg>
          <svg width="20" height="20" viewBox="0 0 24 24"><path d="M3 9h5l6-5v16l-6-5H3z" fill="#f1f1f1" /><path d="M17 8a5 5 0 010 8" stroke="#f1f1f1" strokeWidth="2" fill="none" /></svg>
          <span style={{color: '#ddd', fontSize: 13.5, fontWeight: 600, letterSpacing: 0.3}}>{fmt(cur)} / {fmt(c.dur)}</span>
          <div style={{flex: 1}} />
          <svg width="18" height="18" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.4" fill="#cfcfcf" /><path d="M12 2.8l1.7 2.9h-3.4L12 2.8zm0 18.4l-1.7-2.9h3.4L12 21.2zM2.8 12l2.9-1.7v3.4L2.8 12zm18.4 0l-2.9 1.7v-3.4l2.9 1.7z" fill="#cfcfcf" /></svg>
          <svg width="18" height="18" viewBox="0 0 24 24"><path d="M3 9V3h6M21 9V3h-6M3 15v6h6M21 15v6h-6" stroke="#f1f1f1" strokeWidth="2.4" fill="none" /></svg>
        </div>
        <div style={{padding: '12px 16px 2px', color: '#f1f1f1', fontSize: 22, fontWeight: 800, letterSpacing: 0.1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{c.title}</div>
      </div>
    </div>
  );
};

export const LabGrid: React.FC = () => {
  const frame = useCurrentFrame();
  const cam = interpolate(frame, [0, 360], [1.0, 1.09]);
  const tx = interpolate(frame, [0, 360], [0, -14]);
  // mood shift to documentary B&W (second reference treatment)
  const g = interpolate(frame, [250, 284], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#0a0a0c', overflow: 'hidden'}}>
      <AbsoluteFill style={{filter: `grayscale(${g}) sepia(${0.22 * g}) contrast(${1 + 0.06 * g}) brightness(${1 - 0.14 * g})`}}>
        <img src={staticFile('desk-bg.jpg')} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.3)', filter: 'blur(18px) brightness(0.3) saturate(0.7)'}} />
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
          <div style={{transform: `scale(${0.88 * cam}) translateX(${tx}px)`, display: 'flex', flexDirection: 'column', gap: 30}}>
            <div style={{display: 'flex', gap: 36}}>
              <Player {...CARDS[0]} />
              <Player {...CARDS[1]} />
            </div>
            <div style={{display: 'flex', gap: 36}}>
              <Player {...CARDS[2]} />
              <Player {...CARDS[3]} />
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(0,0,0,0.5) 100%)', pointerEvents: 'none'}} />
    </AbsoluteFill>
  );
};
