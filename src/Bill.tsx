import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {JapanMap} from './JapanMap';

const CRIM = '#e8273c', INK = '#0a1420', YEL = '#ffd60a', BLUE = '#2f86ff', GRY = '#8fa6bd';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const Person: React.FC<{x: number; y: number; s?: number; color: string; cane?: boolean; frac?: number}> =
({x, y, s = 1, color, cane, frac = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <defs>
      <clipPath id={`pc${x}${y}`}><rect x={-40} y={80 - 160 * frac} width={80} height={160 * frac}/></clipPath>
    </defs>
    <g clipPath={frac < 1 ? `url(#pc${x}${y})` : undefined} stroke={color} strokeWidth={9} strokeLinecap="round" fill="none">
      <circle cx={0} cy={-52} r={22} fill={color} stroke="none"/>
      <line x1={0} y1={-24} x2={0} y2={30}/>
      <line x1={0} y1={-8} x2={-30} y2={20}/>
      <line x1={0} y1={-8} x2={30} y2={20}/>
      <line x1={0} y1={30} x2={-22} y2={78}/>
      <line x1={0} y1={30} x2={22} y2={78}/>
      {cane && <line x1={34} y1={10} x2={44} y2={78} stroke={GRY}/>}
    </g>
  </g>
);

// ACT 3 — THE BILL (1200f): dependency -> IPSS milestones -> akiya breakdown
export const Bill: React.FC = () => {
  const f = useCurrentFrame();
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);
  const pA = 1 - t(470, 510), pB = t(490, 530) * (1 - t(1130, 1170)), pC = t(1150, 1190);
  const ratio = interpolate(f, [150, 400], [2.1, 1.3], {...clamp, easing: Easing.inOut(Easing.quad)});
  const year = Math.round(interpolate(f, [150, 400], [2020, 2070], clamp));
  const slam = (t0: number) => interpolate(f, [t0, t0 + 20], [1.7, 1], {...clamp, easing: Easing.out(Easing.back(1.7))});
  const bar = (t0: number) => interpolate(f, [t0, t0 + 40], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});

  const full = Math.floor(ratio), frac = ratio - full;
  const styleFor = () => ({fill: '#1a2938'});

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      <div style={{position: 'absolute', inset: 0, opacity: 0.25}}>
        <JapanMap width={1920} height={1080} styleFor={styleFor} okinawaInset={false}/>
      </div>
      <div style={{position: 'absolute', top: 56, left: 86}}>
        <div style={{fontSize: 30, fontWeight: 800, color: CRIM, letterSpacing: 4, opacity: t(10, 35)}}>ACT 3</div>
        <div style={{fontSize: 62, fontWeight: 900, color: '#fff', lineHeight: 1.02, opacity: t(10, 35)}}>THE BILL</div>
      </div>

      {pA > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pA}}>
          <svg width={1920} height={1080}>
            {Array.from({length: full}, (_, i) => (
              <Person key={i} x={660 + i * 170} y={560} color={BLUE}/>
            ))}
            {frac > 0.02 && <Person x={660 + full * 170} y={560} color={BLUE} frac={frac}/>}
            <Person x={1330} y={552} s={1.08} color="#d9e4ee" cane/>
            <line x1={1180} y1={430} x2={1180} y2={700} stroke="#33475c" strokeWidth={3} strokeDasharray="8 10"/>
          </svg>
          <div style={{position: 'absolute', top: 250, left: 86}}>
            <div style={{fontSize: 26, fontWeight: 800, color: GRY, letterSpacing: 3}}>WORKERS PER SENIOR (65+)</div>
            <div style={{fontSize: 120, fontWeight: 900, color: ratio < 1.6 ? CRIM : '#fff', lineHeight: 1}}>{ratio.toFixed(1)}</div>
            <div style={{fontSize: 44, fontWeight: 900, color: YEL}}>{year}</div>
          </div>
          <div style={{position: 'absolute', top: 760, left: 480, border: '3px dashed ' + GRY, borderRadius: 12,
            padding: '10px 24px', opacity: t(130, 160)}}>
            <span style={{fontSize: 24, fontWeight: 800, color: GRY}}>PROJECTION — IPSS MEDIUM SCENARIO · ALL RESIDENTS</span>
          </div>
        </div>
      )}

      {pB > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pB}}>
          <div style={{position: 'absolute', top: 230, left: 86, fontSize: 32, fontWeight: 900, color: '#fff', letterSpacing: 1}}>
            WORKING-AGE PEOPLE <span style={{color: GRY, fontSize: 24, fontWeight: 700}}>(15–64, all residents)</span>
          </div>
          {[{y: 330, yr: '2032', v: 'BELOW 70M', d: 600},
            {y: 490, yr: '2043', v: 'BELOW 60M', d: 680},
            {y: 650, yr: '2062', v: 'BELOW 50M', d: 780}].map((m, i) => (
            <div key={i} style={{position: 'absolute', top: m.y, left: 86 + i * 230, opacity: f > m.d ? 1 : 0,
              transform: `scale(${slam(m.d)})`, transformOrigin: 'left center',
              border: '4px dashed ' + CRIM, borderRadius: 14, background: 'rgba(10,20,32,0.9)', padding: '14px 30px'}}>
              <span style={{fontSize: 40, fontWeight: 900, color: YEL}}>{m.yr}</span>
              <span style={{fontSize: 40, fontWeight: 900, color: '#fff'}}>  —  {m.v}</span>
            </div>
          ))}
          <div style={{position: 'absolute', top: 830, left: 86, border: '3px dashed ' + GRY, borderRadius: 12,
            padding: '10px 24px', opacity: t(950, 975)}}>
            <span style={{fontSize: 24, fontWeight: 800, color: GRY}}>DOTTED = PROJECTION, NOT FATE · IPSS MEDIUM SCENARIO</span>
          </div>
        </div>
      )}

      {pC > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pC}}>
          <div style={{position: 'absolute', top: 225, left: 86}}>
            <span style={{fontSize: 96, fontWeight: 900, color: '#fff'}}>9.0M</span>
            <span style={{fontSize: 34, fontWeight: 900, color: CRIM}}>  EMPTY HOMES — 13.8% OF ALL OF JAPAN</span>
          </div>
          {[{v: 4.44, n: 'FOR RENT', c: '#5e7a96', d: 1230},
            {v: 3.86, n: 'TRULY ABANDONED', c: CRIM, d: 1290},
            {v: 0.38, n: 'SECOND HOMES', c: '#5e7a96', d: 1350},
            {v: 0.33, n: 'FOR SALE', c: '#5e7a96', d: 1390}].map((b, i) => (
            <div key={i} style={{position: 'absolute', top: 390 + i * 92, left: 86, opacity: f > b.d ? 1 : 0}}>
              <div style={{fontSize: 24, fontWeight: 800, color: b.c === CRIM ? '#ff8093' : GRY}}>
                {b.n} — {b.v.toFixed(2)}M
              </div>
              <div style={{width: `${b.v * 240 * bar(b.d)}px`, height: 34, background: b.c, borderRadius: 8, marginTop: 6}}/>
            </div>
          ))}
          <div style={{position: 'absolute', top: 420, right: 100, width: 520, opacity: t(1480, 1510)}}>
            <div style={{background: '#fff', borderRadius: 14, padding: '20px 28px'}}>
              <div style={{fontSize: 28, fontWeight: 900, color: INK}}>65.0M HOMES</div>
              <div style={{fontSize: 28, fontWeight: 900, color: CRIM}}>vs 56.2M HOUSEHOLDS</div>
              <div style={{fontSize: 22, fontWeight: 700, color: '#44546a', marginTop: 6}}>Japan already has more homes than households</div>
            </div>
            <div style={{background: 'rgba(255,255,255,0.08)', border: '2px solid #33475c', borderRadius: 14,
              padding: '16px 28px', marginTop: 20, opacity: t(1580, 1610)}}>
              <span style={{fontSize: 25, fontWeight: 800, color: '#fff'}}>EVEN TOKYO: 896.5K VACANT (10.9%)</span>
            </div>
          </div>
        </div>
      )}

      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#6d8aa6'}}>
        {f < 1150 ? 'Source: IPSS, Population Projections for Japan (2023), medium variant'
                 : 'Source: MIC Housing and Land Survey, 2023'}
      </div>
    </AbsoluteFill>
  );
};
