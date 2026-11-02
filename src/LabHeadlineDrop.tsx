import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: MONT} = loadFont();
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const enterEase = Easing.bezier(0.22, 0.86, 0.24, 1);
const BOARD_COLOR = '#7dd8c5';

type GroupProps = {
  publisher: string;
  publisherWeight: number;
  title: string;
  published: string;
  slot: number;
  order: number;
  keepCurrent?: boolean;
};

const HeadlineGroup: React.FC<GroupProps> = ({publisher, publisherWeight, title, published, slot, order, keepCurrent = false}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 18], [0, 1], {...clamp, easing: enterEase});
  const dim = keepCurrent ? 0 : interpolate(frame, [94, 116], [0, 1], clamp);
  const y = -370 + enter * (slot + 370) + dim * 24;
  const scale = (0.98 + enter * 0.02) * (1 - dim * 0.025);

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: '100%',
        height: 244,
        zIndex: 10 + order,
        opacity: 1 - dim * 0.48,
        filter: `blur(${dim * 0.7}px)`,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: '50% 122px',
        fontFamily: MONT,
      }}
    >
      <div style={{position: 'absolute', left: 440, top: 0, color: '#fff', fontSize: 60, lineHeight: 1, fontWeight: publisherWeight, letterSpacing: -2.2, textShadow: '0 3px 18px rgba(0,0,0,0.55)'}}>
        {publisher}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 440,
          top: 72,
          width: 1040,
          height: 136,
          boxSizing: 'border-box',
          padding: '18px 26px',
          display: 'flex',
          alignItems: 'center',
          backgroundColor: BOARD_COLOR,
          color: '#111c2b',
          fontSize: 45,
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: -1.15,
          whiteSpace: 'pre-line',
          boxShadow: '0 14px 40px rgba(0,0,0,0.28)',
        }}
      >
        {title}
      </div>
      <div style={{position: 'absolute', right: 440, top: 218, color: 'rgba(255,255,255,0.94)', textAlign: 'right', textShadow: '0 2px 12px rgba(0,0,0,0.9)', whiteSpace: 'nowrap'}}>
        <span style={{fontSize: 18, fontWeight: 400, letterSpacing: 0.45}}>PUBLISHED </span>
        <span style={{fontSize: 20, fontWeight: 700, letterSpacing: -0.2}}>{published}</span>
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
        <HeadlineGroup publisher="Wikinews" publisherWeight={500} title={'Central banks worldwide\ncut interest rates'} published="October 8, 2008" slot={40} order={0} />
      </Sequence>
      <Sequence from={100} durationInFrames={200}>
        <HeadlineGroup publisher="Global Voices" publisherWeight={800} title={"Chinese President's Ambitious\nXiongan Dream Sparks Skepticism"} published="April 16, 2017" slot={330} order={1} />
      </Sequence>
      <Sequence from={200} durationInFrames={100}>
        <HeadlineGroup publisher="SciDev.Net" publisherWeight={700} title={'Study breaks down Nigerian\nsolar power failure'} published="January 19, 2016" slot={620} order={2} keepCurrent />
      </Sequence>

      <div
        style={{
          position: 'absolute',
          left: 70,
          right: 70,
          bottom: 48,
          color: 'rgba(255,255,255,0.92)',
          fontFamily: MONT,
          fontSize: 16,
          fontWeight: 500,
          letterSpacing: 0,
          textAlign: 'center',
          textShadow: '0 2px 12px rgba(0,0,0,0.9)',
          clipPath: `inset(0 ${100 - sourceReveal * 100}% 0 0)`,
        }}
      >
        Wikinews · CC BY 2.5 · en.wikinews.org  |  Global Voices / Jack Hu · CC BY 3.0 · globalvoices.org  |  SciDev.Net / Adole Abutu · CC BY 3.0 · scidev.net
      </div>
    </AbsoluteFill>
  );
};
