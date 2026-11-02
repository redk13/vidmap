import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const LabSpotlightDoc: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 299], [1, 1.015], clamp);
  const dim = interpolate(frame, [20, 56], [0.22, 0.82], {...clamp, easing: Easing.bezier(0.4, 0, 0.2, 1)});
  const spot = interpolate(frame, [26, 60], [0, 0.98], {...clamp, easing: Easing.bezier(0.4, 0, 0.2, 1)});
  const sweep = interpolate(frame, [72, 104], [0, 1], {...clamp, easing: Easing.bezier(0.45, 0, 0.2, 1)});

  // Geometry exported by build_lab8_document.py. The transparent content image
  // contains only the yellow stroke and its original black ink.
  const clipLeft = 548;
  const clipWidth = 1010;
  const clipRight = 1920 - (clipLeft + clipWidth * sweep);
  const highlightClip = `inset(768px ${clipRight}px 244px ${clipLeft}px)`;
  const pageTransform = `scale(${zoom})`;

  return (
    <AbsoluteFill style={{backgroundColor: '#020303', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: pageTransform, transformOrigin: '55% 74%'}}>
        <Img src={staticFile('lab8-document-clean.webp')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080}} />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background: 'radial-gradient(ellipse 900px 370px at 55% 74%, rgba(0,0,0,0) 0%, rgba(0,0,0,.07) 42%, rgba(0,0,0,.72) 100%)',
          opacity: dim,
        }}
      />
      <AbsoluteFill style={{backgroundColor: '#000', opacity: dim * 0.10}} />

      {/* Strong, compact light isolates the exact target line before the yellow
          appears. Keeping it below the highlight preserves the printed ink. */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(ellipse 650px 105px at 55% 74%, rgba(255,255,255,.78) 0%, rgba(255,255,255,.42) 45%, rgba(255,255,255,0) 80%)',
          mixBlendMode: 'screen',
          opacity: spot,
        }}
      />
      <AbsoluteFill style={{transform: pageTransform, transformOrigin: '55% 74%'}}>
        <Img src={staticFile('lab8-highlight-content.png')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, clipPath: highlightClip}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
