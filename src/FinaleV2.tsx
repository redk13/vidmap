import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import korea from '../data/korea.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {loadFont as loadLuck} from '@remotion/google-fonts/LuckiestGuy';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: LUCK} = loadLuck();
const {fontFamily: MONT} = loadMont();
const CRIM = '#e8273c', INK = '#101418', YEL = '#ffd60a', GRY = '#aec4da';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const YRS  = [1950, 1960, 1970, 1980, 1990, 2000, 2008, 2015, 2025, 2040, 2055, 2070];
const VALS = [83.2, 93.4, 103.7, 117.1, 123.6, 126.9, 128.1, 127.1, 123.8, 112.8, 100.0, 87.0];
const X0 = 250, X1 = 1670, Y0 = 840, Y1 = 270;
const xOf = (yr: number) => X0 + ((yr - 1950) / 120) * (X1 - X0);
const yOf = (v: number) => Y0 - ((v - 80) / 50) * (Y0 - Y1);
const valAt = (yr: number) => {
  for (let i = 1; i < YRS.length; i++) if (yr <= YRS[i]) {
    const p = (yr - YRS[i - 1]) / (YRS[i] - YRS[i - 1]);
    return VALS[i - 1] + p * (VALS[i] - VALS[i - 1]);
  }
  return VALS[VALS.length - 1];
};

const toPath = (geom: any): string => {
  const ring = (r: number[][]) => r.map((c, i) => {
    const [x, y] = lonLatToPx(c[0], c[1]);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};

// FINALE V2 (2021f): the curve on satellite -> countermeasures -> Korea tease on REAL map
export const FinaleV2: React.FC = () => {
  const f = useCurrentFrame();
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);
  const pAB = 1 - t(1490, 1535);
  const pC = t(1510, 1555);
  const yr = interpolate(f, [90, 420], [1950, 2070], {...clamp, easing: Easing.inOut(Easing.quad)});
  const slam = (t0: number) => interpolate(f, [t0, t0 + 20], [1.7, 1], {...clamp, easing: Easing.out(Easing.back(1.7))});
    const CAM: number[][] = [[0,960,540,1.03],[70,440,780,1.32],[250,950,570,1.34],[420,1460,380,1.36],[560,1000,540,1.06],[760,980,550,1.09],[950,1420,450,1.38],[1120,1430,460,1.41],[1270,960,540,1.05],[1510,960,540,1.02],[1650,970,540,1.08],[1760,1170,455,1.32],[1850,1165,465,1.35],[1905,370,830,1.33],[1965,380,840,1.34],[2021,960,540,1.06]];
  const camAt = (): [number, number, number] => {
    const n = CAM.length;
    const tts = CAM.map((k) => k[0]);
    const ff = Math.max(tts[0], Math.min(f, tts[n - 1]));
    let i = 0;
    while (i < n - 2 && ff > tts[i + 1]) i++;
    const t0 = tts[i], t1 = tts[i + 1], d = Math.max(1, t1 - t0);
    const u = (ff - t0) / d;
    const u2 = u * u, u3 = u2 * u;
    const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
    const val = (c: number) => {
      const p0 = CAM[i][c], p1 = CAM[i + 1][c];
      const m0 = i > 0 ? (p1 - CAM[i - 1][c]) / Math.max(1, t1 - tts[i - 1]) : (p1 - p0) / d;
      const m1 = i < n - 2 ? (CAM[i + 2][c] - p0) / Math.max(1, tts[i + 2] - t0) : (p1 - p0) / d;
      return h00 * p0 + h10 * d * m0 + h01 * p1 + h11 * d * m1;
    };
    return [val(1), val(2), Math.max(1.0, val(3))];
  };
  const [cox, coy, cs] = camAt();

  

  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    const polys = (fc.features as any[]).map((p) => ({id: p.properties.id, d: toPath(p.geometry)}));
    const kfc = korea as unknown as FeatureCollection;
    const kd = toPath((kfc.features[0] as any).geometry);
    const seoul = lonLatToPx(126.978, 37.566);
    const KC: [number, number] = [440, 785]; // Korea center in sat px
    return {polys, kd, seoul, KC};
  }, []);

  const solidPts: string[] = [], dotPts: string[] = [];
  for (let y = 1950; y <= Math.min(yr, 2025); y += 1) solidPts.push(`${y === 1950 ? 'M' : 'L'}${xOf(y).toFixed(1)},${yOf(valAt(y)).toFixed(1)}`);
  if (yr > 2025) for (let y = 2025; y <= yr; y += 1) dotPts.push(`${y === 2025 ? 'M' : 'L'}${xOf(y).toFixed(1)},${yOf(valAt(y)).toFixed(1)}`);
  const pulse = (f % 50) / 50;
  const kSlide = (1 - interpolate(f, [1530, 1600], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)})) * 220;

  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(12px) brightness(0.5)'}}/>
            {/* plane AB — Japan, dimmed, chart on top */}
      {pAB > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pAB}}>
          <div style={{position: 'absolute', left: 960 - SAT_W / 2 + interpolate(f, [0, 1500], [-40, 40], clamp), top: 540 - SAT_H / 2 - 40,
            width: SAT_W, height: SAT_H, opacity: t(0, 25),
            transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 438.6) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${interpolate(f, [0, 750, 1500], [1.58, 1.5, 1.66], clamp)})`, transformOrigin: '50% 46%'}}>
            <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.72)'}}/>
            <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
              {M.polys.map((p) => (
                <path key={p.id} d={p.d} fill="rgba(8,14,22,0.5)" stroke="rgba(255,255,255,0.16)" strokeWidth={1}/>
              ))}
            </svg>
          </div>
          <div style={{position: 'absolute', inset: 0,
            background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0.15) 40%, rgba(0,0,0,0.8) 100%)'}}/>

          <svg width={1920} height={1080} style={{position: 'absolute'}}>
            <line x1={X0} y1={Y0} x2={X1} y2={Y0} stroke="rgba(174,196,218,0.4)" strokeWidth={2}/>
            <path d={solidPts.join(' ')} fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round"
              style={{filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.7))'}}/>
            {dotPts.length > 1 && <path d={dotPts.join(' ')} fill="none" stroke={CRIM} strokeWidth={6}
              strokeLinecap="round" strokeDasharray="4 16"/>}
            <circle cx={xOf(Math.min(yr, 2070))} cy={yOf(valAt(Math.min(yr, 2070)))} r={13}
              fill={yr > 2025 ? CRIM : '#fff'}/>
            {yr >= 2008 && (
              <g opacity={t(250, 275)}>
                <circle cx={xOf(2008)} cy={yOf(128.1)} r={9} fill={YEL}/>
                <text x={xOf(2008)} y={yOf(128.1) - 24} textAnchor="middle" fontSize={27} fontWeight={900} fill={YEL} fontFamily={MONT}>PEAK 2008 — 128.1M</text>
              </g>
            )}
            {yr >= 2026 && (
              <text x={xOf(2025) - 10} y={yOf(123.8) + 46} textAnchor="end" fontSize={25} fontWeight={800} fill="#fff" opacity={t(300, 325)} fontFamily={MONT}>TODAY — 123.8M</text>
            )}
            {yr >= 2069 && (
              <g opacity={t(430, 455)}>
                <text x={xOf(2070) - 16} y={yOf(87) - 8} textAnchor="end" fontSize={30} fontWeight={900} fill="#ff5a6e" fontFamily={MONT}>2070 — 87.0M</text>
                <text x={xOf(2070) - 16} y={yOf(87) + 26} textAnchor="end" fontSize={21} fontWeight={700} fill={GRY} fontFamily={MONT}>IPSS medium scenario</text>
              </g>
            )}
          </svg>
          <div style={{position: 'absolute', top: 60, left: 86}}>
            <div style={{fontSize: 96, fontWeight: 900, color: '#fff', lineHeight: 1, textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>{valAt(Math.min(yr, 2070)).toFixed(1)}M</div>
            <div style={{fontFamily: LUCK, fontSize: 44, color: YEL, marginTop: 4}}>{Math.round(Math.min(yr, 2070))}</div>
          </div>
          {f > 920 && (
            <div style={{position: 'absolute', top: 70, right: 86, width: 600, opacity: t(920, 945)}}>
              <div style={{fontFamily: LUCK, fontSize: 36, color: '#fff', marginBottom: 14, textShadow: '0 4px 14px rgba(0,0,0,0.8)'}}>TOKYO IS TRYING —</div>
              {[{s: 960, txt: '4-DAY WORKWEEK — OPTIONAL (metro gov staff, 2025)', r: -1.5},
                {s: 1030, txt: 'FREE DAYCARE FOR PRESCHOOLERS (2025)', r: 1},
                {s: 1100, txt: 'EVEN A GOVERNMENT DATING APP', r: -1}].map((c, i) => (
                <div key={i} style={{background: '#fff', borderRadius: 10, padding: '10px 18px', marginBottom: 12,
                  opacity: f > c.s ? 1 : 0, transform: `scale(${slam(c.s)}) rotate(${c.r}deg)`, transformOrigin: 'right center',
                  boxShadow: '0 10px 24px rgba(0,0,0,0.55)'}}>
                  <span style={{fontSize: 23, fontWeight: 900, color: INK}}>{c.txt}</span>
                </div>
              ))}
              <div style={{fontSize: 25, fontWeight: 900, color: '#ff5a6e', marginTop: 10, opacity: t(1180, 1205)}}>
                SO FAR, THE CURVE HASN'T BENT.
              </div>
            </div>
          )}
          <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
            Sources: Statistics Bureau of Japan · IPSS (2023) medium variant · Tokyo Metropolitan Government
          </div>
        </div>
      )}

      {/* plane C — slide west to Korea on the same satellite */}
      {pC > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pC}}>
          <div style={{position: 'absolute', left: 960 - M.KC[0] + interpolate(f, [1510, 2021], [20, -25], clamp), top: 540 - M.KC[1], width: SAT_W, height: 1250,
            overflow: 'hidden', transformOrigin: `${M.KC[0]}px ${M.KC[1]}px`,
            transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 540) * (1 - cs)}px) scale(${cs}) perspective(1800px) rotateX(35deg) scale(${interpolate(f, [1510, 2021], [2.44, 2.56], clamp)})`}}>
            <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.78)'}}/>
            <svg width={SAT_W} height={1250} style={{position: 'absolute', left: 0, top: 0}}>
              <g transform={`translate(${kSlide} 0)`} opacity={t(1530, 1590)}>
                <path d={M.kd} fill="rgba(194,40,58,0.5)" stroke={CRIM} strokeWidth={2.2}/>
              </g>
              {f > 1700 && (
                <g>
                  <circle cx={M.seoul[0]} cy={M.seoul[1]} r={6} fill="#fff"/>
                  <circle cx={M.seoul[0]} cy={M.seoul[1]} r={9 + 42 * pulse} fill="none" stroke={CRIM}
                    strokeWidth={3 * (1 - pulse)} opacity={1 - pulse}/>
                  <line x1={M.seoul[0] + 6} y1={M.seoul[1] - 6} x2={M.seoul[0] + 60} y2={M.seoul[1] - 64} stroke="#fff" strokeWidth={2}/>
                  <g transform={`translate(${M.seoul[0] + 60} ${M.seoul[1] - 100}) rotate(-2)`} opacity={t(1700, 1720)}>
                    <rect x={0} y={0} rx={8} width={132} height={40} fill="#fff"
                      style={{filter: 'drop-shadow(0 6px 14px rgba(0,0,0,0.55))'}}/>
                    <text x={66} y={28} textAnchor="middle" fontSize={23} fontWeight={900} fill={INK} fontFamily={MONT}>SEOUL</text>
                  </g>
                </g>
              )}
            </svg>
          </div>
          <div style={{position: 'absolute', inset: 0,
            background: 'radial-gradient(ellipse at 42% 46%, rgba(0,0,0,0.05) 40%, rgba(0,0,0,0.76) 100%)'}}/>

          <div style={{position: 'absolute', top: 180, left: 110, opacity: t(1600, 1630)}}>
            <div style={{fontSize: 32, fontWeight: 800, color: GRY, letterSpacing: 3}}>MEANWHILE, NEXT DOOR…</div>
            <div style={{fontFamily: LUCK, fontSize: 56, color: '#fff', marginTop: 10, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>SOUTH KOREA</div>
            <div style={{fontSize: 150, fontWeight: 900, color: '#ff3b50', lineHeight: 1, textShadow: '0 8px 26px rgba(0,0,0,0.8)'}}>0.80</div>
            <div style={{fontSize: 28, fontWeight: 800, color: GRY}}>FERTILITY RATE — 2025</div>
            <div style={{fontSize: 58, fontWeight: 900, color: '#fff', marginTop: 26, opacity: t(1790, 1815), textShadow: '0 4px 16px rgba(0,0,0,0.8)'}}>
              SEOUL: <span style={{color: '#ff3b50'}}>0.63</span>
            </div>
          </div>
          {f > 1870 && (
            <div style={{position: 'absolute', bottom: 150, left: 110, transform: `rotate(-4deg) scale(${slam(1870)})`,
              transformOrigin: 'left bottom'}}>
              <div style={{border: '5px solid #fff', borderRadius: 10, padding: '8px 26px', display: 'inline-block',
                background: 'rgba(5,8,13,0.5)', boxShadow: '0 12px 28px rgba(0,0,0,0.55)'}}>
                <span style={{fontFamily: LUCK, fontSize: 48, color: '#fff'}}>SAME MACHINE. <span style={{color: '#ff3b50'}}>TURNED UP.</span></span>
              </div>
            </div>
          )}
          <div style={{position: 'absolute', bottom: 60, left: 114, fontSize: 27, fontWeight: 900, color: YEL, opacity: t(1950, 1975)}}>
            NEXT EPISODE — SOUTH KOREA
          </div>
          <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
            Source: Statistics Korea, 2026 · Imagery: Esri
          </div>
        </div>
      )}
    
      {pC > 0.01 && f > 1700 && (
        <Img src={staticFile('photos/seoul.png')} style={{position: 'absolute', right: 80, bottom: 110, width: 430,
          opacity: pC * t(1700, 1725),
          transform: `scale(${interpolate(f, [1700, 1728], [1.5, 1], clamp)}) rotate(${2 + 0.8 * Math.sin(f / 38)}deg) translateY(${5 * Math.sin(f / 27)}px)`, transformOrigin: 'right bottom',
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))'}}/>
      )}
      
      {pC > 0.01 && f > 1620 && f < 1745 && (() => {
        const p = interpolate(f, [1620, 1715], [0, 1], clamp);
        const px = 2010 - 860 * p;
        const py = 255 + 185 * p + 70 * Math.sin(Math.PI * p);
        const ang = -168 + 26 * Math.cos(Math.PI * p);
        const op = pC * Math.min(interpolate(f, [1620, 1635], [0, 1], clamp), interpolate(f, [1718, 1742], [1, 0], clamp));
        return (
          <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none', opacity: op}}>
            <g transform={`translate(${px} ${py}) rotate(${ang})`}>
              <path d="M0,0 L64,-10 L22,6 Z" fill="#ffffff" stroke="#9db4c8" strokeWidth={1.5}/>
              <path d="M0,0 L64,-10 L30,18 Z" fill="#dfe9f2" stroke="#9db4c8" strokeWidth={1.5}/>
            </g>
            {[0.12, 0.24, 0.36].map((d, i) => {
              const q = Math.max(0, p - d);
              return <circle key={i} cx={2010 - 860 * q} cy={255 + 185 * q + 70 * Math.sin(Math.PI * q)} r={3.5 - i} fill="#ffffff" opacity={0.35 - i * 0.1}/>;
            })}
          </svg>
        );
      })()}
      </AbsoluteFill>
  );
};
