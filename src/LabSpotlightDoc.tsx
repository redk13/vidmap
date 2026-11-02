import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const LabSpotlightDoc: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 299], [1.09, 1.115], clamp);
  const dim = interpolate(frame, [20, 56], [0.18, 0.76], {...clamp, easing: Easing.bezier(0.4, 0, 0.2, 1)});
  const spot = interpolate(frame, [26, 60], [0, 0.72], {...clamp, easing: Easing.bezier(0.4, 0, 0.2, 1)});
  const sweep = interpolate(frame, [72, 104], [0, 1], {...clamp, easing: Easing.bezier(0.45, 0, 0.2, 1)});

  // Geometry exported by build_lab8_document.py. The transparent content image
  // contains only the yellow stroke and its original black ink, so the sweep
  // preserves letters without a rectangular page overlay or blend-mode loss.
  const clipLeft = 445;
  const clipWidth = 950;
  const clipRight = 1920 - (clipLeft + clipWidth * sweep);
  const highlightClip = `inset(724px ${clipRight}px 296px ${clipLeft}px)`;
  const pageTransform = `scale(${zoom})`;

  return (
    <AbsoluteFill style={{backgroundColor: '#020303', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: pageTransform, transformOrigin: '52% 68%'}}>
        <Img src={staticFile('lab8-document-clean.webp')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080}} />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          background: 'radial-gradient(ellipse 850px 390px at 52% 68%, rgba(0,0,0,0) 0%, rgba(0,0,0,.05) 44%, rgba(0,0,0,.64) 100%)',
          opacity: dim,
        }}
      />
      <AbsoluteFill style={{backgroundColor: '#000', opacity: dim * 0.09}} />

      {/* Keep the yellow above the dimming layer, as in the bright reference,
          but below the soft spotlight so it still belongs to the same light. */}
      <AbsoluteFill style={{transform: pageTransform, transformOrigin: '52% 68%'}}>
        <Img src={staticFile('lab8-highlight-content.png')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, clipPath: highlightClip}} />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: 'radial-gradient(ellipse 700px 280px at 52% 68%, rgba(255,255,255,.28) 0%, rgba(255,255,255,.11) 46%, rgba(255,255,255,0) 78%)',
          mixBlendMode: 'screen',
          opacity: spot,
        }}
      />
    </AbsoluteFill>
  );
};
