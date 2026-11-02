import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, cancelRender, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const fontGate = delayRender('Loading Shot 13 local fonts');
const fontFaces = [
  new FontFace('Shot13Kalam', `url(${staticFile('lab13-Kalam-Bold.ttf')})`, {weight: '700', style: 'normal'}),
  new FontFace('Shot13Montserrat', `url(${staticFile('lab13-Montserrat-Italic.ttf')})`, {weight: '100 900', style: 'italic'}),
];
Promise.all(fontFaces.map((font) => font.load()))
  .then((loaded) => {
    loaded.forEach((font) => document.fonts.add(font));
    continueRender(fontGate);
  })
  .catch((error) => cancelRender(error));

const WritingText: React.FC<{
  start: number;
  end: number;
  children: string;
  style: React.CSSProperties;
}> = ({start, end, children, style}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [start, end], [0, 1], {...clamp, easing: Easing.bezier(0.28, 0.02, 0.32, 1)});
  if (frame < start) return null;
  return (
    <div
      style={{
        ...style,
        clipPath: `inset(-12% ${100 - progress * 100}% -18% 0)`,
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </div>
  );
};

export const LabPaperWriting: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const settle = spring({frame, fps, config: {damping: 15, stiffness: 105, mass: 0.72}});
  const subtitleLift = spring({frame: Math.max(0, frame - 98), fps, config: {damping: 17, stiffness: 115, mass: 0.65}});

  return (
    <AbsoluteFill style={{backgroundColor: '#111b18', overflow: 'hidden'}}>
      <Img src={staticFile('lab13-chalkboard.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <Audio src={staticFile('lab13-writing.wav')} volume={0.8} />

      <div
        style={{
          position: 'absolute',
          left: 300,
          top: 210,
          width: 930,
          height: 270,
          transform: `translateY(${(1 - settle) * -24}px) rotate(${(1 - settle) * -1.15}deg) scale(${0.965 + settle * 0.035})`,
          transformOrigin: '50% 58%',
        }}
      >
        <Img src={staticFile('lab13-note-cutout.png')} style={{position: 'absolute', inset: 0, width: 930, height: 270}} />
        <WritingText
          start={20}
          end={85}
          style={{
            position: 'absolute',
            left: 175,
            top: 108,
            width: 610,
            fontFamily: 'Shot13Kalam',
            fontWeight: 700,
            fontSize: 66,
            lineHeight: 1.08,
            letterSpacing: -1.1,
            color: '#101817',
          }}
        >
          Negative Gearing:
        </WritingText>
      </div>

      <WritingText
        start={102}
        end={154}
        style={{
          position: 'absolute',
          left: 395,
          top: 535 + (1 - subtitleLift) * 12,
          width: 1260,
          fontFamily: 'Shot13Montserrat',
          fontStyle: 'italic',
          fontWeight: 500,
          fontSize: 50,
          lineHeight: 1.15,
          letterSpacing: -1.15,
          color: '#f1f1e9',
          textShadow: '0 2px 6px rgba(0,0,0,.38)',
        }}
      >
        An Australian tax strategy for property investors.
      </WritingText>

      <div style={{position: 'absolute', left: 60, bottom: 28, fontFamily: 'Shot13Montserrat', fontStyle: 'italic', fontWeight: 400, fontSize: 15, color: 'rgba(240,240,230,.42)'}}>
        Original generated paper &amp; chalkboard assets · Shot Lab 13
      </div>
    </AbsoluteFill>
  );
};
