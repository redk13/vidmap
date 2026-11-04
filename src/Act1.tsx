import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {JapanMap} from './JapanMap';

const RED = '#c2283a', CRIM = '#e8273c', BLUE = '#2f86ff', INK = '#0a1420', GREY = '#1d2b3a', YEL = '#ffd60a';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const FLIP = 770; // frame where migration view flips to fertility view

const qbez = (p0: [number, number], c: [number, number], p1: [number, number], t: number): [number, number] => [
  (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
  (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1],
];

// ACT 1 — THE PARADOX (1500 frames): arrows → fertility flip
export const Act1: React.FC = () => {
  const f = useCurrentFrame();
  const W = 1920, H = 1080;
  const mig = interpolate(f, [FLIP - 60, FLIP], [1, 0], clamp);        // migration layer presence
  const fert = interpolate(f, [FLIP, FLIP + 80], [0, 1], clamp);       // fertility layer presence
  const counter = Math.round(interpolate(f, [90, 600], [0, 65219], clamp));
  const pulse = (f % 50) / 50;

  const styleFor = (id: number) => {
    if (fert > 0) {
      if (id === 13) return {fill: `rgba(232,39,60,${0.45 + 0.55 * fert})`, glow: fert > 0.7, stroke: '#ff8a98', strokeWidth: 3};
      if (id === 47) return {fill: `rgba(47,134,255,${0.3 + 0.7 * fert})`, glow: fert > 0.7, stroke: '#9cc4ff', strokeWidth: 2.5};
      return {fill: GREY};
    }
    if (id === 13) return {fill: BLUE, glow: true, stroke: '#bcd9ff', strokeWidth: 2.5};
    return {fill: '#2b4156'};
  };

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      <JapanMap width={W} height={H} styleFor={styleFor}>
        {(centroidOf) => {
          const T = centroidOf(13);
          const els: React.ReactNode[] = [];
          if (mig > 0) {
            for (let id = 1; id <= 46; id++) {
              if (id === 13) continue;
              const S = centroidOf(id === 13 ? 14 : id);
              const mx = (S[0] + T[0]) / 2, my = (S[1] + T[1]) / 2;
              const dx = T[0] - S[0], dy = T[1] - S[1];
              const len = Math.hypot(dx, dy) || 1;
              const bend = ((id % 2 === 0 ? 1 : -1) * (40 + (id * 13) % 60));
              const C: [number, number] = [mx - (dy / len) * bend, my + (dx / len) * bend];
              const grow = interpolate(f, [80 + id * 4, 170 + id * 4], [0, 1], clamp);
              if (grow <= 0) continue;
              const pts: string[] = [];
              const steps = 26;
              for (let i = 0; i <= steps * grow; i++) {
                const [x, y] = qbez(S, C, T, i / steps);
                pts.push(`${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`);
              }
              els.push(<path key={`a${id}`} d={pts.join(' ')} fill="none" stroke="#7fb4e8"
                strokeWidth={2.2} opacity={0.5 * mig} strokeLinecap="round"/>);
              // flowing particle
              const pt = ((f * 0.013 + id * 0.11) % 1) * grow;
              const [px, py] = qbez(S, C, T, pt);
              els.push(<circle key={`p${id}`} cx={px} cy={py} r={4} fill="#cfe6ff" opacity={0.9 * mig}/>);
            }
            els.push(
              <g key="trunk" opacity={mig * interpolate(f, [430, 460], [0, 1], clamp)}>
                <rect x={T[0] + 60} y={T[1] + 40} rx={12} width={540} height={62} fill={YEL}/>
                <text x={T[0] + 330} y={T[1] + 83} textAnchor="middle" fontSize={34} fontWeight={900} fill={INK}>
                  BIGGEST GROUP: AGE 20–24
                </text>
              </g>
            );
          }
          if (fert > 0.5) {
            els.push(
              <g key="tok" opacity={interpolate(f, [FLIP + 100, FLIP + 130], [0, 1], clamp)}>
                <circle cx={T[0]} cy={T[1]} r={46} fill={CRIM} opacity={0.22}/>
                <circle cx={T[0]} cy={T[1]} r={26} fill={CRIM} opacity={0.35}/>
                <circle cx={T[0]} cy={T[1]} r={14 + 60 * pulse} fill="none" stroke={CRIM} strokeWidth={3.5 * (1 - pulse)} opacity={1 - pulse}/>
                <circle cx={T[0]} cy={T[1]} r={14 + 60 * ((pulse + 0.5) % 1)} fill="none" stroke={CRIM} strokeWidth={3.5 * (1 - (pulse + 0.5) % 1)} opacity={1 - (pulse + 0.5) % 1}/>
                <line x1={T[0] + 12} y1={T[1] - 12} x2={T[0] + 92} y2={T[1] - 86} stroke="#fff" strokeWidth={3}/>
                <rect x={T[0] + 92} y={T[1] - 146} rx={12} width={520} height={62} fill={CRIM}/>
                <text x={T[0] + 352} y={T[1] - 103} textAnchor="middle" fontSize={34} fontWeight={900} fill="#fff">
                  TOKYO 0.96 — THE LOWEST
                </text>
              </g>
            );
            const O = centroidOf(47);
            els.push(
              <g key="oki" opacity={interpolate(f, [FLIP + 160, FLIP + 190], [0, 1], clamp)}>
                <line x1={O[0]} y1={O[1] - 30} x2={O[0]} y2={O[1] - 268} stroke="#fff" strokeWidth={3}/>
                <rect x={O[0] - 160} y={O[1] - 330} rx={12} width={560} height={62} fill={BLUE}/>
                <text x={O[0] + 120} y={O[1] - 287} textAnchor="middle" fontSize={34} fontWeight={900} fill="#fff">
                  OKINAWA 1.52 — THE HIGHEST
                </text>
              </g>
            );
          }
          return <g>{els}</g>;
        }}
      </JapanMap>

      {mig > 0 && (
        <div style={{position: 'absolute', top: 64, left: 86, opacity: mig}}>
          <div style={{fontSize: 96, fontWeight: 900, color: '#fff', lineHeight: 1}}>
            +{counter.toLocaleString('en-US')}
          </div>
          <div style={{fontSize: 30, fontWeight: 700, color: YEL, letterSpacing: 3, marginTop: 10}}>
            NET MOVES INTO TOKYO — 2025
          </div>
          <div style={{fontSize: 21, color: '#8fa6bd', marginTop: 6}}>
            Slower than 2024 — still #1 of all prefectures · Source: MIC, 2026
          </div>
        </div>
      )}

      {fert > 0 && (
        <div style={{position: 'absolute', top: 64, left: 86, opacity: fert}}>
          <div style={{fontSize: 64, fontWeight: 900, color: '#fff', lineHeight: 1.05}}>
            NOW FLIP THE MAP:<br/><span style={{color: CRIM}}>FERTILITY</span>
          </div>
          <div style={{display: 'inline-block', marginTop: 22, background: '#fff', borderRadius: 12, padding: '10px 26px'}}>
            <span style={{fontSize: 40, fontWeight: 900, color: INK}}>JAPAN 1.14 </span>
            <span style={{fontSize: 26, fontWeight: 700, color: CRIM}}> — 10TH RECORD LOW IN A ROW</span>
          </div>
          <div style={{fontSize: 21, color: '#8fa6bd', marginTop: 10}}>Source: MHLW, 2026</div>
        </div>
      )}
    </AbsoluteFill>
  );
};
