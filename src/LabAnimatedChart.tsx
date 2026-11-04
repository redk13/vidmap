import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, cancelRender, continueRender, delayRender, interpolate, interpolateColors, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const fontGate = delayRender('Loading Shot 14 local font');
const chartFont = new FontFace('Shot14Montserrat', `url(${staticFile('lab14-Montserrat-Variable.ttf')})`, {weight: '100 900', style: 'normal'});
chartFont.load()
  .then((font) => {
    document.fonts.add(font);
    continueRender(fontGate);
  })
  .catch((error) => cancelRender(error));

const WriteText: React.FC<{start: number; end: number; children: string; style: React.CSSProperties}> = ({start, end, children, style}) => {
  const frame = useCurrentFrame();
  if (frame < start) return null;
  const progress = interpolate(frame, [start, end], [0, 1], {...clamp, easing: Easing.bezier(0.25, 0.02, 0.25, 1)});
  return <div style={{...style, clipPath: `inset(-15% ${100 - progress * 100}% -20% 0)`, whiteSpace: 'nowrap'}}>{children}</div>;
};

const Arrow: React.FC<{start: number; end: number; d: string; tipX: number; tipY: number}> = ({start, end, d, tipX, tipY}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < start) return null;
  const progress = interpolate(frame, [start, end], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const local = frame - end;
  const head = local < 0 ? 0 : spring({frame: local, fps, config: {damping: 13, stiffness: 180}});
  return (
    <g fill="none" stroke="#202321" strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - progress} />
      <path d="M22 -14 L0 0 L22 14" transform={`translate(${tipX} ${tipY}) scale(${head})`} />
    </g>
  );
};

export const LabAnimatedChart: React.FC = () => {
  const frame = useCurrentFrame();
  const BASE = 910;
  const BOTTOM_H = 337;
  const TOP_H = 331;
  const bottomH = interpolate(frame, [20, 75], [0, BOTTOM_H], {...clamp, easing: Easing.out(Easing.cubic)});
  const topH = interpolate(frame, [75, 135], [0, TOP_H], {...clamp, easing: Easing.out(Easing.cubic)});
  const bottomColor = interpolateColors(frame, [60, 85], ['#38a9cc', '#a49b48']);
  const axisProgress = interpolate(frame, [8, 36], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const statSpring = spring({frame: Math.max(0, frame - 210), fps: 30, config: {damping: 14, stiffness: 125, mass: 0.72}});

  return (
    <AbsoluteFill style={{backgroundColor: '#e9e8e1', overflow: 'hidden', fontFamily: 'Shot14Montserrat'}}>
      <Img src={staticFile('lab14-dotted-paper.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <Audio src={staticFile('lab14-chart.wav')} volume={1.1} />

      <WriteText start={0} end={25} style={{position: 'absolute', left: 310, top: 68, width: 1300, textAlign: 'center', fontSize: 55, fontWeight: 800, letterSpacing: -1.7, color: '#111513'}}>
        Investment property owners - Australia
      </WriteText>

      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="axisReveal"><rect x={640} y={290} width={510 * axisProgress} height={640} /></clipPath>
        </defs>
        <g fill="none" stroke="#343834" strokeWidth={2} clipPath="url(#axisReveal)">
          {[320, 468, 615, 763].map((y) => (
            <path key={y} d={`M680 ${y} H1130`} strokeDasharray="1 7" strokeLinecap="round" opacity={0.68} />
          ))}
        </g>
        <path d="M650 910 H1140" pathLength={1} fill="none" stroke="#343834" strokeDasharray={1} strokeDashoffset={1 - axisProgress} strokeWidth={2.6} />
        <rect x={800} y={BASE - bottomH} width={320} height={bottomH} fill={bottomColor} />
        <rect x={800} y={BASE - BOTTOM_H - topH} width={320} height={topH} fill="#c92557" />
      </svg>

      {[['2M', 320], ['1.5M', 468], ['1M', 615], ['500K', 763]].map(([label, y], i) => (
        <WriteText key={label} start={8 + i * 3} end={22 + i * 3} style={{position: 'absolute', left: 565, top: Number(y) - 18, width: 90, textAlign: 'right', fontSize: 24, fontWeight: 500, color: '#303530'}}>
          {label}
        </WriteText>
      ))}
      <WriteText start={30} end={42} style={{position: 'absolute', left: 880, top: 928, width: 160, textAlign: 'center', fontSize: 28, fontWeight: 750, color: '#202421'}}>People</WriteText>

      <WriteText start={84} end={99} style={{position: 'absolute', left: 800, top: 720, width: 320, textAlign: 'center', fontSize: 34, fontWeight: 750, color: '#ffffff'}}>1.14M</WriteText>
      <WriteText start={137} end={151} style={{position: 'absolute', left: 800, top: 385, width: 320, textAlign: 'center', fontSize: 34, fontWeight: 750, color: '#ffffff'}}>1.12M</WriteText>
      <WriteText start={140} end={158} style={{position: 'absolute', left: 730, top: 168, width: 460, textAlign: 'center', fontSize: 43, fontWeight: 800, letterSpacing: -1, color: '#38a9cc'}}>2.26 million</WriteText>

      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <Arrow start={158} end={174} d="M1370 425 C1305 410 1235 410 1150 425" tipX={1150} tipY={425} />
        <Arrow start={184} end={200} d="M1370 760 C1305 748 1235 748 1150 760" tipX={1150} tipY={760} />
      </svg>
      <WriteText start={172} end={190} style={{position: 'absolute', left: 1400, top: 395, width: 390, fontSize: 31, fontWeight: 750, color: '#c92557'}}>Negatively geared</WriteText>
      <WriteText start={198} end={216} style={{position: 'absolute', left: 1400, top: 730, width: 350, fontSize: 31, fontWeight: 750, color: '#a49b48'}}>Neutral/profit</WriteText>

      <div style={{position: 'absolute', left: 320, top: 380, width: 430, color: '#111513', transform: `translateY(${(1 - statSpring) * 20}px) scale(${0.92 + statSpring * 0.08})`, transformOrigin: 'left center'}}>
        <WriteText start={210} end={224} style={{fontSize: 43, fontWeight: 450, lineHeight: 1.1}}>Over</WriteText>
        <WriteText start={218} end={238} style={{fontSize: 138, fontWeight: 850, lineHeight: 1.05, letterSpacing: -7}}>$10</WriteText>
        <WriteText start={230} end={246} style={{fontSize: 57, fontWeight: 450, lineHeight: 1.1, letterSpacing: -1.5}}>billion</WriteText>
      </div>

      <div style={{position: 'absolute', left: 60, bottom: 34, fontSize: 17, fontWeight: 500, lineHeight: 1.45, color: 'rgba(30,35,31,.56)'}}>
        <div>Source: ATO Taxation Statistics 2022-23</div>
        <div>The Conversation · 2025</div>
      </div>
    </AbsoluteFill>
  );
};
