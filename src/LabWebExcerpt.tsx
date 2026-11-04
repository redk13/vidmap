import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const easeOut = Easing.bezier(0.2, 0.82, 0.22, 1);
const BROWSER_X = 320;
const BROWSER_Y = 68;
const BROWSER_W = 1280;
const TOOLBAR_H = 70;
const PAGE_W = 1280;
const PAGE_H = 900;
const PAGE_VIEW_H = 810;

type Rect = {x: number; y: number; w: number; h: number};
type Highlight = Rect & {delay?: number};
type SceneSpec = {
  page: string;
  url: string;
  source: string;
  crop: Rect;
  targetW: number;
  targetY: number;
  highlights: Highlight[];
};

const scenes: SceneSpec[] = [
  {
    page: 'lab11-bls-cpi.svg',
    url: 'https://www.bls.gov/news.release/cpi.nr0.htm',
    source: 'Source: U.S. Bureau of Labor Statistics — Consumer Price Index, September 2026 — Public domain — bls.gov/news.release/cpi.nr0.htm',
    crop: {x: 40, y: 375, w: 1200, h: 232},
    targetW: 1640,
    targetY: 420,
    highlights: [{x: 42, y: 566, w: 1196, h: 40}],
  },
  {
    page: 'lab11-census-construction.svg',
    url: 'https://www.census.gov/construction/nrc/current/index.html',
    source: 'Source: U.S. Census Bureau — New Residential Construction, September 2026 — Public domain — census.gov/construction/nrc/current',
    crop: {x: 290, y: 295, w: 930, h: 225},
    targetW: 1600,
    targetY: 400,
    highlights: [
      {x: 300, y: 373, w: 740, h: 29},
      {x: 300, y: 407, w: 795, h: 29, delay: 7},
    ],
  },
  {
    page: 'lab11-eia-sectors.svg',
    url: 'https://www.eia.gov/energyexplained/us-energy-facts/',
    source: 'Source: U.S. Energy Information Administration — U.S. energy facts explained — Public domain — eia.gov/energyexplained/us-energy-facts',
    crop: {x: 290, y: 325, w: 930, h: 285},
    targetW: 1600,
    targetY: 340,
    highlights: [
      {x: 340, y: 378, w: 185, h: 30},
      {x: 340, y: 428, w: 200, h: 30, delay: 6},
      {x: 340, y: 478, w: 640, h: 30, delay: 12},
      {x: 364, y: 516, w: 730, h: 30, delay: 12},
    ],
  },
];

const Scanlines: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      pointerEvents: 'none',
      background: 'repeating-linear-gradient(0deg, rgba(8,18,22,0.045) 0px, rgba(8,18,22,0.045) 1px, transparent 1px, transparent 4px)',
      opacity: 0.52,
      mixBlendMode: 'multiply',
    }}
  />
);

const Browser: React.FC<{spec: SceneSpec; enter: number; dim: number}> = ({spec, enter, dim}) => {
  const y = BROWSER_Y + (1 - enter) * 28;
  const scale = 0.975 + enter * 0.025 - dim * 0.012;
  return (
    <div
      style={{
        position: 'absolute',
        left: BROWSER_X,
        top: y,
        width: BROWSER_W,
        height: TOOLBAR_H + PAGE_VIEW_H,
        borderRadius: 17,
        overflow: 'hidden',
        backgroundColor: '#fff',
        boxShadow: '0 26px 70px rgba(0,0,0,0.52), 0 0 0 1px rgba(255,255,255,0.2)',
        transform: `scale(${scale})`,
        transformOrigin: '50% 48%',
        filter: `blur(${dim * 1.35}px) brightness(${1 - dim * 0.18})`,
        fontFamily: 'Arial, Helvetica, sans-serif',
      }}
    >
      <div style={{position: 'absolute', left: 0, top: 0, width: '100%', height: TOOLBAR_H, background: 'linear-gradient(180deg,#f5f6f7 0%,#dde1e4 100%)', borderBottom: '1px solid #c5cacf'}}>
        {['#ef625b', '#e7bc45', '#62c75c'].map((color, i) => (
          <div key={color} style={{position: 'absolute', left: 22 + i * 24, top: 27, width: 13, height: 13, borderRadius: '50%', backgroundColor: color, boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.12)'}} />
        ))}
        <div style={{position: 'absolute', left: 116, top: 17, color: '#899198', fontSize: 34, fontWeight: 300, lineHeight: 1}}>‹</div>
        <div style={{position: 'absolute', left: 151, top: 17, color: '#a7adb2', fontSize: 34, fontWeight: 300, lineHeight: 1}}>›</div>
        <div style={{position: 'absolute', left: 238, top: 15, width: 804, height: 40, borderRadius: 8, backgroundColor: '#f8f9fa', border: '1px solid #d6dade', color: '#50585e', fontSize: 16, lineHeight: '38px', textAlign: 'center', letterSpacing: 0.05}}>
          {spec.url}
        </div>
        <div style={{position: 'absolute', right: 134, top: 22, color: '#8e969c', fontSize: 24, lineHeight: 1}}>↻</div>
        <div style={{position: 'absolute', right: 62, top: 21, color: '#929aa0', fontSize: 27, fontWeight: 300, lineHeight: 1}}>+</div>
        <div style={{position: 'absolute', right: 24, top: 25, width: 15, height: 17, border: '2px solid #a1a8ad', borderRadius: 3}} />
      </div>
      <div style={{position: 'absolute', left: 0, top: TOOLBAR_H, width: BROWSER_W, height: PAGE_VIEW_H, overflow: 'hidden', backgroundColor: '#fff'}}>
        <Img src={staticFile(spec.page)} style={{position: 'absolute', left: 0, top: 0, width: PAGE_W, height: PAGE_H, maxWidth: 'none'}} />
      </div>
      <Scanlines />
    </div>
  );
};

const WebScene: React.FC<{spec: SceneSpec}> = ({spec}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 11], [0, 1], {...clamp, easing: easeOut});
  const detach = interpolate(frame, [16, 36], [0, 1], {...clamp, easing: easeOut});
  const dim = interpolate(frame, [16, 38], [0, 1], clamp);
  const targetX = (1920 - spec.targetW) / 2;
  const targetH = spec.crop.h * (spec.targetW / spec.crop.w);
  const originalX = BROWSER_X + spec.crop.x;
  const originalY = BROWSER_Y + TOOLBAR_H + spec.crop.y;
  const left = interpolate(detach, [0, 1], [originalX, targetX]);
  const top = interpolate(detach, [0, 1], [originalY, spec.targetY]);
  const width = interpolate(detach, [0, 1], [spec.crop.w, spec.targetW]);
  const height = interpolate(detach, [0, 1], [spec.crop.h, targetH]);
  const pageScale = width / spec.crop.w;

  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 42%, #29312e 0%, #151a17 48%, #070908 100%)', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 110%, rgba(115,137,119,0.12), transparent 55%)'}} />
      <Browser spec={spec} enter={enter} dim={dim} />

      {frame >= 16 ? (
        <div
          style={{
            position: 'absolute',
            left,
            top,
            width,
            height,
            overflow: 'hidden',
            backgroundColor: '#fff',
            outline: `${Math.max(0.6, detach * 2)}px solid rgba(24,31,32,${0.35 + detach * 0.55})`,
            boxShadow: `0 ${detach * 24}px ${detach * 58}px rgba(0,0,0,${detach * 0.55})`,
          }}
        >
          <Img
            src={staticFile(spec.page)}
            style={{
              position: 'absolute',
              left: -spec.crop.x * pageScale,
              top: -spec.crop.y * pageScale,
              width: PAGE_W * pageScale,
              height: PAGE_H * pageScale,
              maxWidth: 'none',
            }}
          />
          {spec.highlights.map((hl, i) => {
            const delay = hl.delay ?? 0;
            const hp = interpolate(frame, [42 + delay, 55 + delay], [0, 1], {...clamp, easing: Easing.outQuad});
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: (hl.x - spec.crop.x) * pageScale,
                  top: (hl.y - spec.crop.y) * pageScale,
                  width: hl.w * pageScale,
                  height: hl.h * pageScale,
                  backgroundColor: '#edf343',
                  opacity: 0.69,
                  mixBlendMode: 'multiply',
                  transform: `scaleX(${hp})`,
                  transformOrigin: '0 50%',
                }}
              />
            );
          })}
          <Scanlines />
        </div>
      ) : null}

      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          bottom: 37,
          color: 'rgba(242,245,241,0.88)',
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 16,
          fontWeight: 400,
          letterSpacing: 0.05,
          textAlign: 'center',
          textShadow: '0 2px 10px rgba(0,0,0,0.9)',
        }}
      >
        {spec.source}
      </div>
    </AbsoluteFill>
  );
};

export const LabWebExcerpt: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#080a09'}}>
    {scenes.map((spec, i) => (
      <Sequence key={spec.page} from={i * 100} durationInFrames={100}>
        <WebScene spec={spec} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
