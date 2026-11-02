import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const enterEase = Easing.bezier(0.22, 0.86, 0.24, 1);
const BOARD_COLOR = '#7dd8c5';

type GroupProps = {
  title: string;
  published: string;
  slot: number;
  order: number;
  keepCurrent?: boolean;
};

const HeadlineGroup: React.FC<GroupProps> = ({title, published, slot, order, keepCurrent = false}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 18], [0, 1], {...clamp, easing: enterEase});
  const dim = keepCurrent ? 0 : interpolate(frame, [94, 116], [0, 1], clamp);
  const y = -360 + enter * (slot + 360) + dim * 24;
  const scale = (0.98 + enter * 0.02) * (1 - dim * 0.025);

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: '100%',
        height: 250,
        zIndex: 10 + order,
        opacity: 1 - dim * 0.48,
        filter: `blur(${dim * 0.7}px)`,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: '50% 125px',
        fontFamily: 'Arial, Helvetica, sans-serif',
      }}
    >
      <div style={{position: 'absolute', left: 360, top: 0, color: '#fff', fontSize: 44, lineHeight: 1, fontWeight: 700, letterSpacing: -1.2, textShadow: '0 3px 18px rgba(0,0,0,0.55)'}}>
        Wikinews
      </div>
      <div
        style={{
          position: 'absolute',
          left: 330,
          top: 62,
          width: 1260,
          height: 132,
          boxSizing: 'border-box',
          padding: '28px 38px',
          display: 'flex',
          alignItems: 'center',
          backgroundColor: BOARD_COLOR,
          color: '#10232d',
          fontSize: 50,
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: -1.1,
          boxShadow: '0 14px 40px rgba(0,0,0,0.28)',
        }}
      >
        {title}
      </div>
      <div style={{position: 'absolute', right: 360, top: 204, color: 'rgba(255,255,255,0.94)', fontSize: 18, fontWeight: 500, letterSpacing: 0.7, textShadow: '0 2px 12px rgba(0,0,0,0.9)'}}>
        PUBLISHED {published}
      </div>
    </div>
  );
};

export const LabHeadlineDrop: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 299], [1.04, 1.07], clamp);
  const sourceReveal = interpolate(frame, [8, 24], [0, 1], {...clamp, easing: enterEase});

  return (
    <AbsoluteFill style={{backgroundColor: '#07131d', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '50% 48%'}}>
        <Img src={staticFile('lab10-finance-bg.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(2,10,18,0.25) 0%, rgba(2,10,18,0.16) 48%, rgba(2,10,18,0.72) 100%)'}} />

      <Sequence from={0} durationInFrames={300}>
        <HeadlineGroup title="Central banks worldwide cut interest rates" published="October 8, 2008" slot={70} order={0} />
      </Sequence>
      <Sequence from={100} durationInFrames={200}>
        <HeadlineGroup title="Bank of England raises interest rates" published="January 11, 2007" slot={340} order={1} />
      </Sequence>
      <Sequence from={200} durationInFrames={100}>
        <HeadlineGroup title="Hungary extends fuel price cap" published="February 16, 2022" slot={610} order={2} keepCurrent />
      </Sequence>

      <div
        style={{
          position: 'absolute',
          left: 90,
          right: 90,
          bottom: 60,
          color: 'rgba(255,255,255,0.92)',
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 20,
          fontWeight: 500,
          letterSpacing: 0.25,
          textAlign: 'center',
          textShadow: '0 2px 12px rgba(0,0,0,0.9)',
          clipPath: `inset(0 ${100 - sourceReveal * 100}% 0 0)`,
        }}
      >
        Headlines: Wikinews · CC BY 2.5 · en.wikinews.org
      </div>
    </AbsoluteFill>
  );
};
