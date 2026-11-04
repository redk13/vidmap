import React from 'react';
import {AbsoluteFill, Easing, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, delayRender, continueRender, cancelRender} from 'remotion';
const registerLocalFont = (family: string, file: string, weight = '400 900') => {
  const handle = delayRender(`Loading local font: ${family}`);
  const face = new FontFace(family, `url("${staticFile(file)}")`, {style: 'normal', weight});
  face.load().then((loaded) => {
    document.fonts.add(loaded);
    continueRender(handle);
  }).catch(cancelRender);
};

registerLocalFont('Montserrat', 'Montserrat-Variable.ttf');
const MONT = 'Montserrat';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const glow = '0 0 5px rgba(255,255,255,.85), 0 0 18px rgba(255,102,92,.82), 0 0 40px rgba(255,55,65,.45)';

const FloatingElement: React.FC<{
  start: number;
  end: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  rx: number;
  ry: number;
  rz: number;
  children: (local: number) => React.ReactNode;
}> = ({start, end, x, y, vx, vy, rx, ry, rz, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - start;
  if (local < 0 || frame > end) return null;

  const enter = spring({frame: local, fps, config: {damping: 17, stiffness: 105, mass: 0.85}});
  const exit = interpolate(frame, [end - 22, end], [0, 1], {...clamp, easing: Easing.bezier(0.4, 0, 0.7, 0.2)});
  const t = local / (end - start);
  const px = x + vx * t + 55 * (1 - enter) - 45 * exit;
  const py = y + vy * t + 65 * (1 - enter) - 30 * exit;
  const scale = (0.80 + 0.20 * enter) * (1 + 0.055 * t - 0.06 * exit);
  const opacity = interpolate(local, [0, 5], [0, 1], clamp) * (1 - exit);

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        fontFamily: MONT,
        color: '#fff5ec',
        opacity,
        transform: `translate3d(${px}px, ${py}px, 0) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg) skewX(-2deg) scale(${scale})`,
        transformOrigin: 'left top',
        textShadow: glow,
      }}
    >
      {children(local)}
    </div>
  );
};

const Label: React.FC<{children: React.ReactNode; projection?: boolean}> = ({children, projection}) => (
  <div
    style={{
      fontSize: 19,
      fontWeight: 750,
      letterSpacing: 2.1,
      color: projection ? '#ffe78a' : '#ffe9dc',
      borderBottom: projection ? '2px dotted rgba(255,231,138,.85)' : undefined,
      paddingBottom: projection ? 7 : 0,
      textShadow: '0 0 9px rgba(255,82,68,.7), 0 2px 5px rgba(0,0,0,.8)',
    }}
  >
    {children}
  </div>
);

const FertilityNumber: React.FC = () => (
  <div style={{width: 600, whiteSpace: 'nowrap'}}>
    <div style={{fontSize: 126, fontWeight: 900, lineHeight: 0.95, letterSpacing: -5}}>0.96</div>
    <div style={{marginTop: 24}}><Label>TOKYO FERTILITY · 2025</Label></div>
  </div>
);

const PopulationBars: React.FC<{local: number}> = ({local}) => {
  const growNow = spring({frame: local, fps: 30, config: {damping: 18, stiffness: 95}});
  const growFuture = spring({frame: Math.max(0, local - 8), fps: 30, config: {damping: 18, stiffness: 95}});
  const maxHeight = 235;
  const futureRatio = 87 / 126.15;

  return (
    <div style={{width: 610}}>
      <Label projection>JAPAN POPULATION · IPSS MEDIUM</Label>
      <div style={{height: 330, display: 'flex', alignItems: 'flex-end', gap: 72, borderBottom: '2px solid rgba(255,255,255,.55)', padding: '0 34px', marginTop: 20}}>
        <div style={{width: 150, textAlign: 'center'}}>
          <div style={{fontSize: 35, fontWeight: 850, marginBottom: 12}}>126.15M</div>
          <div style={{height: maxHeight * growNow, minHeight: 2, background: 'linear-gradient(180deg,#fff3e8,#ff766e)', boxShadow: '0 0 24px rgba(255,105,96,.7)'}} />
          <div style={{fontSize: 23, fontWeight: 750, letterSpacing: 2, marginTop: 14}}>2020</div>
        </div>
        <div style={{width: 150, textAlign: 'center'}}>
          <div style={{fontSize: 35, fontWeight: 850, marginBottom: 12, color: '#ffe78a'}}>87M</div>
          <div style={{height: maxHeight * futureRatio * growFuture, minHeight: 2, background: 'rgba(255,231,138,.13)', border: '3px dotted #ffe78a', boxSizing: 'border-box', boxShadow: '0 0 24px rgba(255,213,92,.4)'}} />
          <div style={{fontSize: 21, fontWeight: 750, letterSpacing: 1.2, marginTop: 14, color: '#ffe78a'}}>2070 SCENARIO</div>
        </div>
      </div>
    </div>
  );
};

const WorkerDots: React.FC<{local: number}> = ({local}) => {
  const dotRow = (count: number, row: number, color: string) => (
    <div style={{display: 'flex', gap: 12, height: 36, alignItems: 'center'}}>
      {Array.from({length: count}, (_, i) => {
        const enter = spring({frame: Math.max(0, local - row * 9 - i * 1.1), fps: 30, config: {damping: 15, stiffness: 120}});
        return <span key={i} style={{width: 25, height: 25, borderRadius: '50%', background: color, opacity: enter, transform: `scale(${0.25 + 0.75 * enter})`, boxShadow: `0 0 15px ${color}`}} />;
      })}
    </div>
  );

  return (
    <div style={{width: 650}}>
      <Label projection>WORKING-AGE PEOPLE PER SENIOR · 2070 SCENARIO</Label>
      <div style={{display: 'flex', alignItems: 'center', gap: 30, marginTop: 28}}>
        <div style={{fontSize: 70, fontWeight: 900, color: '#ffe78a', letterSpacing: -3}}>1.3</div>
        <div style={{display: 'grid', gap: 22}}>
          {dotRow(13, 0, '#8ef5ef')}
          {dotRow(10, 1, '#ffe78a')}
        </div>
      </div>
      <div style={{display: 'flex', gap: 58, marginTop: 20, fontSize: 18, fontWeight: 700, letterSpacing: 2}}>
        <span style={{color: '#8ef5ef'}}>13 WORKING-AGE</span>
        <span style={{color: '#ffe78a'}}>10 SENIORS</span>
      </div>
    </div>
  );
};

const AgeGauge: React.FC<{local: number}> = ({local}) => {
  const lineGrow = spring({frame: local, fps: 30, config: {damping: 19, stiffness: 100}});
  const marker = spring({frame: Math.max(0, local - 8), fps: 30, config: {damping: 14, stiffness: 110}});
  const ticks = [28, 29, 30, 31, 32, 33, 34];

  return (
    <div style={{width: 720}}>
      <Label>FIRST-TIME MOTHER · JAPAN · 2025</Label>
      <div style={{height: 95, display: 'flex', alignItems: 'flex-end', justifyContent: 'center'}}>
        <div style={{fontSize: 76, fontWeight: 900, color: '#fff5ec', opacity: marker, transform: `translateY(${28 * (1 - marker)}px)`}}>31.0</div>
      </div>
      <div style={{position: 'relative', width: 630, height: 92, marginLeft: 22}}>
        <div style={{position: 'absolute', left: 0, top: 20, height: 3, width: 630 * lineGrow, background: '#fff5ec', boxShadow: glow}} />
        {ticks.map((tick, i) => (
          <div key={tick} style={{position: 'absolute', left: i * 105, top: 10, textAlign: 'center', transform: 'translateX(-50%)'}}>
            <div style={{height: tick === 31 ? 30 : 20, width: tick === 31 ? 4 : 2, background: tick === 31 ? '#ffe78a' : '#fff5ec', margin: '0 auto'}} />
            <div style={{fontSize: 18, fontWeight: tick === 31 ? 850 : 600, marginTop: 10, color: tick === 31 ? '#ffe78a' : '#fff5ec'}}>{tick}</div>
          </div>
        ))}
        <div style={{position: 'absolute', left: 315, top: -14, width: 4, height: 70, background: '#ffe78a', boxShadow: '0 0 20px #ffd75e', opacity: marker, transform: `scaleY(${marker})`, transformOrigin: 'bottom'}} />
      </div>
    </div>
  );
};

const MigrationFlow: React.FC<{local: number}> = ({local}) => (
  <div style={{width: 900}}>
    <div style={{display: 'flex', alignItems: 'baseline', gap: 30}}>
      <div style={{fontSize: 96, fontWeight: 900, letterSpacing: -4, whiteSpace: 'nowrap'}}>+65,219</div>
      <Label>TOKYO NET MIGRATION · 2025</Label>
    </div>
    <svg width="850" height="150" viewBox="0 0 850 150" style={{overflow: 'visible', marginTop: 18}}>
      <g fill="none" stroke="#ff9e91" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" style={{filter: 'drop-shadow(0 0 9px rgba(255,91,84,.9))'}}>
        {[0, 1, 2, 3, 4].map((i) => {
          const pulse = 0.32 + 0.68 * (0.5 + 0.5 * Math.sin(local / 4.5 - i * 0.95));
          return <path key={i} d={`M ${55 + i * 92} 35 L ${100 + i * 92} 75 L ${55 + i * 92} 115`} opacity={pulse} />;
        })}
      </g>
      <circle cx="715" cy="75" r="57" fill="rgba(255,231,138,.09)" stroke="#ffe78a" strokeWidth="4" strokeDasharray="5 9" style={{filter: 'drop-shadow(0 0 12px rgba(255,220,90,.65))'}} />
      <text x="715" y="83" textAnchor="middle" fill="#fff5ec" fontFamily={MONT} fontSize="23" fontWeight="800" letterSpacing="1">TOKYO</text>
    </svg>
  </div>
);

const TitleMark: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 15, stiffness: 105}});
  const exit = interpolate(frame, [35, 55], [0, 1], {...clamp, easing: Easing.bezier(0.4, 0, 0.7, 0.2)});
  const scale = (0.72 + 0.28 * enter) * (1 + 0.12 * exit);
  const x = 400 - 150 * exit;
  const y = 235 + 60 * (1 - enter) + 25 * exit;

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        fontFamily: MONT,
        color: '#ffe66d',
        opacity: 1 - exit,
        transform: `translate3d(${x}px, ${y}px, 0) rotateX(10deg) rotateY(-12deg) rotateZ(-5deg) skewX(-3deg) scale(${scale})`,
        transformOrigin: 'left top',
        textShadow: '0 0 6px rgba(255,245,150,.9), 0 0 22px rgba(255,151,52,.9), 0 0 48px rgba(255,69,45,.6)',
      }}
    >
      <div style={{fontSize: 150, fontWeight: 900, lineHeight: 0.9, letterSpacing: -6}}>TOKYO</div>
      <div style={{fontSize: 38, fontWeight: 800, letterSpacing: 7, marginTop: 28}}>CITY IN NUMBERS</div>
      <div style={{fontSize: 22, fontWeight: 600, letterSpacing: 5, marginTop: 22, color: '#fff1c4'}}>DEMOGRAPHY × ECONOMY</div>
    </div>
  );
};

export const LabDataCity: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 359], [1.045, 1.085], clamp);
  const warm = interpolate(frame, [35, 125], [0, 0.25], clamp);

  return (
    <AbsoluteFill style={{background: '#10171b', overflow: 'hidden'}}>
      <OffthreadVideo
        muted
        src={staticFile('lab7-tokyo-aerial.mp4')}
        style={{width: 1920, height: 1080, objectFit: 'cover', transform: `scale(${zoom})`, filter: 'brightness(.70) saturate(.78) contrast(1.12)'}}
      />
      <AbsoluteFill style={{background: 'linear-gradient(135deg, rgba(7,58,61,.30), rgba(15,28,38,.08) 52%, rgba(255,103,74,.12))'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,107,72,.65), rgba(255,65,84,.14) 47%, rgba(8,21,31,.08))', opacity: warm}} />
      <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 43%, transparent 32%, rgba(0,0,0,.43) 100%)'}} />

      <AbsoluteFill style={{perspective: 1400, transformStyle: 'preserve-3d'}}>
        <TitleMark />
        <FloatingElement start={50} end={120} x={190} y={300} vx={45} vy={-45} rx={8} ry={-10} rz={-4}>
          {() => <FertilityNumber />}
        </FloatingElement>
        <FloatingElement start={105} end={175} x={1120} y={250} vx={-35} vy={-35} rx={9} ry={-11} rz={-4}>
          {(local) => <PopulationBars local={local} />}
        </FloatingElement>
        <FloatingElement start={160} end={230} x={200} y={465} vx={40} vy={-40} rx={8} ry={-10} rz={-4}>
          {(local) => <WorkerDots local={local} />}
        </FloatingElement>
        <FloatingElement start={215} end={285} x={980} y={605} vx={-35} vy={-45} rx={9} ry={-12} rz={-5}>
          {(local) => <AgeGauge local={local} />}
        </FloatingElement>
        <FloatingElement start={270} end={359} x={330} y={270} vx={45} vy={-35} rx={8} ry={-10} rz={-4}>
          {(local) => <MigrationFlow local={local} />}
        </FloatingElement>
      </AbsoluteFill>

      <AbsoluteFill style={{background: 'linear-gradient(180deg, transparent 84%, rgba(0,0,0,.58) 100%)'}} />
      <div style={{position: 'absolute', left: 60, right: 60, bottom: 54, display: 'flex', justifyContent: 'space-between', gap: 30, fontFamily: MONT, fontSize: 17, fontWeight: 600, letterSpacing: 1.2, color: 'rgba(255,255,255,.82)', textShadow: '0 2px 5px #000'}}>
        <div>DATA: MHLW 2025 · MIC 2025 · IPSS 2023 MEDIUM SCENARIO</div>
        <div>AERIAL: ITO JUNICHI / PEXELS · 2020</div>
      </div>
    </AbsoluteFill>
  );
};
