import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, cancelRender, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const fontGate = delayRender('Loading Shot 15 local font');
const neonFont = new FontFace('Shot15Montserrat', `url(${staticFile('lab14-Montserrat-Variable.ttf')})`, {weight: '100 900', style: 'normal'});
neonFont.load().then((font) => {document.fonts.add(font); continueRender(fontGate);}).catch((error) => cancelRender(error));

const WriteText: React.FC<{start: number; end: number; children: string; style: React.CSSProperties}> = ({start, end, children, style}) => {
  const frame = useCurrentFrame();
  if (frame < start) return null;
  const progress = interpolate(frame, [start, end], [0, 1], clamp);
  return <div style={{...style, clipPath: `inset(-18% ${100 - progress * 100}% -22% 0)`, whiteSpace: 'nowrap'}}>{children}</div>;
};

const NeonFrame: React.FC<{x: number; y: number; start: number; title: string; subtitle: string}> = ({x, y, start, title, subtitle}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < start) return null;
  const local = frame - start;
  const enter = spring({frame: local, fps, config: {damping: 13, stiffness: 155, mass: 0.7}});
  const opacity = interpolate(local, [0, 5], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: 500, height: 220, opacity, transform: `translateY(${(1 - enter) * 24}px) scale(${0.76 + enter * 0.24})`, transformOrigin: 'center'}}>
      <Img src={staticFile('lab15-neon-frame.png')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', filter: 'drop-shadow(0 0 12px rgba(255,177,44,.48))'}} />
      <div style={{position: 'absolute', inset: '48px 40px 38px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, color: '#fffdf5', textAlign: 'center', textShadow: '0 2px 4px rgba(0,0,0,.82), 0 0 9px rgba(0,0,0,.42)'}}>
        <WriteText start={start + 10} end={start + 27} style={{fontSize: 41, fontWeight: 800, lineHeight: 1.08, letterSpacing: -1}}>{title}</WriteText>
        <WriteText start={start + 20} end={start + 36} style={{fontSize: 23, fontWeight: 500, lineHeight: 1.15, color: '#fff8e7'}}>{subtitle}</WriteText>
      </div>
    </div>
  );
};

const Arrow: React.FC<{id: string; start: number; end: number; d: string; tip: [number, number]; angle: number; direction: 'right' | 'down' | 'left' | 'up'}> = ({id, start, end, d, tip, angle, direction}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < start) return null;
  const progress = interpolate(frame, [start, end], [0, 1], clamp);
  const head = spring({frame: Math.max(0, frame - end), fps, config: {damping: 12, stiffness: 190}});
  const clip = direction === 'right'
    ? {x: 815, y: 195, width: 290 * progress, height: 145}
    : direction === 'down'
      ? {x: 1230, y: 350, width: 200, height: 315 * progress}
      : direction === 'left'
        ? {x: 1105 - 290 * progress, y: 680, width: 290 * progress, height: 145}
        : {x: 490, y: 660 - 315 * progress, width: 200, height: 315 * progress};
  return (
    <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
      <defs>
        <clipPath id={`${id}-reveal`}><rect {...clip} /></clipPath>
        <filter id={`${id}-glow`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <g clipPath={`url(#${id}-reveal)`} filter={`url(#${id}-glow)`}>
        <path d={d} fill="none" stroke="#58f4e4" strokeWidth={5} strokeLinecap="round" strokeDasharray="14 18" />
      </g>
      {frame >= end ? (
        <g transform={`translate(${tip[0]} ${tip[1]}) rotate(${angle}) scale(${head})`} filter={`url(#${id}-glow)`}>
          <path d="M-22 -14 L0 0 L-22 14" fill="none" stroke="#58f4e4" strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      ) : null}
    </svg>
  );
};

export const LabNeonFrames: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#071014', overflow: 'hidden', fontFamily: 'Shot15Montserrat'}}>
      <OffthreadVideo src={staticFile('lab15-sea-clouds.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(.58) saturate(.7) blur(1.2px)', transform: 'scale(1.015)'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(2,10,15,.12), rgba(2,10,15,.34))'}} />
      <Audio src={staticFile('lab15-neon.wav')} volume={1.1} />

      <NeonFrame x={340} y={150} start={0} title="Evaporation" subtitle="Water becomes vapor" />
      <Arrow id="arrow-one" start={32} end={48} d="M840 265 C920 220 1000 220 1080 265" tip={[1080, 265]} angle={25} direction="right" />
      <NeonFrame x={1080} y={150} start={50} title="Condensation" subtitle="Clouds form" />
      <Arrow id="arrow-two" start={82} end={98} d="M1330 370 C1380 450 1380 560 1330 640" tip={[1330, 640]} angle={120} direction="down" />
      <NeonFrame x={1080} y={640} start={100} title="Precipitation" subtitle="Rain, snow or hail" />
      <Arrow id="arrow-three" start={132} end={148} d="M1080 755 C1000 800 920 800 840 755" tip={[840, 755]} angle={-150} direction="left" />
      <NeonFrame x={340} y={640} start={150} title="Collection" subtitle="Rivers & oceans" />
      <Arrow id="arrow-four" start={182} end={200} d="M590 640 C540 560 540 450 590 370" tip={[590, 370]} angle={-60} direction="up" />

      <div style={{position: 'absolute', left: 60, bottom: 30, fontSize: 16, fontWeight: 500, lineHeight: 1.45, color: 'rgba(239,248,245,.68)', textShadow: '0 1px 4px rgba(0,0,0,.8)'}}>
        <div>Source: USGS Water Science School · The Water Cycle</div>
        <div>Background: Salva F. Ayala / Pexels · 14548015</div>
      </div>
    </AbsoluteFill>
  );
};
