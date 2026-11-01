import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

// Shot 06 replacement: generated raster paper, licensed headlines baked in,
// then each clipping physically cut into two WebP halves by scripts/build_tear6_assets.py.
// This component does NOT draw paper, dots, textures, headlines or source names.
const CARDS = [
  {top: 'tear6-1-top.webp', bottom: 'tear6-1-bottom.webp'},
  {top: 'tear6-2-top.webp', bottom: 'tear6-2-bottom.webp'},
  {top: 'tear6-3-top.webp', bottom: 'tear6-3-bottom.webp'},
] as const;

const W = 1500;
const H = 760;
const CARD = 120;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const HalfClipping: React.FC<{top: string; bottom: string; local: number}> = ({top, bottom, local}) => {
  const enter = interpolate(local, [4, 28], [0, 1], {...clamp, easing: Easing.bezier(0.22, 0.72, 0.22, 1)});
  const leave = interpolate(local, [100, 118], [0, 1], {...clamp, easing: Easing.bezier(0.22, 0.72, 0.22, 1)});
  const open = local < 100 ? enter : 1 - leave;
  const opacity = interpolate(local, [0, 3], [0, 1], clamp) * interpolate(local, [118, 119], [1, 0], clamp);
  const travel = 190 * (1 - open);

  return (
    <div style={{position: 'absolute', left: (1920 - W) / 2, top: (1080 - H) / 2, width: W, height: H, opacity}}>
      <Img src={staticFile(bottom)} style={{position: 'absolute', inset: 0, width: W, height: H, transform: `translateY(${-travel}px)`, filter: 'drop-shadow(0 15px 13px rgba(0,0,0,0.32))'}} />
      <Img src={staticFile(top)} style={{position: 'absolute', inset: 0, width: W, height: H, transform: `translateY(${travel}px)`, filter: 'drop-shadow(0 15px 13px rgba(0,0,0,0.32))'}} />
    </div>
  );
};

export const LabTear6: React.FC = () => {
  const frame = useCurrentFrame();
  const index = Math.min(CARDS.length - 1, Math.floor(frame / CARD));
  const local = frame - index * CARD;
  const card = CARDS[index];
  return (
    <AbsoluteFill style={{background: '#a8a8a6', overflow: 'hidden'}}>
      <Img src={staticFile('tear6-background.webp')} style={{position: 'absolute', inset: 0, width: 1920, height: 1080, objectFit: 'cover', filter: 'brightness(1.05) contrast(0.93) saturate(0.6)'}} />
      <HalfClipping key={index} top={card.top} bottom={card.bottom} local={local} />
    </AbsoluteFill>
  );
};
