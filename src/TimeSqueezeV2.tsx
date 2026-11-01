import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {loadFont as loadLuck} from '@remotion/google-fonts/LuckiestGuy';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: LUCK} = loadLuck();
const {fontFamily: MONT} = loadMont();
const CRIM = '#e8273c', INK = '#101418', YEL = '#ffd60a', GRN = '#49e07c';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const toPath = (geom: any): string => {
  const ring = (r: number[][]) => r.map((c, i) => {
    const [x, y] = lonLatToPx(c[0], c[1]);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};

// TIME SQUEEZE V2 (1270f) — clock ring tightens ON the tilted satellite over Tokyo
export const TimeSqueezeV2: React.FC = () => {
  const f = useCurrentFrame();
  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    const polys = (fc.features as any[]).map((p) => ({id: p.properties.id, d: toPath(p.geometry)}));
    const T = lonLatToPx(139.69, 35.68);
    return {polys, T};
  }, []);
  const T = M.T;
  const fadeIn = interpolate(f, [0, 25], [0, 1], clamp);
    const zoomS = interpolate(f, [0, 140, 620, 1270], [1.56, 1.74, 1.64, 1.85], {...clamp, easing: Easing.out(Easing.quad)});
  const panX = interpolate(f, [0, 1270], [55, -55], clamp);
  const CAM: number[][] = [[0,960,540,1.05],[110,1040,350,1.35],[230,1050,360,1.38],[350,1290,680,1.4],[460,1300,690,1.42],[540,350,430,1.45],[660,360,440,1.47],[780,1570,700,1.38],[900,1560,710,1.4],[1020,770,760,1.24],[1140,780,750,1.26],[1270,960,560,1.1]];
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

  const ringR = interpolate(f, [80, 700], [168, 84], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const ringOp = interpolate(f, [60, 100], [0, 1], clamp);
  const hand = (f * 3.1) % 360;
  const age = interpolate(f, [330, 460], [25, 31], clamp);
  const mar = Math.round(interpolate(f, [800, 980], [430000, 489119], clamp));
  const slam = interpolate(f, [530, 552], [1.8, 1], {...clamp, easing: Easing.out(Easing.back(1.8))});
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);
  const puppet = interpolate(f, [120, 142], [0, 1], clamp);
  const puppetPop = interpolate(f, [120, 142], [1.6, 1], {...clamp, easing: Easing.out(Easing.back(1.6))});
  const bob = 0;

  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(4px) brightness(0.72) saturate(1.08)'}}/>
            <div style={{position: 'absolute', left: 960 - SAT_W / 2 + panX, top: 540 - SAT_H / 2 - 40,
        width: SAT_W, height: SAT_H, opacity: fadeIn,
        transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 438.6) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${zoomS})`, transformOrigin: '50% 46%'}}>
        <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.8)'}}/>
        <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
          {M.polys.map((p) => (
            <path key={p.id} d={p.d} fill={p.id === 13 ? 'rgba(255,214,10,0.14)' : 'rgba(8,14,22,0.42)'}
              stroke="rgba(255,255,255,0.22)" strokeWidth={1}/>
          ))}
          {/* clock ring lying on the map, tightening over Tokyo */}
          <g opacity={ringOp}>
            <circle cx={T[0]} cy={T[1]} r={ringR} fill="rgba(255,214,10,0.08)" stroke={YEL} strokeWidth={5}/>
            <circle cx={T[0]} cy={T[1]} r={ringR + 14} fill="none" stroke="rgba(255,214,10,0.35)" strokeWidth={2}
              strokeDasharray="6 10"/>
            {Array.from({length: 12}, (_, i) => {
              const a = (i * 30 * Math.PI) / 180;
              return <line key={i}
                x1={T[0] + (ringR - 14) * Math.sin(a)} y1={T[1] - (ringR - 14) * Math.cos(a)}
                x2={T[0] + ringR * Math.sin(a)} y2={T[1] - ringR * Math.cos(a)}
                stroke={YEL} strokeWidth={4}/>;
            })}
            <line x1={T[0]} y1={T[1]} x2={T[0] + (ringR - 26) * Math.sin((hand * Math.PI) / 180)}
              y2={T[1] - (ringR - 26) * Math.cos((hand * Math.PI) / 180)}
              stroke="#fff" strokeWidth={5} strokeLinecap="round"/>
            <circle cx={T[0]} cy={T[1]} r={8} fill="#fff"/>
          </g>
        </svg>
      </div>
      <div style={{position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at 62% 45%, rgba(0,0,0,0) 44%, rgba(0,0,0,0.74) 100%)'}}/>

      {/* left column — screen space */}
      <div style={{position: 'absolute', top: 52, left: 86, opacity: t(15, 40)}}>
        <div style={{fontSize: 30, fontWeight: 900, color: CRIM, letterSpacing: 5}}>CAUSE #2</div>
        <div style={{fontFamily: LUCK, fontSize: 74, color: '#fff', lineHeight: 1.0, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>
          THE TIME<br/>SQUEEZE
        </div>
      </div>

      <Img src={staticFile('puppets/girl.png')} style={{position: 'absolute', left: 612, top: 236 + bob,
        height: 270, opacity: puppet, transform: `scale(${puppetPop}) rotate(2deg)`,
        filter: 'drop-shadow(0 14px 26px rgba(0,0,0,0.6))'}}/>

      <div style={{position: 'absolute', top: 322, left: 86, opacity: t(300, 330)}}>
        <div style={{fontSize: 25, fontWeight: 800, color: '#aec4da', letterSpacing: 3}}>AVG FIRST-TIME MOTHER</div>
        <div style={{fontSize: 116, fontWeight: 900, color: YEL, lineHeight: 1, textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>
          AGE {age.toFixed(1)}
        </div>
      </div>

      <div style={{position: 'absolute', top: 568, left: 86, opacity: t(500, 525), maxWidth: 740}}>
        <div style={{fontSize: 35, fontWeight: 900, color: '#fff', textShadow: '0 4px 14px rgba(0,0,0,0.8)'}}>
          FEWER THAN <span style={{color: CRIM, fontSize: 46}}>3%</span> OF BIRTHS HAPPEN OUTSIDE MARRIAGE
        </div>
        <div style={{display: 'inline-block', marginTop: 16, transform: `scale(${slam}) rotate(-2deg)`, transformOrigin: 'left center',
          background: CRIM, borderRadius: 10, padding: '10px 24px', opacity: f > 530 ? 1 : 0,
          boxShadow: '0 12px 26px rgba(0,0,0,0.6)'}}>
          <span style={{fontFamily: LUCK, fontSize: 38, color: '#fff'}}>LATE MARRIAGE = LOW FERTILITY</span>
        </div>
      </div>

      <div style={{position: 'absolute', top: 806, left: 86, opacity: t(780, 810)}}>
        <div style={{fontSize: 25, fontWeight: 800, color: '#aec4da', letterSpacing: 3}}>MARRIAGES — 2025</div>
        <div style={{fontSize: 84, fontWeight: 900, color: '#fff', lineHeight: 1, textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>
          {mar.toLocaleString('en-US')} <span style={{color: GRN, fontSize: 58}}>▲</span>
        </div>
        <div style={{fontSize: 24, fontWeight: 800, color: GRN, marginTop: 8, opacity: t(990, 1015)}}>
          2ND RISE IN A ROW — A FLICKER OF HOPE · still below 599,000 (2019)
        </div>
      </div>

      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
        Sources: MHLW, 2025 · OECD Family Database (2.4%, 2023)
      </div>
    
      {f > 560 && (
        <Img src={staticFile('photos/office-night.png')} style={{position: 'absolute', right: 28, top: 620, width: 360,
          opacity: interpolate(f, [560, 578], [0, 1], clamp),
          transform: `scale(${interpolate(f, [560, 582], [1.5, 1], clamp)}) rotate(2deg)`, transformOrigin: 'right top',
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))'}}/>
      )}
      {f > 470 && (
        <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
          <ellipse cx={320} cy={436} rx={290} ry={84} fill="none" stroke="#e8273c" strokeWidth={6}
            transform="rotate(-3 320 436)" pathLength={100} strokeDasharray={100}
            strokeDashoffset={100 - 100 * interpolate(f, [470, 512], [0, 1], clamp)} strokeLinecap="round"/>
        </svg>
      )}
      </AbsoluteFill>
  );
};
