import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {TEAR_HIGHLIGHTS} from './tear6-highlights';

// Correct reference structure: the HEADLINE is on the wall behind.
// A separate gray paper sheet covers it and tears into top/bottom halves.
const WALLS = ['tear6-wall-1.webp', 'tear6-wall-2.webp', 'tear6-wall-3.webp'] as const;
const CARD = 120;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const LabTearWall: React.FC = () => {
  const frame = useCurrentFrame();
  const index = Math.min(WALLS.length - 1, Math.floor(frame / CARD));
  const local = frame - index * CARD;
  const enter = interpolate(local, [6, 30], [0, 1], {...clamp, easing: Easing.bezier(0.22, 0.72, 0.22, 1)});
  const leave = interpolate(local, [100, 118], [0, 1], {...clamp, easing: Easing.bezier(0.22, 0.72, 0.22, 1)});
  const open = local < 100 ? enter : 1 - leave;
  const travel = 480 * open;
  const shadowAlpha = 0.35 * open;

  return (
    <AbsoluteFill style={{background: '#dededa', overflow: 'hidden'}}>
      {/* The licensed headline, date and attribution live on the wall. */}
      <Img src={staticFile(WALLS[index])} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />

      {/* Selective highlighter strokes begin only after the paper is fully open.
          Multiply keeps the black letters and the wall texture visible. */}
      {TEAR_HIGHLIGHTS[index].map((rect, markIndex) => {
        const start = 34 + markIndex * 5;
        const sweep = interpolate(local, [start, start + 12], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
        return (
          <div
            key={`${index}-${markIndex}`}
            style={{
              position: 'absolute',
              left: rect.x,
              top: rect.y,
              width: rect.width,
              height: rect.height,
              background: '#e5ed2f',
              mixBlendMode: 'multiply',
              transform: `scaleX(${sweep})`,
              transformOrigin: 'left center',
            }}
          />
        );
      })}

      {open <= 0.001 ? (
        <Img src={staticFile('tear6-cover-full.webp')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
      ) : (
        <>
          <Img src={staticFile('tear6-cover-bottom.webp')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080, transform: `translateY(${travel}px)`, filter: `drop-shadow(0 ${-10 * open}px ${14 * open}px rgba(0,0,0,${shadowAlpha}))`}} />
          <Img src={staticFile('tear6-cover-top.webp')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080, transform: `translateY(${-travel}px)`, filter: `drop-shadow(0 ${10 * open}px ${14 * open}px rgba(0,0,0,${shadowAlpha}))`}} />
        </>
      )}
    </AbsoluteFill>
  );
};
