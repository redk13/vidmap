import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {geoMercator, geoPath} from 'd3-geo';
import type {FeatureCollection} from 'geojson';
import korea from '../data/korea.json';
import {JapanMap} from './JapanMap';

const CRIM = '#e8273c', INK = '#0a1420', YEL = '#ffd60a', GRY = '#8fa6bd';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const YRS  = [1950, 1960, 1970, 1980, 1990, 2000, 2008, 2015, 2025, 2040, 2055, 2070];
const VALS = [83.2, 93.4, 103.7, 117.1, 123.6, 126.9, 128.1, 127.1, 123.8, 112.8, 100.0, 87.0];
const X0 = 250, X1 = 1670, Y0 = 840, Y1 = 270; // chart box
const xOf = (yr: number) => X0 + ((yr - 1950) / 120) * (X1 - X0);
const yOf = (v: number) => Y0 - ((v - 80) / 50) * (Y0 - Y1);
const valAt = (yr: number) => {
  for (let i = 1; i < YRS.length; i++) if (yr <= YRS[i]) {
    const p = (yr - YRS[i-1]) / (YRS[i] - YRS[i-1]);
    return VALS[i-1] + p * (VALS[i] - VALS[i-1]);
  }
  return VALS[VALS.length-1];
};

// FINALE (1100f): the curve -> countermeasures -> Korea tease
export const Finale: React.FC = () => {
  const f = useCurrentFrame();
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);
  const pAB = 1 - t(1490, 1535);
  const pC = t(1510, 1555);
  const yr = interpolate(f, [90, 420], [1950, 2070], {...clamp, easing: Easing.inOut(Easing.quad)});
  const slam = (t0: number) => interpolate(f, [t0, t0 + 20], [1.7, 1], {...clamp, easing: Easing.out(Easing.back(1.7))});

  const K = useMemo(() => {
    const fc = korea as unknown as FeatureCollection;
    const proj = geoMercator().fitExtent([[1050, 190], [1780, 920]], fc as any);
    const path = geoPath(proj);
    const seoul = proj([126.978, 37.566]) as [number, number];
    return {d: path(fc.features[0] as any) ?? '', seoul};
  }, []);

  const solidPts = [], dotPts = [];
  for (let y = 1950; y <= Math.min(yr, 2025); y += 1) solidPts.push(`${y===1950?'M':'L'}${xOf(y).toFixed(1)},${yOf(valAt(y)).toFixed(1)}`);
  if (yr > 2025) for (let y = 2025; y <= yr; y += 1) dotPts.push(`${y===2025?'M':'L'}${xOf(y).toFixed(1)},${yOf(valAt(y)).toFixed(1)}`);
  const pulse = (f % 50) / 50;

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      {pAB > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pAB}}>
          <div style={{position: 'absolute', inset: 0, opacity: 0.18}}>
            <JapanMap width={1920} height={1080} styleFor={() => ({fill: '#1a2938'})} okinawaInset={false}/>
          </div>
          <svg width={1920} height={1080} style={{position: 'absolute'}}>
            <line x1={X0} y1={Y0} x2={X1} y2={Y0} stroke="#33475c" strokeWidth={2}/>
            <path d={solidPts.join(' ')} fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round"/>
            {dotPts.length > 1 && <path d={dotPts.join(' ')} fill="none" stroke={CRIM} strokeWidth={6}
              strokeLinecap="round" strokeDasharray="4 16"/>}
            <circle cx={xOf(Math.min(yr, 2070))} cy={yOf(valAt(Math.min(yr, 2070)))} r={13}
              fill={yr > 2025 ? CRIM : '#fff'}/>
            {yr >= 2008 && (
              <g opacity={t(250, 275)}>
                <circle cx={xOf(2008)} cy={yOf(128.1)} r={9} fill={YEL}/>
                <text x={xOf(2008)} y={yOf(128.1) - 24} textAnchor="middle" fontSize={27} fontWeight={900} fill={YEL}>PEAK 2008 — 128.1M</text>
              </g>
            )}
            {yr >= 2026 && (
              <text x={xOf(2025) - 10} y={yOf(123.8) + 46} textAnchor="end" fontSize={25} fontWeight={800} fill="#fff" opacity={t(300, 325)}>TODAY — 123.8M</text>
            )}
            {yr >= 2069 && (
              <g opacity={t(430, 455)}>
                <text x={xOf(2070) - 16} y={yOf(87) - 8} textAnchor="end" fontSize={30} fontWeight={900} fill={CRIM}>2070 — 87.0M</text>
                <text x={xOf(2070) - 16} y={yOf(87) + 26} textAnchor="end" fontSize={21} fontWeight={700} fill={GRY}>IPSS medium scenario</text>
              </g>
            )}
          </svg>
          <div style={{position: 'absolute', top: 60, left: 86}}>
            <div style={{fontSize: 90, fontWeight: 900, color: '#fff', lineHeight: 1}}>{valAt(Math.min(yr, 2070)).toFixed(1)}M</div>
            <div style={{fontSize: 40, fontWeight: 900, color: YEL, marginTop: 4}}>{Math.round(Math.min(yr, 2070))}</div>
          </div>
          {f > 920 && (
            <div style={{position: 'absolute', top: 70, right: 86, width: 600, opacity: t(920, 945)}}>
              <div style={{fontSize: 30, fontWeight: 900, color: '#fff', marginBottom: 14}}>TOKYO IS TRYING —</div>
              {[{s: 960, txt: '4-DAY WORKWEEK — OPTIONAL (metro gov staff, 2025)'},
                {s: 1030, txt: 'FREE DAYCARE FOR PRESCHOOLERS (2025)'},
                {s: 1100, txt: 'EVEN A GOVERNMENT DATING APP'}].map((c, i) => (
                <div key={i} style={{background: '#fff', borderRadius: 10, padding: '10px 18px', marginBottom: 12,
                  opacity: f > c.s ? 1 : 0, transform: `scale(${slam(c.s)})`, transformOrigin: 'right center'}}>
                  <span style={{fontSize: 23, fontWeight: 900, color: INK}}>{c.txt}</span>
                </div>
              ))}
              <div style={{fontSize: 24, fontWeight: 800, color: CRIM, marginTop: 10, opacity: t(1180, 1205)}}>
                SO FAR, THE CURVE HASN'T BENT.
              </div>
            </div>
          )}
          <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#6d8aa6'}}>
            Sources: Statistics Bureau of Japan · IPSS (2023) medium variant · Tokyo Metropolitan Government
          </div>
        </div>
      )}

      {pC > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pC}}>
          <svg width={1920} height={1080} style={{position: 'absolute'}}>
            <path d={K.d} fill="#2a0e14" stroke={CRIM} strokeWidth={3}
              opacity={t(1530, 1590)} transform={`translate(${(1 - t(1530, 1600)) * 300} 0)`}/>
            {f > 1700 && (
              <g>
                <circle cx={K.seoul[0]} cy={K.seoul[1]} r={10} fill={CRIM}/>
                <circle cx={K.seoul[0]} cy={K.seoul[1]} r={14 + 60 * pulse} fill="none" stroke={CRIM}
                  strokeWidth={3.5 * (1 - pulse)} opacity={1 - pulse}/>
              </g>
            )}
          </svg>
          <div style={{position: 'absolute', top: 210, left: 110, opacity: t(1600, 1630)}}>
            <div style={{fontSize: 34, fontWeight: 800, color: GRY, letterSpacing: 3}}>MEANWHILE, NEXT DOOR…</div>
            <div style={{fontSize: 46, fontWeight: 900, color: '#fff', marginTop: 10}}>SOUTH KOREA</div>
            <div style={{fontSize: 150, fontWeight: 900, color: CRIM, lineHeight: 1}}>0.80</div>
            <div style={{fontSize: 28, fontWeight: 800, color: GRY}}>FERTILITY RATE — 2025</div>
            <div style={{fontSize: 58, fontWeight: 900, color: '#fff', marginTop: 28, opacity: t(1790, 1815)}}>
              SEOUL: <span style={{color: CRIM}}>0.63</span>
            </div>
          </div>
          {f > 1870 && (
            <div style={{position: 'absolute', bottom: 150, left: 110, transform: `rotate(-4deg) scale(${slam(1870)})`,
              transformOrigin: 'left bottom'}}>
              <div style={{border: '5px solid #fff', borderRadius: 10, padding: '10px 26px', display: 'inline-block'}}>
                <span style={{fontSize: 46, fontWeight: 900, color: '#fff'}}>SAME MACHINE. <span style={{color: CRIM}}>TURNED UP.</span></span>
              </div>
            </div>
          )}
          <div style={{position: 'absolute', bottom: 60, left: 114, fontSize: 26, fontWeight: 800, color: YEL, opacity: t(1950, 1975)}}>
            NEXT EPISODE — SOUTH KOREA
          </div>
          <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#6d8aa6'}}>
            Source: Statistics Korea, 2026
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
