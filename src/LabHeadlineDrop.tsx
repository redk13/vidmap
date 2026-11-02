import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const enterEase = Easing.bezier(0.22, 0.86, 0.24, 1);
const exitEase = Easing.bezier(0.55, 0, 0.9, 0.45);

type BoardProps = {
  title: string;
  color: string;
  source: string;
  holdAtEnd?: boolean;
};

const HeadlineBoard: React.FC<BoardProps> = ({title, color, source, holdAtEnd = false}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 16], [0, 1], {...clamp, easing: enterEase});
  const exit = holdAtEnd ? 0 : interpolate(frame, [82, 99], [0, 1], {...clamp, easing: exitEase});
  const y = -360 + enter * 520 + exit * 1100;
  const scale = 0.975 + enter * 0.025;
  const sourceReveal = interpolate(frame, [7, 21], [0, 1], {...clamp, easing: enterEase});

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 280,
          top: 0,
          width: 1360,
          minHeight: 170,
          boxSizing: 'border-box',
          padding: '34px 46px',
          display: 'flex',
          alignItems: 'center',
          backgroundColor: color,
          color: '#10232d',
          borderRadius: 4,
          boxShadow: '0 24px 72px rgba(0,0,0,0.38)',
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 54,
          fontWeight: 800,
          lineHeight: 1.12,
          letterSpacing: -1.25,
          transform: `translateY(${y}px) scale(${scale})`,
          transformOrigin: '50% 50%',
        }}
      >
        {title}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 90,
          right: 90,
          bottom: 64,
          color: 'rgba(255,255,255,0.92)',
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 20,
          fontWeight: 500,
          letterSpacing: 0.25,
          textAlign: 'center',
          textShadow: '0 2px 12px rgba(0,0,0,0.9)',
          clipPath: `inset(0 ${100 - sourceReveal * 100}% 0 0)`,
          transform: `translateY(${exit * 120}px)`,
        }}
      >
        {source}
      </div>
    </AbsoluteFill>
  );
};

export const LabHeadlineDrop: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 299], [1.04, 1.075], clamp);

  return (
    <AbsoluteFill style={{backgroundColor: '#07131d', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '50% 48%'}}>
        <Img src={staticFile('lab10-finance-bg.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(2,10,18,0.24) 0%, rgba(2,10,18,0.12) 45%, rgba(2,10,18,0.68) 100%)'}} />

      <Sequence from={0} durationInFrames={100}>
        <HeadlineBoard
          title="Central banks worldwide cut interest rates"
          color="#7dd8c5"
          source="Source: Wikinews · 8 Oct 2008 · CC BY 2.5 · en.wikinews.org"
        />
      </Sequence>
      <Sequence from={100} durationInFrames={100}>
        <HeadlineBoard
          title="China to surpass Japan to become second largest economy"
          color="#ff9a8a"
          source="Source: Wikinews · 2 Jan 2010 · CC BY 2.5 · en.wikinews.org"
        />
      </Sequence>
      <Sequence from={200} durationInFrames={100}>
        <HeadlineBoard
          title="Hungary extends fuel price cap"
          color="#a9bfff"
          source="Source: Wikinews · 16 Feb 2022 · CC BY 2.5 · en.wikinews.org"
          holdAtEnd
        />
      </Sequence>
    </AbsoluteFill>
  );
};
