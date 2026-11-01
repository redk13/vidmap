import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {geoMercator, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import tokyo23 from '../data/tokyo23.json';
import {JapanMap} from './JapanMap';

const CRIM = '#e8273c', INK = '#0a1420', YEL = '#ffd60a', BLUE = '#2f86ff', GRY = '#8fa6bd';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const ease = Easing.inOut(Easing.cubic);
const OUT = 800; // phase 2: zoom back out (vo/06 starts here)

// ACT 2a — SPACE SQUEEZE (1673f): dive to Shinjuku, then zoom out to empty Japan
export const Dive: React.FC = () => {
  const f = useCurrentFrame();
  const W = 1920, H = 1080;

  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    for (const ft of fc.features) {
      const p: any = ft;
      if (p.properties.id === 13 && p.geometry.type === 'MultiPolygon') {
        let best = p.geometry.coordinates[0];
        for (const poly of p.geometry.coordinates) {
          if (JSON.stringify(poly).length > JSON.stringify(best).length) best = poly;
        }
        p.geometry = {type: 'Polygon', coordinates: best};
      }
    }
    const mainFc = {type: 'FeatureCollection', features: fc.features.filter((x: any) => x.properties.id !== 47)} as FeatureCollection;
    const proj = geoMercator().fitExtent([[W * 0.10, H * 0.07], [W * 0.96, H * 0.95]], mainFc as any);
    const path = geoPath(proj);
    const tokyoF: any = fc.features.find((x: any) => x.properties.id === 13);
    const T = path.centroid(tokyoF) as [number, number];
    const wfc = tokyo23 as unknown as FeatureCollection;
    const projW = geoMercator().fitExtent([[220, 90], [1700, 1010]], wfc as any);
    const pathW = geoPath(projW);
    const shin: any = wfc.features.find((x: any) => (x as any).properties.n === 'Shinjuku');
    const S = pathW.centroid(shin) as [number, number];
    const wards = wfc.features.map((x: any) => ({n: x.properties.n, d: pathW(x) ?? ''}));
    return {T, S, wards};
  }, []);

  // phase 1: dive in
  const z = interpolate(f, [40, 330], [0, 1], {...clamp, easing: ease});
  const s1 = 1 + z * 6;
  const japanOp1 = interpolate(f, [300, 360], [1, 0], clamp);
  const g2 = interpolate(f, [290, 430], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const s2 = 0.35 + 0.65 * g2;
  const wardsIn = interpolate(f, [290, 340], [0, 1], clamp);
  const pulse = (f % 55) / 55;
  const shinOn = f > 470 && f < OUT;
  const slam = (t0: number) => ({
    opacity: interpolate(f, [t0, t0 + 12], [0, 1], clamp),
    scale: interpolate(f, [t0, t0 + 22], [1.6, 1], {...clamp, easing: Easing.out(Easing.back(1.8))}),
  });
  const c1 = slam(560), c2 = slam(640), c3 = slam(715);
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);

  // phase 2: zoom back out — empty Japan
  const out = t(OUT, OUT + 70);
  const wardsOp = wardsIn * (1 - out);
  const phase1Ui = 1 - t(OUT - 20, OUT + 30);
  const cnt9 = (interpolate(f, [OUT + 100, OUT + 260], [0, 9.0], clamp)).toFixed(1);
  const abOn = f > OUT + 370;
  const houses = 26;

  const styleFor = (id: number) => {
    if (f >= OUT) {
      if (id === 13) return {fill: BLUE, stroke: '#9cc4ff', strokeWidth: 1.5};
      const gray = ((id * 7) % 47) / 47;
      return {fill: gray < t(OUT + 60, OUT + 500) ? '#141f2b' : '#243748'};
    }
    if (id === 13) return {fill: BLUE, glow: true, stroke: '#bcd9ff', strokeWidth: 2.5};
    return {fill: '#203346'};
  };

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      {(japanOp1 > 0 || out > 0) && (
        <div style={{position: 'absolute', inset: 0, opacity: Math.max(japanOp1, out),
          transformOrigin: `${M.T[0]}px ${M.T[1]}px`,
          transform: f < OUT
            ? `translate(${(960 - M.T[0]) * z}px, ${(540 - M.T[1]) * z}px) scale(${s1})`
            : `translate(${(960 - M.T[0]) * (1 - out) * 1}px, ${(540 - M.T[1]) * (1 - out)}px) scale(${1 + 6 * (1 - out)})`}}>
          <JapanMap width={W} height={H} styleFor={styleFor} okinawaInset={false}>
            {(centroidOf) => {
              if (f < OUT + 60) return null;
              const ids = [1, 2, 3, 5, 6, 7, 9, 15, 16, 17, 20, 24, 29, 30, 31, 32, 33, 36, 38, 39, 41, 43, 44, 45, 46, 18];
              return (
                <g>
                  {ids.slice(0, houses).map((id, i) => {
                    const on = t(OUT + 120 + i * 14, OUT + 140 + i * 14);
                    if (on <= 0) return null;
                    const [cx, cy] = centroidOf(id);
                    const red = abOn && i % 3 === 0;
                    return (
                      <g key={id} opacity={on} transform={`translate(${cx} ${cy - 14 * on})`}>
                        <path d="M -14 0 L 0 -14 L 14 0 L 14 16 L -14 16 Z"
                          fill={red ? CRIM : '#5e7a96'} stroke="#0a1420" strokeWidth={2}/>
                      </g>
                    );
                  })}
                </g>
              );
            }}
          </JapanMap>
        </div>
      )}

      {wardsOp > 0 && (
        <svg width={W} height={H} style={{position: 'absolute', top: 0, left: 0, opacity: wardsOp,
          transformOrigin: `${M.S[0]}px ${M.S[1]}px`, transform: `scale(${s2 * (1 + out * 0.8)})`}}>
          {M.wards.map((w) => (
            <path key={w.n} d={w.d}
              fill={w.n === 'Shinjuku' ? (f > 470 ? YEL : '#2b4156') : '#2b4156'}
              stroke={w.n === 'Shinjuku' && f > 470 ? '#fff' : '#0e1c2a'}
              strokeWidth={w.n === 'Shinjuku' && f > 470 ? 3 : 1.5}/>
          ))}
          {shinOn && (
            <g>
              <circle cx={M.S[0]} cy={M.S[1]} r={18 + 70 * pulse} fill="none" stroke={YEL}
                strokeWidth={3.5 * (1 - pulse)} opacity={1 - pulse}/>
              <line x1={M.S[0]} y1={M.S[1] - 16} x2={M.S[0] + 60} y2={M.S[1] - 120} stroke="#fff" strokeWidth={3}/>
              <rect x={M.S[0] + 60} y={M.S[1] - 180} rx={12} width={280} height={60} fill="#fff"/>
              <text x={M.S[0] + 200} y={M.S[1] - 138} textAnchor="middle" fontSize={33} fontWeight={900} fill={INK}>SHINJUKU</text>
            </g>
          )}
        </svg>
      )}

      {f > 490 && phase1Ui > 0 && (
        <div style={{position: 'absolute', top: 56, left: 86, opacity: t(490, 515) * phase1Ui}}>
          <div style={{fontSize: 30, fontWeight: 800, color: CRIM, letterSpacing: 4}}>CAUSE #1</div>
          <div style={{fontSize: 62, fontWeight: 900, color: '#fff', lineHeight: 1.02}}>THE SPACE<br/>SQUEEZE</div>
        </div>
      )}
      {phase1Ui > 0 && [{c: c1, y: 700, txt: 'TINY APARTMENTS', w: 420},
        {c: c2, y: 790, txt: 'COMMUTES CAN EAT NEARLY 2 HOURS A DAY', w: 760},
        {c: c3, y: 880, txt: "SOME OF JAPAN'S MOST EXPENSIVE SQUARE METERS", w: 860}].map((k, i) => (
        <div key={i} style={{position: 'absolute', top: k.y, right: 60, width: k.w, height: 64,
          background: '#fff', borderRadius: 12, opacity: k.c.opacity * phase1Ui,
          transform: `scale(${k.c.scale})`, transformOrigin: 'right center',
          display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <span style={{fontSize: 29, fontWeight: 900, color: INK, whiteSpace: 'nowrap'}}>{k.txt}</span>
        </div>
      ))}

      {f > OUT + 80 && (
        <div style={{position: 'absolute', top: 56, left: 86, opacity: t(OUT + 80, OUT + 110)}}>
          <div style={{fontSize: 44, fontWeight: 900, color: '#fff', lineHeight: 1.05}}>
            MEANWHILE, THE REST OF JAPAN<br/><span style={{color: CRIM}}>IS EMPTYING OUT</span>
          </div>
          <div style={{marginTop: 26}}>
            <span style={{fontSize: 110, fontWeight: 900, color: '#fff', lineHeight: 1}}>{cnt9}M</span>
            <span style={{fontSize: 32, fontWeight: 900, color: YEL}}>  VACANT HOMES — 13.8%</span>
          </div>
          <div style={{fontSize: 34, fontWeight: 900, color: '#ff8093', marginTop: 10, opacity: t(OUT + 370, OUT + 395)}}>
            3.86M FULLY ABANDONED
          </div>
          <div style={{fontSize: 26, fontWeight: 800, color: GRY, marginTop: 10, opacity: t(OUT + 500, OUT + 525)}}>
            SOME SELL FOR UNDER $10,000
          </div>
          <div style={{display: 'inline-block', background: '#fff', borderRadius: 12, padding: '10px 24px',
            marginTop: 18, opacity: t(OUT + 620, OUT + 645)}}>
            <span style={{fontSize: 28, fontWeight: 900, color: INK}}>MORE HOMES THAN HOUSEHOLDS</span>
          </div>
        </div>
      )}
      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#6d8aa6'}}>
        {f < OUT ? '' : 'Source: MIC Housing and Land Survey, 2023'}
      </div>
    </AbsoluteFill>
  );
};
