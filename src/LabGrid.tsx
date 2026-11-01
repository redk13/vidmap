import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
const {fontFamily: MONT} = loadFont();

// Invented titles + generic invented channel names (NO real outlets, NO logos).
// Footage: Wikimedia Commons free-licensed clips (sources in البطاقة.md), trimmed then originals deleted.
const CARDS = [
  {src: 'yt1.mp4', title: "Japan's Population Is Collapsing — Here's Why", ch: 'Global Lens', subs: '2.1M subscribers', meta: '1.4M views • 3 weeks ago', likes: '38K', av: '#e05c4f', rot: -2.4, delay: 8},
  {src: 'yt2.mp4', title: 'Inside Tokyo: The City Swallowing a Nation', ch: 'Map & Data', subs: '890K subscribers', meta: '612K views • 1 month ago', likes: '21K', av: '#4f7fe0', rot: 1.8, delay: 40},
  {src: 'yt3.mp4', title: "9 Million Empty Homes: Japan's Akiya Crisis", ch: 'The Population Desk', subs: '1.3M subscribers', meta: '2.8M views • 2 months ago', likes: '95K', av: '#49b06e', rot: 2.0, delay: 72},
  {src: 'yt4.mp4', title: "Why Japan's Countryside Is Disappearing", ch: 'City Signals', subs: '640K subscribers', meta: '486K views • 5 days ago', likes: '17K', av: '#b06ec9', rot: -1.5, delay: 104},
];

const Pill: React.FC<{t: string; light?: boolean}> = ({t, light}) => (
  <div style={{background: light ? '#f1f1f1' : '#272727', color: light ? '#0f0f0f' : '#f1f1f1', borderRadius: 17, padding: '7px 13px', fontSize: 12.5, fontWeight: 700, marginLeft: 8, fontFamily: MONT, whiteSpace: 'nowrap'}}>{t}</div>
);

const Player: React.FC<(typeof CARDS)[0]> = (c) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - c.delay, fps, config: {damping: 13, stiffness: 125}});
  const scale = interpolate(s, [0, 1], [1.45, 1]);
  const opacity = frame < c.delay ? 0 : Math.min(1, (frame - c.delay) / 6);
  return (
    <div style={{width: 760, borderRadius: 14, overflow: 'hidden', background: '#0f0f0f', boxShadow: '0 30px 70px rgba(0,0,0,0.6)', transform: `rotate(${c.rot}deg) scale(${scale})`, opacity, fontFamily: MONT}}>
      {/* generic dark chrome bar — deliberately NOT a YouTube logo */}
      <div style={{height: 40, background: '#1c1c1c', display: 'flex', alignItems: 'center', padding: '0 14px', gap: 7}}>
        {['#3a3a3a', '#3a3a3a', '#3a3a3a'].map((col, i) => (
          <div key={i} style={{width: 10, height: 10, borderRadius: 5, background: col}} />
        ))}
        <div style={{flex: 1, margin: '0 60px', height: 24, borderRadius: 12, background: '#121212', border: '1px solid #313131', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 10px'}}>
          <span style={{color: '#7a7a7a', fontSize: 11.5}}>Search</span>
          <svg width="12" height="12" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" fill="none" stroke="#8a8a8a" strokeWidth="2.6" /><line x1="15.5" y1="15.5" x2="21" y2="21" stroke="#8a8a8a" strokeWidth="2.6" /></svg>
        </div>
      </div>
      <OffthreadVideo muted src={staticFile(c.src)} style={{width: 760, height: 427, objectFit: 'cover', display: 'block'}} />
      <div style={{padding: '12px 16px 15px'}}>
        <div style={{color: '#f1f1f1', fontSize: 21, fontWeight: 800, letterSpacing: 0.1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{c.title}</div>
        <div style={{display: 'flex', alignItems: 'center', marginTop: 10}}>
          <div style={{width: 34, height: 34, borderRadius: 17, background: c.av, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 800}}>{c.ch[0]}</div>
          <div style={{marginLeft: 10, lineHeight: 1.15}}>
            <div style={{color: '#fff', fontSize: 14, fontWeight: 700}}>{c.ch}</div>
            <div style={{color: '#9a9a9a', fontSize: 11}}>{c.subs}</div>
          </div>
          <Pill t="Subscribe" light />
          <div style={{flex: 1}} />
          <Pill t={`▲ ${c.likes}`} />
          <Pill t="Share" />
          <Pill t="Save" />
        </div>
        <div style={{marginTop: 10, color: '#8f8f8f', fontSize: 12.5}}>{c.meta}</div>
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
