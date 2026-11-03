import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const CENTER_ORDER = [3, 4, 2, 5, 1, 6, 0, 7];

const Sheet: React.FC<{src: string; x: number; y: number; w: number; h: number; p: number; offsetY: number}> = ({src, x, y, w, h, p, offsetY}) => {
  const strips = 8;
  const stripW = w / strips;
  const opacity = interpolate(p, [0, 0.1], [0, 1], clamp);
  const scale = 0.42 + p * 0.58;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity, transform: `translateY(${(1 - p) * offsetY}px) scale(${scale})`, transformOrigin: 'center', perspective: '1150px', transformStyle: 'preserve-3d', filter: 'drop-shadow(0 20px 20px rgba(0,0,0,.46))'}}>
      {Array.from({length: strips}, (_, i) => {
        const rank = CENTER_ORDER.indexOf(i);
        const delay = rank * 0.045;
        const sp = interpolate(p, [delay, 0.55 + delay], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
        const direction = i % 2 === 0 ? -1 : 1;
        return (
          <div key={i} style={{position: 'absolute', left: i * stripW, top: 0, width: stripW, height: h, overflow: 'hidden', backfaceVisibility: 'hidden', transformOrigin: i % 2 === 0 ? 'left center' : 'right center', transform: `translateZ(${(1 - sp) * -105}px) rotateY(${(1 - sp) * direction * 78}deg)`, filter: `brightness(${0.52 + sp * 0.48})`}}>
            <Img src={staticFile(src)} style={{position: 'absolute', left: -i * stripW, top: 0, width: w, height: h, maxWidth: 'none', objectFit: 'fill'}} />
            <div style={{position: 'absolute', inset: 0, background: direction < 0 ? 'linear-gradient(90deg, rgba(0,0,0,.78), rgba(255,255,255,.28))' : 'linear-gradient(90deg, rgba(255,255,255,.28), rgba(0,0,0,.78))', opacity: (1 - sp) * 0.72, pointerEvents: 'none'}} />
          </div>
        );
      })}
    </div>
  );
};

export const LabPaperMorph: React.FC = () => {
  const frame = useCurrentFrame();
  const openP = interpolate(frame, [8, 34, 196, 222], [0, 1, 1, 0], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const appear = Math.min(
    interpolate(frame, [0, 3], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)}),
    interpolate(frame, [222, 225], [1, 0], {...clamp, easing: Easing.in(Easing.cubic)})
  );
  const wadOut = interpolate(openP, [0.16, 0.38], [0, 1], clamp);
  const wadOpacity = appear * (1 - wadOut);
  const halfIn = interpolate(openP, [0.10, 0.28], [0, 1], clamp);
  const halfOut = interpolate(openP, [0.52, 0.74], [0, 1], clamp);
  const halfOpacity = halfIn * (1 - halfOut) * appear;
  const halfScale = 0.34 + interpolate(openP, [0.10, 0.74], [0, 1], clamp) * 0.84;
  const mainP = interpolate(openP, [0.40, 0.90], [0, 1], clamp);
  const stripP = interpolate(openP, [0.50, 1], [0, 1], clamp);

  return (
    <AbsoluteFill style={{backgroundColor: '#0c0e10', overflow: 'hidden'}}>
      <Img src={staticFile('city-bg.jpg')} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(13px) brightness(.64) saturate(.75)', transform: 'scale(1.06)'}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 49%, rgba(222,229,224,${0.08 + openP * 0.10}) 0%, rgba(0,0,0,.12) 46%, rgba(0,0,0,.60) 100%)`}} />
      <Audio src={staticFile('crumple-morph.wav')} volume={1.08} />

      <div style={{position: 'absolute', left: 760, top: 720, width: 400, height: 55, borderRadius: '50%', background: 'rgba(0,0,0,.52)', filter: 'blur(20px)', opacity: wadOpacity * 0.72, transform: `scaleX(${0.55 + appear * 0.45})`}} />

      <div style={{position: 'absolute', left: 760, top: 350, width: 400, height: 369, opacity: wadOpacity, clipPath: `circle(${appear * 76}% at 50% 50%)`, transform: `scale(${(0.35 + appear * 0.65) * (1 + openP * 0.12)})`, transformOrigin: 'center', filter: 'drop-shadow(0 22px 22px rgba(0,0,0,.58))'}}>
        <Img src={staticFile('crump-wad-2d.png')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>

      <div style={{position: 'absolute', left: 410, top: 256, width: 1100, height: 568, opacity: halfOpacity, clipPath: `inset(0 ${50 * (1 - halfIn)}% 0 ${50 * (1 - halfIn)}%)`, transform: `translateY(${(0.5 - openP) * 28}px) rotate(${(openP - 0.4) * 3}deg) scale(${halfScale})`, transformOrigin: 'center', filter: 'drop-shadow(0 24px 24px rgba(0,0,0,.52))'}}>
        <Img src={staticFile('crump-half-2d.png')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>

      <Sheet src="crump-strip-2d.png" x={540} y={140} w={840} h={351.5} p={stripP} offsetY={170} />
      <Sheet src="crump-paper-2d.png" x={420} y={500} w={1080} h={516} p={mainP} offsetY={-245} />
    </AbsoluteFill>
  );
};
