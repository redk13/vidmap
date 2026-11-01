import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {geoMercator, geoPath} from 'd3-geo';
import type {FeatureCollection} from 'geojson';
import tokyo23 from '../data/tokyo23.json';

const CRIM = '#e8273c', INK = '#0a1420', YEL = '#ffd60a', GRN = '#49e07c';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

// ACT 2b — THE TIME SQUEEZE (750f): clock-ring tightens over Tokyo
export const TimeSqueeze: React.FC = () => {
  const f = useCurrentFrame();
  const wards = useMemo(() => {
    const fc = tokyo23 as unknown as FeatureCollection;
    const proj = geoMercator().fitExtent([[700, 120], [1880, 1020]], fc as any);
    const path = geoPath(proj);
    return fc.features.map((x: any) => ({n: x.properties.n, d: path(x) ?? ''}));
  }, []);

  const CX = 1330, CY = 560;
  const ringR = interpolate(f, [80, 700], [300, 150], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const ringOp = interpolate(f, [60, 100], [0, 1], clamp);
  const hand = (f * 3.1) % 360;
  const age = interpolate(f, [330, 460], [25, 31], clamp);
  const mar = Math.round(interpolate(f, [800, 980], [430000, 489119], clamp));
  const slam = interpolate(f, [530, 552], [1.8, 1], {...clamp, easing: Easing.out(Easing.back(1.8))});
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      <svg width={1920} height={1080} style={{position: 'absolute', opacity: 0.3}}>
        {wards.map((w) => <path key={w.n} d={w.d} fill="#223548" stroke="#0e1c2a" strokeWidth={1.5}/>)}
      </svg>

      <svg width={1920} height={1080} style={{position: 'absolute', opacity: ringOp}}>
        <circle cx={CX} cy={CY} r={ringR} fill="rgba(255,214,10,0.05)" stroke={YEL} strokeWidth={5}/>
        {Array.from({length: 12}, (_, i) => {
          const a = (i * 30 * Math.PI) / 180;
          return <line key={i}
            x1={CX + (ringR - 16) * Math.sin(a)} y1={CY - (ringR - 16) * Math.cos(a)}
            x2={CX + ringR * Math.sin(a)} y2={CY - ringR * Math.cos(a)}
            stroke={YEL} strokeWidth={4}/>;
        })}
        <line x1={CX} y1={CY} x2={CX + (ringR - 40) * Math.sin((hand * Math.PI) / 180)}
          y2={CY - (ringR - 40) * Math.cos((hand * Math.PI) / 180)}
          stroke="#fff" strokeWidth={5} strokeLinecap="round"/>
        {/* worker glyph */}
        <g stroke="#cfe6ff" strokeWidth={6} strokeLinecap="round" fill="none">
          <circle cx={CX} cy={CY - 52} r={20} fill="#cfe6ff" stroke="none"/>
          <line x1={CX} y1={CY - 28} x2={CX} y2={CY + 28}/>
          <line x1={CX} y1={CY - 12} x2={CX - 34} y2={CY + 16}/>
          <line x1={CX} y1={CY - 12} x2={CX + 34} y2={CY + 16}/>
          <line x1={CX} y1={CY + 28} x2={CX - 24} y2={CY + 78}/>
          <line x1={CX} y1={CY + 28} x2={CX + 24} y2={CY + 78}/>
          <rect x={CX + 26} y={CY + 8} width={34} height={26} rx={4} fill="#cfe6ff" stroke="none"/>
        </g>
      </svg>

      <div style={{position: 'absolute', top: 56, left: 86, opacity: t(15, 40)}}>
        <div style={{fontSize: 30, fontWeight: 800, color: CRIM, letterSpacing: 4}}>CAUSE #2</div>
        <div style={{fontSize: 62, fontWeight: 900, color: '#fff', lineHeight: 1.02}}>THE TIME<br/>SQUEEZE</div>
      </div>

      <div style={{position: 'absolute', top: 330, left: 86, opacity: t(300, 330)}}>
        <div style={{fontSize: 26, fontWeight: 800, color: '#8fa6bd', letterSpacing: 3}}>AVG FIRST-TIME MOTHER</div>
        <div style={{fontSize: 118, fontWeight: 900, color: YEL, lineHeight: 1}}>AGE {age.toFixed(1)}</div>
      </div>

      <div style={{position: 'absolute', top: 800, left: 86, opacity: t(780, 810)}}>
        <div style={{fontSize: 26, fontWeight: 800, color: '#8fa6bd', letterSpacing: 3}}>MARRIAGES — 2025</div>
        <div style={{fontSize: 86, fontWeight: 900, color: '#fff', lineHeight: 1}}>
          {mar.toLocaleString('en-US')} <span style={{color: GRN, fontSize: 60}}>▲</span>
        </div>
        <div style={{fontSize: 25, fontWeight: 700, color: GRN, marginTop: 8, opacity: t(990, 1015)}}>
          2ND RISE IN A ROW — A FLICKER OF HOPE · still below 599,000 (2019)
        </div>
      </div>

      <div style={{position: 'absolute', top: 560, left: 86, opacity: t(500, 525)}}>
        <div style={{fontSize: 40, fontWeight: 900, color: '#fff'}}>
          FEWER THAN <span style={{color: CRIM}}>3%</span> OF BIRTHS HAPPEN OUTSIDE MARRIAGE
        </div>
        <div style={{display: 'inline-block', marginTop: 14, transform: `scale(${slam})`, transformOrigin: 'left center',
          background: CRIM, borderRadius: 10, padding: '8px 22px', opacity: f > 530 ? 1 : 0}}>
          <span style={{fontSize: 36, fontWeight: 900, color: '#fff'}}>LATE MARRIAGE = LOW FERTILITY</span>
        </div>
      </div>

      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#6d8aa6'}}>
        Sources: MHLW, 2025 · OECD Family Database (2.4%, 2023)
      </div>
    </AbsoluteFill>
  );
};
