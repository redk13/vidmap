import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import tokyo23 from '../data/tokyo23.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {lonLatToPx3, SAT3_W, SAT3_H} from './sat3';
import {loadFont as loadLuck} from '@remotion/google-fonts/LuckiestGuy';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: LUCK} = loadLuck();
const {fontFamily: MONT} = loadMont();
const CRIM = '#e8273c', INK = '#101418', YEL = '#ffd60a', RED = '#c2283a', GRY = '#aec4da';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const BH16 = ['Shinjuku', 'Bunkyo', 'Taito', 'Sumida', 'Shinagawa', 'Meguro', 'Ota', 'Setagaya', 'Shibuya', 'Nakano', 'Suginami', 'Toshima', 'Kita', 'Arakawa', 'Itabashi', 'Nerima'];

const qb = (p0: number[], c: number[], p1: number[], t: number) => [
  (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
  (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1],
];
const pathWith = (geom: any, proj: (lon: number, lat: number) => [number, number]): string => {
  const ring = (r: number[][]) => r.map((c, i) => {
    const [x, y] = proj(c[0], c[1]);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};
const centroidOf = (geom: any, proj: (lon: number, lat: number) => [number, number]): [number, number] => {
  let best: number[][] = [];
  const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
  for (const p of polys) if (p[0].length > best.length) best = p[0];
  let sx = 0, sy = 0;
  for (const c of best) { const [x, y] = proj(c[0], c[1]); sx += x; sy += y; }
  return [sx / best.length, sy / best.length];
};

// MACHINE V2 — CAUSE #3 + BLACK HOLE payoff (2776f) on real satellite
export const MachineV2: React.FC = () => {
  const f = useCurrentFrame();
  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    const polys = (fc.features as any[]).map((p) => {
      let g = p.geometry;
      if (p.properties.id === 13 && g.type === 'MultiPolygon') {
        let best = g.coordinates[0];
        for (const poly of g.coordinates) if (JSON.stringify(poly).length > JSON.stringify(best).length) best = poly;
        g = {type: 'Polygon', coordinates: best};
      }
      return {id: p.properties.id, d: pathWith(g, lonLatToPx), c: centroidOf(g, lonLatToPx)};
    });
    const T = lonLatToPx(139.69, 35.68);
    const A = polys.find((p) => p.id === 5)!.c; // Akita
    const wfc = tokyo23 as unknown as FeatureCollection;
    const wards = (wfc.features as any[]).map((w) => ({
      n: w.properties.n, d: pathWith(w.geometry, lonLatToPx3), c: centroidOf(w.geometry, lonLatToPx3),
    }));
    let wx = 0, wy = 0;
    for (const w of wards) { wx += w.c[0]; wy += w.c[1]; }
    const WC: [number, number] = [wx / wards.length, wy / wards.length];
    return {polys, T, A, wards, WC};
  }, []);
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);

  const japanOp = Math.min(t(0, 25), 1 - t(1540, 1590));
  const wardsOp = t(1570, 1620);
  const wave = interpolate(f, [1250, 1510], [0, 47], clamp);
  const grayT = interpolate(f, [700, 1200], [0, 30], clamp);
  const cnt744 = Math.round(interpolate(f, [1255, 1500], [0, 744], clamp));
  const cnt16 = Math.round(interpolate(f, [1840, 2080], [0, 16], clamp));
  const stamp = interpolate(f, [1620, 1642], [2.2, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const fl = interpolate(f, [180, 420], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});
  const baseLoss = interpolate(f, [300, 500], [1, 0.25], clamp);
  const pulse = (f % 50) / 50;

  const C = [(M.A[0] + M.T[0]) / 2 + 190, (M.A[1] + M.T[1]) / 2];
  const P = qb(M.A, C, M.T, fl);
  const girlFade = fl > 0 && fl < 1 ? Math.min(1, (1 - fl) * 8) : 0;

  const fillFor = (id: number): string => {
    if (id === 13) return 'rgba(47,134,255,0.65)';
    const waveIdx = (id * 11) % 47;
    if (f > 1240 && waveIdx < wave && f < 1560) return 'rgba(194,40,58,0.6)';
    const gOrder = (id * 7) % 47;
    if (gOrder < grayT) return 'rgba(4,8,14,0.66)';
    return 'rgba(10,16,24,0.32)';
  };
  const zoomA = interpolate(f, [0, 200, 900, 1540], [1.6, 1.5, 1.64, 1.56], clamp);
  const zoomB = interpolate(f, [1570, 2776], [1.45, 1.75], {...clamp, easing: Easing.out(Easing.quad)});
  const CAM: number[][] = [[0,960,540,1.04],[130,650,410,1.34],[260,660,420,1.37],[380,920,610,1.4],[500,930,620,1.42],[640,790,500,1.2],[820,780,510,1.22],[980,960,540,1.05],[1100,520,310,1.26],[1260,530,320,1.29],[1420,960,540,1.02],[1600,350,180,1.3],[1740,360,190,1.33],[1880,960,550,1.06],[2100,960,565,1.18],[2350,960,560,1.24],[2500,960,545,1.06],[2776,960,540,1.1]];
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


  const MiniPyr: React.FC<{x: number; y: number; label: string; bars: number[]; hi: number; hiColor: string; o: number}> =
  ({x, y, label, bars, hi, hiColor, o}) => (
    <g opacity={o} transform={`translate(${x} ${y}) rotate(-2)`}>
      <rect x={-78} y={-46} width={156} height={142} rx={10} fill="rgba(255,255,255,0.94)"
        style={{filter: 'drop-shadow(0 8px 18px rgba(0,0,0,0.5))'}}/>
      <text x={0} y={-22} textAnchor="middle" fontSize={17} fontWeight={900} fill={INK} fontFamily={MONT}>{label}</text>
      {bars.map((w, i) => (
        <rect key={i} x={-w / 2} y={-8 + i * 19} width={w} height={14} rx={3}
          fill={i === hi ? hiColor : '#8197ad'}/>
      ))}
    </g>
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(12px) brightness(0.5)'}}/>
            {japanOp > 0 && (
        <div style={{position: 'absolute', left: 960 - SAT_W / 2 + interpolate(f, [0, 1560], [40, -45], clamp), top: 540 - SAT_H / 2 - 40,
          width: SAT_W, height: SAT_H, opacity: japanOp,
          transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 438.6) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${zoomA})`, transformOrigin: '50% 46%'}}>
          <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.78)'}}/>
          <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
            <defs>
              <radialGradient id="haloM">
                <stop offset="0%" stopColor="#7db8ff" stopOpacity="0.9"/>
                <stop offset="50%" stopColor="#2f86ff" stopOpacity="0.35"/>
                <stop offset="100%" stopColor="#2f86ff" stopOpacity="0"/>
              </radialGradient>
            </defs>
            {M.polys.map((p) => (
              <path key={p.id} d={p.d} fill={fillFor(p.id)} stroke="rgba(255,255,255,0.25)" strokeWidth={0.8}/>
            ))}
            <circle cx={M.T[0]} cy={M.T[1]} r={54 + 14 * pulse} fill="url(#haloM)" opacity={0.8}/>

            {f > 60 && f < 1540 && (
              <g>
                {Array.from({length: 21}, (_, i) => {
                  const q = qb(M.A, C, M.T, i / 20);
                  return <circle key={i} cx={q[0]} cy={q[1]} r={3.2} fill="#9cc4ff" opacity={i / 20 < fl ? 0.8 : 0.2}/>;
                })}
                {girlFade > 0 && (
                  <g opacity={girlFade}>
                    <ellipse cx={P[0]} cy={P[1] + 42} rx={26} ry={9} fill="rgba(0,0,0,0.45)"/>
                    <foreignObject x={P[0] - 38} y={P[1] - 52} width={76} height={96}>
                      <Img src={staticFile('puppets/girl.png')} style={{width: 76, height: 94, objectFit: 'contain'}}/>
                    </foreignObject>
                  </g>
                )}
                <MiniPyr x={M.A[0] - 170} y={M.A[1] - 20} label="A RURAL TOWN" hi={4} hiColor={CRIM} o={t(60, 85)}
                  bars={[52, 66, 74, 62, 46 * baseLoss]}/>
                <MiniPyr x={M.T[0] + 190} y={M.T[1] - 60} label="TOKYO" hi={2} hiColor={YEL} o={t(60, 85)}
                  bars={[44, 72, 88 + 12 * (1 - baseLoss), 52, 26]}/>
              </g>
            )}
          </svg>
        </div>
      )}

      {wardsOp > 0 && (
        <div style={{position: 'absolute', left: 960 - M.WC[0] + interpolate(f, [1570, 2776], [25, -35], clamp), top: 540 - M.WC[1], width: SAT3_W, height: 1500,
          opacity: wardsOp, transformOrigin: `${M.WC[0]}px ${M.WC[1]}px`, overflow: 'hidden',
          transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 540) * (1 - cs)}px) scale(${cs}) perspective(1800px) rotateX(35deg) scale(${zoomB})`}}>
          <Img src={staticFile('tokyo-sat.jpg')} style={{position: 'absolute', width: SAT3_W, height: SAT3_H, filter: 'brightness(0.8)'}}/>
          <svg width={SAT3_W} height={SAT3_H} style={{position: 'absolute', left: 0, top: 0}}>
            {M.wards.map((w) => {
              const bhIdx = BH16.indexOf(w.n);
              const on = bhIdx >= 0 && bhIdx < cnt16;
              return <path key={w.n} d={w.d}
                fill={on ? 'rgba(2,4,8,0.9)' : 'rgba(10,18,28,0.28)'}
                stroke={on ? CRIM : 'rgba(255,255,255,0.4)'} strokeWidth={on ? 2.5 : 1}/>;
            })}
            {cnt16 > 0 && (() => {
              const parts = [];
              for (let i = 0; i < 90; i++) {
                const a0 = ((i * 137.5) % 360) * (Math.PI / 180);
                const r0 = 140 + ((i * 53) % 540);
                const sp = ((f - 1840) / 210 + i * 0.0113) % 1;
                const r = r0 * (1 - sp);
                const th = a0 + (1 - r / r0) * 5.2;
                parts.push(<circle key={i} cx={M.WC[0] + r * Math.cos(th)} cy={M.WC[1] + r * Math.sin(th) * 0.8}
                  r={1.6 + 2.6 * sp} fill="#cfe2ff" opacity={(0.12 + 0.7 * sp) * Math.min(1, (f - 1840) / 60)}/>);
              }
              return <g>{parts}</g>;
            })()}
            {cnt16 > 0 && (() => {
              const pups = ['puppets/worker.png', 'puppets/girl.png', 'puppets/senior.png'];
              const els = [];
              for (let i = 0; i < 6; i++) {
                const sp = ((f - 1840) / 240 + i / 6) % 1;
                const r = 60 + 580 * (1 - sp);
                const th = (i * 60 + 25) * (Math.PI / 180) + sp * 3.0;
                const x = M.WC[0] + r * Math.cos(th);
                const y = M.WC[1] + r * Math.sin(th) * 0.8;
                const w = 104 * (0.3 + 0.7 * (r / 640));
                const op = Math.min(1, (f - 1840) / 50) * Math.min(1, sp / 0.1) * Math.min(1, (1 - sp) / 0.15) * 0.95;
                els.push(<image key={i} href={staticFile(pups[i % 3])} x={x - w / 2} y={y - w * 1.6} width={w}
                  opacity={Math.max(0, op)} transform={`rotate(${sp * 140} ${x} ${y})`}/>);
              }
              return <g>{els}</g>;
            })()}
            {['Shinjuku', 'Shibuya', 'Setagaya'].map((n) => {
              const w = M.wards.find((x) => x.n === n)!;
              const idx = BH16.indexOf(n);
              return idx < cnt16 ? (
                <text key={n} x={w.c[0]} y={w.c[1] + 6} textAnchor="middle" fontSize={20} fontWeight={900}
                  fill="#ff8093" fontFamily={MONT}>{n.toUpperCase()}</text>
              ) : null;
            })}
          </svg>
        </div>
      )}

      <div style={{position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 46%, rgba(0,0,0,0.72) 100%)'}}/>

      {japanOp > 0 && (
        <div style={{position: 'absolute', top: 52, left: 86, opacity: t(15, 40) * japanOp}}>
          <div style={{fontSize: 30, fontWeight: 900, color: CRIM, letterSpacing: 5}}>CAUSE #3</div>
          <div style={{fontFamily: LUCK, fontSize: 74, color: '#fff', lineHeight: 1.0, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>
            THE MACHINE<br/>ITSELF
          </div>
        </div>
      )}

      {f > 1240 && f < 1560 && (
        <div style={{position: 'absolute', top: 430, left: 86, opacity: t(1250, 1275) * japanOp}}>
          <div style={{fontSize: 112, fontWeight: 900, color: '#fff', lineHeight: 1, textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>{cnt744}</div>
          <div style={{fontSize: 28, fontWeight: 900, color: '#ff8093', letterSpacing: 2, marginTop: 6}}>
            OF 1,729 MUNICIPALITIES "AT RISK"
          </div>
          <div style={{fontSize: 20, color: GRY, fontWeight: 700, marginTop: 6}}>Population Strategy Council — a private panel · Apr 2024</div>
        </div>
      )}

      {f > 1615 && (
        <div style={{position: 'absolute', top: 64, left: 86, transform: `scale(${stamp}) rotate(-6deg)`, transformOrigin: 'left top'}}>
          <div style={{border: '6px solid ' + CRIM, borderRadius: 10, padding: '8px 26px', background: 'rgba(255,255,255,0.96)',
            boxShadow: '0 14px 30px rgba(0,0,0,0.6)'}}>
            <div style={{fontFamily: LUCK, fontSize: 58, color: CRIM, letterSpacing: 2}}>BLACK HOLE</div>
          </div>
        </div>
      )}
      {f > 1850 && (
        <div style={{position: 'absolute', top: 262, left: 86, opacity: t(1850, 1875)}}>
          <div style={{fontSize: 98, fontWeight: 900, color: '#fff', lineHeight: 1, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>
            {cnt16}<span style={{color: GRY, fontSize: 60}}> / 23</span>
          </div>
          <div style={{fontSize: 27, fontWeight: 900, color: '#ff8093', letterSpacing: 2, marginTop: 4}}>TOKYO WARDS LABELED</div>
          <div style={{fontSize: 27, fontWeight: 900, color: '#ff8093', letterSpacing: 2}}>"BLACK-HOLE TYPE"</div>
          <div style={{fontSize: 21, color: GRY, fontWeight: 700, marginTop: 14, lineHeight: 1.5, textShadow: '0 3px 10px rgba(0,0,0,0.8)'}}>
            25 nationwide — 16 of them in Tokyo<br/>High inflow of the young, ultra-low fertility<br/>Chair: Akio Mimura · a PRIVATE council, not the government
          </div>
        </div>
      )}
      {f > 2440 && (
        <div style={{position: 'absolute', bottom: 120, left: 86, width: 560, background: '#fff', borderRadius: 12,
          padding: '16px 24px', opacity: t(2440, 2465), transform: 'rotate(-1.5deg)',
          boxShadow: '0 12px 28px rgba(0,0,0,0.6)'}}>
          <div style={{fontSize: 24, fontWeight: 900, color: INK}}>BUT — RIETI RESEARCHERS PUSH BACK:</div>
          <div style={{fontSize: 22, fontWeight: 700, color: '#44546a', marginTop: 4}}>the method and the labels oversimplify</div>
        </div>
      )}
      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
        Source: Population Strategy Council report, Apr 2024 · RIETI commentary · Imagery: Esri
      </div>
    
      {f > 1700 && f < 2420 && (
        <Img src={staticFile('photos/aerial.png')} style={{position: 'absolute', left: 86, top: 560, width: 360,
          opacity: Math.min(t(1700, 1720), 1 - t(2380, 2420)),
          transform: `scale(${interpolate(f, [1700, 1724], [1.5, 1], clamp)}) rotate(${-2 + 0.8 * Math.sin(f / 40)}deg) translateY(${5 * Math.sin(f / 30)}px)`, transformOrigin: 'left top',
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))'}}/>
      )}
      </AbsoluteFill>
  );
};
