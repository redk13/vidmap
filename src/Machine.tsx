import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {geoMercator, geoPath} from 'd3-geo';
import type {FeatureCollection} from 'geojson';
import tokyo23 from '../data/tokyo23.json';
import {JapanMap} from './JapanMap';

const CRIM = '#e8273c', INK = '#0a1420', YEL = '#ffd60a', RED = '#c2283a', BLUE = '#2f86ff';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const BH16 = ['Shinjuku','Bunkyo','Taito','Sumida','Shinagawa','Meguro','Ota','Setagaya','Shibuya','Nakano','Suginami','Toshima','Kita','Arakawa','Itabashi','Nerima'];

const qb = (p0: number[], c: number[], p1: number[], t: number) => [
  (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
  (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1],
];

// ACT 2c — THE MACHINE ITSELF + BLACK HOLE payoff (1200f)
export const Machine: React.FC = () => {
  const f = useCurrentFrame();
  const wards = useMemo(() => {
    const fc = tokyo23 as unknown as FeatureCollection;
    const proj = geoMercator().fitExtent([[640, 130], [1860, 1000]], fc as any);
    const path = geoPath(proj);
    return fc.features.map((x: any) => ({n: x.properties.n, d: path(x) ?? '', c: path.centroid(x) as [number, number]}));
  }, []);

  const japanOp = interpolate(f, [1540, 1590], [1, 0], clamp);
  const wardsOp = interpolate(f, [1570, 1620], [0, 1], clamp);
  const wave = interpolate(f, [1250, 1510], [0, 47], clamp); // 744 flash wave over prefectures
  const grayT = interpolate(f, [700, 1200], [0, 30], clamp); // towns gray out
  const cnt744 = Math.round(interpolate(f, [1255, 1500], [0, 744], clamp));
  const cnt16 = Math.round(interpolate(f, [1840, 2080], [0, 16], clamp));
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);
  const stamp = interpolate(f, [1620, 1642], [2.2, 1], {...clamp, easing: Easing.out(Easing.cubic)});

  const styleFor = (id: number) => {
    if (id === 13) return {fill: BLUE, glow: true, stroke: '#bcd9ff', strokeWidth: 2};
    const waveIdx = ((id * 11) % 47);
    if (f > 1240 && waveIdx < wave && f < 1540) return {fill: RED};
    const gOrder = (id * 7) % 47;
    if (gOrder < grayT) return {fill: '#16202b'};
    return {fill: '#2b4156'};
  };

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      {japanOp > 0 && (
        <div style={{position: 'absolute', inset: 0, opacity: japanOp}}>
          <JapanMap width={1920} height={1080} styleFor={styleFor} okinawaInset={false}>
            {(centroidOf) => {
              const A = centroidOf(5);  // Akita — the rural town
              const T = centroidOf(13);
              const C = [(A[0] + T[0]) / 2 + 160, (A[1] + T[1]) / 2 - 120];
              const fl = interpolate(f, [180, 420], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
              const P = qb(A, C, T, fl);
              const baseLoss = interpolate(f, [300, 500], [1, 0.25], clamp);
              const els: React.ReactNode[] = [];
              if (f > 60 && f < 1540) {
                // dotted pull-arrow
                const dots = [];
                for (let i = 0; i <= 20; i++) {
                  const q = qb(A, C, T, i / 20);
                  dots.push(<circle key={i} cx={q[0]} cy={q[1]} r={3.5} fill="#9cc4ff" opacity={i / 20 < fl ? 0.7 : 0.18}/>);
                }
                els.push(<g key="dots">{dots}</g>);
                // young-person glyph travelling
                if (fl > 0 && fl < 1) els.push(
                  <g key="girl" transform={`translate(${P[0]} ${P[1]})`}>
                    <circle cx={0} cy={-26} r={13} fill="#ffd9a0"/>
                    <path d="M -14 24 L 0 -12 L 14 24 Z" fill="#ff8093"/>
                  </g>
                );
                // town mini-pyramid: base drains
                const bx = A[0] - 150, by = A[1] - 60;
                els.push(
                  <g key="tp" opacity={t(60, 85)}>
                    <text x={bx + 55} y={by - 16} textAnchor="middle" fontSize={22} fontWeight={800} fill="#8fa6bd">A RURAL TOWN</text>
                    {[70, 86, 96, 82, 60].map((w, i) => (
                      <rect key={i} x={bx + 55 - (i === 4 ? w * baseLoss : w) / 2} y={by + i * 17}
                        width={i === 4 ? w * baseLoss : w} height={13} rx={3}
                        fill={i === 4 ? CRIM : '#5e7purple'.slice(0,0) || '#5e7a96'}/>
                    ))}
                  </g>
                );
                // Tokyo mini-pyramid: mid bars fat, base thin — barely moves
                const gx = T[0] + 120, gy = T[1] - 40;
                els.push(
                  <g key="kp" opacity={t(60, 85)}>
                    <text x={gx + 55} y={gy - 16} textAnchor="middle" fontSize={22} fontWeight={800} fill="#8fa6bd">TOKYO</text>
                    {[60, 96, 116 + 14 * (1 - baseLoss), 70, 34].map((w, i) => (
                      <rect key={i} x={gx + 55 - w / 2} y={gy + i * 17} width={w} height={13} rx={3}
                        fill={i === 2 ? YEL : '#5e7a96'}/>
                    ))}
                  </g>
                );
              }
              return <g>{els}</g>;
            }}
          </JapanMap>
        </div>
      )}

      {wardsOp > 0 && (
        <svg width={1920} height={1080} style={{position: 'absolute', opacity: wardsOp}}>
          {wards.map((w, i) => {
            const bhIdx = BH16.indexOf(w.n);
            const on = bhIdx >= 0 && bhIdx < cnt16;
            return <path key={w.n} d={w.d}
              fill={on ? '#05070c' : '#2b4156'}
              stroke={on ? CRIM : '#0e1c2a'} strokeWidth={on ? 2.5 : 1.5}/>;
          })}
          {['Shinjuku', 'Shibuya', 'Setagaya'].map((n) => {
            const w = wards.find((x) => x.n === n)!;
            const idx = BH16.indexOf(n);
            return idx < cnt16 ? (
              <text key={n} x={w.c[0]} y={w.c[1] + 6} textAnchor="middle" fontSize={21} fontWeight={900} fill="#ff8093">
                {n.toUpperCase()}
              </text>
            ) : null;
          })}
        </svg>
      )}

      <div style={{position: 'absolute', top: 56, left: 86, opacity: t(15, 40) * japanOp}}>
        <div style={{fontSize: 30, fontWeight: 800, color: CRIM, letterSpacing: 4}}>CAUSE #3</div>
        <div style={{fontSize: 62, fontWeight: 900, color: '#fff', lineHeight: 1.02}}>THE MACHINE<br/>ITSELF</div>
      </div>

      {f > 1240 && f < 1560 && (
        <div style={{position: 'absolute', top: 430, left: 86, opacity: t(1250, 1275)}}>
          <div style={{fontSize: 110, fontWeight: 900, color: '#fff', lineHeight: 1}}>{cnt744}</div>
          <div style={{fontSize: 28, fontWeight: 800, color: RED, letterSpacing: 2, marginTop: 6}}>
            OF 1,729 MUNICIPALITIES "AT RISK"
          </div>
          <div style={{fontSize: 20, color: '#8fa6bd', marginTop: 6}}>Population Strategy Council — a private panel · Apr 2024</div>
        </div>
      )}

      {f > 1615 && (
        <div style={{position: 'absolute', top: 70, left: 86, transform: `scale(${stamp}) rotate(-6deg)`,
          transformOrigin: 'left top'}}>
          <div style={{border: '6px solid ' + CRIM, borderRadius: 10, padding: '10px 28px', background: 'rgba(255,255,255,0.96)'}}>
            <div style={{fontSize: 54, fontWeight: 900, color: CRIM, letterSpacing: 2}}>BLACK HOLE</div>
          </div>
        </div>
      )}
      {f > 1850 && (
        <div style={{position: 'absolute', top: 260, left: 86, opacity: t(1850, 1875)}}>
          <div style={{fontSize: 96, fontWeight: 900, color: '#fff', lineHeight: 1}}>{cnt16}<span style={{color: '#8fa6bd', fontSize: 60}}> / 23</span></div>
          <div style={{fontSize: 27, fontWeight: 800, color: '#ff8093', letterSpacing: 2, marginTop: 4}}>TOKYO WARDS LABELED</div>
          <div style={{fontSize: 27, fontWeight: 800, color: '#ff8093', letterSpacing: 2}}>"BLACK-HOLE TYPE"</div>
          <div style={{fontSize: 21, color: '#8fa6bd', marginTop: 14, lineHeight: 1.5}}>
            25 nationwide — 16 of them in Tokyo<br/>High inflow of the young, ultra-low fertility<br/>Chair: Akio Mimura · a PRIVATE council, not the government
          </div>
        </div>
      )}
      {f > 2440 && (
        <div style={{position: 'absolute', bottom: 120, left: 86, width: 560, background: '#fff', borderRadius: 12,
          padding: '16px 24px', opacity: t(2440, 2465)}}>
          <div style={{fontSize: 24, fontWeight: 900, color: INK}}>BUT — RIETI RESEARCHERS PUSH BACK:</div>
          <div style={{fontSize: 22, fontWeight: 700, color: '#44546a', marginTop: 4}}>the method and the labels oversimplify</div>
        </div>
      )}
      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#6d8aa6'}}>
        Source: Population Strategy Council report, Apr 2024 · RIETI commentary
      </div>
    </AbsoluteFill>
  );
};
