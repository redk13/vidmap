import React from 'react';
import {AbsoluteFill, Easing, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const SCREEN = {x: 566, y: 217, w: 789, h: 508};

type EpisodeProps = {title: string; kicker: string; video: string; credit: string};

const ScreenEpisode: React.FC<EpisodeProps> = ({title, kicker, video, credit}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 14], [0, 1], {...clamp, easing: Easing.bezier(0.4, 0, 0.2, 1)});
  const titleEnter = interpolate(frame, [3, 18], [0, 1], {...clamp, easing: Easing.bezier(0.2, 0.8, 0.2, 1)});
  const progress = Math.min(1, frame / 119);

  return (
    <AbsoluteFill style={{backgroundColor: '#f7f7f5', clipPath: `inset(0 ${100 - enter * 100}% 0 0)`}}>
      <div style={{height: '28%', padding: '20px 30px 12px', boxSizing: 'border-box', color: '#111', fontFamily: 'Arial, Helvetica, sans-serif'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, fontWeight: 700, letterSpacing: 1.6, color: '#666'}}>
          <span style={{width: 24, height: 5, backgroundColor: '#e5c529', display: 'inline-block'}} />
          {kicker}
        </div>
        <div style={{fontSize: 36, lineHeight: 1.06, fontWeight: 800, letterSpacing: -1.1, marginTop: 14, transform: `translateY(${16 * (1 - titleEnter)}px)`}}>
          {title}
        </div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: '28%', bottom: 0, overflow: 'hidden', backgroundColor: '#111'}}>
        <OffthreadVideo src={staticFile(video)} muted style={{width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.025)'}} />
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: '30px 22px 12px', background: 'linear-gradient(transparent, rgba(0,0,0,0.72))', color: '#fff', fontSize: 13, fontFamily: 'Arial, Helvetica, sans-serif'}}>
          Footage: {credit} / Pexels
        </div>
        <div style={{position: 'absolute', left: 0, bottom: 0, height: 4, width: `${progress * 100}%`, backgroundColor: '#e5c529'}} />
      </div>
    </AbsoluteFill>
  );
};

export const LabLaptopVideos: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = 1.06 + 0.04 * Math.min(1, frame / 359);

  return (
    <AbsoluteFill style={{backgroundColor: '#77736c', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '50% 52%'}}>
        <AbsoluteFill style={{left: SCREEN.x, top: SCREEN.y, width: SCREEN.w, height: SCREEN.h, overflow: 'hidden', borderRadius: 8, backgroundColor: '#f7f7f5'}}>
          <Sequence from={0} durationInFrames={132}>
            <ScreenEpisode title="Inside an Automated Factory" kicker="VIDEO 01 / AUTOMATION" video="lab9-factory.mp4" credit="Pixabay" />
          </Sequence>
          <Sequence from={120} durationInFrames={132}>
            <ScreenEpisode title="Inside a High-Speed Rail Station" kicker="VIDEO 02 / TRANSIT" video="lab9-train.mp4" credit="Marc Curtis" />
          </Sequence>
          <Sequence from={240} durationInFrames={120}>
            <ScreenEpisode title="Above a Field of Solar Panels" kicker="VIDEO 03 / ENERGY" video="lab9-solar.mp4" credit="K" />
          </Sequence>
        </AbsoluteFill>
        <Img src={staticFile('lab9-laptop.png')} style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
