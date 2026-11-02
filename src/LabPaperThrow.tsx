import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const pageStyle: React.CSSProperties = {position: 'absolute', left: 0, top: 0, width: 720, height: 920};

export const LabPaperThrow: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const first = spring({frame, fps, config: {damping: 16, stiffness: 78, mass: 0.9}});
  const second = spring({frame: Math.max(0, frame - 28), fps, config: {damping: 16, stiffness: 78, mass: 0.9}});
  const light = interpolate(frame, [86, 122], [0, 1], {...clamp, easing: Easing.bezier(0.4, 0, 0.2, 1)});
  const sweep = interpolate(frame, [138, 171], [0, 1], {...clamp, easing: Easing.bezier(0.45, 0, 0.2, 1)});

  const firstTransform = `translate3d(${250 - 950 * (1 - first)}px, ${90 - 800 * (1 - first)}px, 0) rotate(${-7 - 25 * (1 - first)}deg)`;
  const secondTransform = `translate3d(${800 + 900 * (1 - second)}px, ${60 - 850 * (1 - second)}px, 0) rotate(${5 + 25 * (1 - second)}deg)`;

  const clipLeft = 55;
  const clipWidth = 540;
  const clipRight = 720 - (clipLeft + clipWidth * sweep);
  const highlightClip = `inset(560px ${clipRight}px 304px ${clipLeft}px)`;

  return (
    <AbsoluteFill style={{backgroundColor: '#050505', overflow: 'hidden'}}>
      <Img src={staticFile('lab8-desk.webp')} style={{position: 'absolute', width: 1920, height: 1080, filter: `brightness(${1 - 0.28 * light})`}} />

      {/* First printed sheet is thrown onto the desk and stays there. */}
      <AbsoluteFill style={{transform: firstTransform, transformOrigin: 'center center'}}>
        <Img src={staticFile('lab8-paper1.png')} style={{...pageStyle, transform: 'translate(16px, 22px)', filter: 'brightness(0) blur(12px)', opacity: 0.42}} />
        <Img src={staticFile('lab8-paper1.png')} style={{...pageStyle, filter: `brightness(${1 - 0.34 * light})`}} />
      </AbsoluteFill>

      {/* The second sheet falls over the first after it has begun to settle. */}
      {frame >= 28 ? (
        <AbsoluteFill style={{transform: secondTransform, transformOrigin: 'center center'}}>
          <Img src={staticFile('lab8-paper2-clean.png')} style={{...pageStyle, transform: 'translate(16px, 22px)', filter: 'brightness(0) blur(12px)', opacity: 0.46}} />
          <Img src={staticFile('lab8-paper2-clean.png')} style={{...pageStyle, opacity: 1 - light}} />
          <Img src={staticFile('lab8-paper2-lit.png')} style={{...pageStyle, opacity: light}} />
          <Img src={staticFile('lab8-highlight-content.png')} style={{...pageStyle, clipPath: highlightClip}} />
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
