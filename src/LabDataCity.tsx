import React from 'react';
import {AbsoluteFill, Easing, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: MONT} = loadFont();
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const DATA = [
  {value: '0.96', label: 'TOKYO FERTILITY · 2025', start: 90, x: 170, y: 320, vx: 90, vy: -110, scale: 1.00, rx: 18, ry: -24, rz: -12, blur: 0.0},
  {value: '+65,219', label: 'TOKYO NET MIGRATION · 2025', start: 115, x: 1030, y: 300, vx: -60, vy: -80, scale: 0.88, rx: 22, ry: -28, rz: -12, blur: 0.5},
  {value: '898K', label: 'TOKYO VACANT HOMES · 2023', start: 140, x: 1290, y: 520, vx: -100, vy: -120, scale: 1.06, rx: 17, ry: -22, rz: -14, blur: 0.0},
  {value: '31.0', label: 'FIRST-TIME MOTHER AGE · JAPAN · 2025', start: 165, x: 330, y: 660, vx: 80, vy: -150, scale: 0.90, rx: 24, ry: -30, rz: -12, blur: 0.4},
  {value: '1.3', label: 'WORKERS PER SENIOR · 2070 SCENARIO', start: 190, x: 870, y: 740, vx: -40, vy: -150, scale: 1.00, rx: 18, ry: -24, rz: -13, blur: 0.0, projection: true},
  {value: '87M', label: 'JAPAN POPULATION · 2070 SCENARIO', start: 215, x: 1390, y: 750, vx: -90, vy: -170, scale: 0.84, rx: 26, ry: -32, rz: -14, blur: 0.7, projection: true},
] as const;

type Datum = (typeof DATA)[number];

const FloatingDatum: React.FC<{item: Datum}> = ({item}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - item.start;
  if (local < 0) return null;

  const enter = spring({frame: local, fps, config: {damping: 17, stiffness: 105, mass: 0.85}});
  const t = local / 270;
  const x = item.x + item.vx * t;
  const y = item.y + 85 * (1 - enter) + item.vy * t;
  const scale = item.scale * (0.68 + 0.32 * enter) * (1 + 0.13 * t);
  const opacity = interpolate(local, [0, 5], [0, 1], clamp);
  const isProjection = 'projection' in item && item.projection;

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        color: '#fff5ec',
        fontFamily: MONT,
        whiteSpace: 'nowrap',
        opacity,
        transform: `translate3d(${x}px, ${y}px, 0) rotateX(${item.rx}deg) rotateY(${item.ry}deg) rotateZ(${item.rz}deg) skewX(-8deg) scale(${scale})`,
        transformOrigin: 'left center',
        filter: `blur(${item.blur}px)`,
        textShadow: '0 0 5px rgba(255,255,255,.9), 0 0 18px rgba(255,102,92,.88), 0 0 42px rgba(255,55,65,.52)',
      }}
    >
      <div style={{fontSize: 116, fontWeight: 900, lineHeight: 0.95, letterSpacing: -4}}>{item.value}</div>
      <div
        style={{
          marginTop: 22,
          fontSize: 19,
          fontWeight: 700,
          letterSpacing: 2.2,
          color: isProjection ? '#ffe78a' : '#ffe9dc',
          borderBottom: isProjection ? '2px dotted rgba(255,231,138,.8)' : undefined,
          paddingBottom: isProjection ? 7 : 0,
          textShadow: '0 0 9px rgba(255,82,68,.75), 0 2px 5px rgba(0,0,0,.75)',
        }}
      >
        {item.label}
      </div>
    </div>
  );
};

const TitleMark: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 15, stiffness: 105}});
  const exit = interpolate(frame, [65, 90], [0, 1], {...clamp, easing: Easing.bezier(0.4, 0, 0.7, 0.2)});
  const scale = (0.65 + 0.35 * enter) * (1 + 0.22 * exit);
  const x = 400 - 210 * exit;
  const y = 250 + 75 * (1 - enter) + 40 * exit;

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        fontFamily: MONT,
        color: '#ffe66d',
        opacity: 1 - exit,
        transform: `translate3d(${x}px, ${y}px, 0) rotateX(20deg) rotateY(-25deg) rotateZ(-10deg) skewX(-7deg) scale(${scale})`,
        transformOrigin: 'left center',
        textShadow: '0 0 6px rgba(255,245,150,.9), 0 0 22px rgba(255,151,52,.95), 0 0 52px rgba(255,69,45,.68)',
      }}
    >
      <div style={{fontSize: 158, fontWeight: 900, lineHeight: 0.9, letterSpacing: -6}}>TOKYO</div>
      <div style={{fontSize: 39, fontWeight: 800, letterSpacing: 7, marginTop: 30}}>CITY IN NUMBERS</div>
      <div style={{fontSize: 22, fontWeight: 600, letterSpacing: 5, marginTop: 24, color: '#fff1c4'}}>DEMOGRAPHY × ECONOMY</div>
    </div>
  );
};

export const LabDataCity: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 359], [1.045, 1.095], clamp);
  const warm = interpolate(frame, [35, 125], [0, 0.28], clamp);

  return (
    <AbsoluteFill style={{background: '#10171b', overflow: 'hidden'}}>
      <OffthreadVideo
        muted
        src={staticFile('lab7-tokyo-aerial.mp4')}
        style={{
          width: 1920,
          height: 1080,
          objectFit: 'cover',
          transform: `scale(${zoom})`,
          filter: 'brightness(.70) saturate(.78) contrast(1.12)',
        }}
      />
      <AbsoluteFill style={{background: 'linear-gradient(135deg, rgba(7,58,61,.32), rgba(15,28,38,.08) 52%, rgba(255,103,74,.13))'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,107,72,.72), rgba(255,65,84,.16) 47%, rgba(8,21,31,.08))', opacity: warm}} />
      <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 43%, transparent 32%, rgba(0,0,0,.43) 100%)'}} />

      <AbsoluteFill style={{perspective: 1100, transformStyle: 'preserve-3d'}}>
        <TitleMark />
        {DATA.map((item) => <FloatingDatum key={item.label} item={item} />)}
      </AbsoluteFill>

      <AbsoluteFill style={{background: 'linear-gradient(180deg, transparent 84%, rgba(0,0,0,.58) 100%)'}} />
      <div style={{position: 'absolute', left: 60, right: 60, bottom: 54, display: 'flex', justifyContent: 'space-between', gap: 30, fontFamily: MONT, fontSize: 17, fontWeight: 600, letterSpacing: 1.2, color: 'rgba(255,255,255,.82)', textShadow: '0 2px 5px #000'}}>
        <div>DATA: MHLW 2025 · MIC 2023/2025 · IPSS 2023 MEDIUM SCENARIO</div>
        <div>AERIAL: ITO JUNICHI / PEXELS · 2020</div>
      </div>
    </AbsoluteFill>
  );
}
