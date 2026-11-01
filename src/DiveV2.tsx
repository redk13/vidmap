import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import tokyo23 from '../data/tokyo23.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {lonLatToPx2, SAT2_W, SAT2_H} from './sat2';
import {loadFont as loadLuck} from '@remotion/google-fonts/LuckiestGuy';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: LUCK} = loadLuck();
const {fontFamily: MONT} = loadMont();
const CRIM = '#e8273c', INK = '#101418', YEL = '#ffd60a', BLUE = '#2f86ff', GRY = '#aec4da';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const ease = Easing.inOut(Easing.cubic);
const OUT = 800;

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

// DIVE V2 — SPACE SQUEEZE (1673f): satellite dive to Shinjuku, zoom out to emptying Japan
export const DiveV2: React.FC = () => {
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
    const wfc = tokyo23 as unknown as FeatureCollection;
    const wards = (wfc.features as any[]).map((w) => ({
      n: w.properties.n, d: pathWith(w.geometry, lonLatToPx2), c: centroidOf(w.geometry, lonLatToPx2),
    }));
    const S = wards.find((w) => w.n === 'Shinjuku')!.c;
    return {polys, T, wards, S};
  }, []);
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);

  // plane A (whole Japan, z6) — origin pinned on Tokyo
  const out = t(OUT, OUT + 70);
  const sA = f < OUT
    ? interpolate(f, [40, 330], [1.35, 5.5], {...clamp, easing: ease})
    : interpolate(f, [OUT, OUT + 70], [5.5, 1.45], {...clamp, easing: Easing.out(Easing.cubic)});
  const opA = f < OUT
    ? Math.min(t(0, 25), interpolate(f, [300, 360], [1, 0], clamp))
    : t(OUT, OUT + 40);

  // plane B (Kanto, z10) — origin pinned on Shinjuku
  const sB = interpolate(f, [290, 430], [0.55, 1.5], {...clamp, easing: Easing.out(Easing.cubic)}) * (1 + out * 1.4);
  const CAM: number[][] = [[0,960,540,1.0],[840,960,540,1.0],[920,340,710,1.26],[1040,350,700,1.29],[1150,520,610,1.2],[1290,1460,700,1.36],[1430,1490,770,1.42],[1560,1480,780,1.44],[1673,960,560,1.04]];
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
  const opB = Math.min(t(290, 340), 1 - t(OUT, OUT + 50));

  const shinOn = f > 470 && f < OUT;
  const slam = (t0: number) => ({
    o: t(t0, t0 + 12),
    s: interpolate(f, [t0, t0 + 22], [1.6, 1], {...clamp, easing: Easing.out(Easing.back(1.8))}),
  });
  const c1 = slam(560), c2 = slam(640), c3 = slam(715);
  const phase1Ui = 1 - t(OUT - 20, OUT + 30);
  const cnt9 = (interpolate(f, [OUT + 100, OUT + 260], [0, 9.0], clamp)).toFixed(1);
  const abOn = f > OUT + 370;
  const houseIds = [1, 2, 3, 5, 6, 7, 9, 15, 16, 17, 20, 24, 29, 30, 31, 32, 33, 36, 38, 39, 41, 43, 44, 45, 46, 18];

  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(4px) brightness(0.72) saturate(1.08)'}}/>
            {opA > 0 && (
        <div style={{position: 'absolute', left: 1110 - M.T[0], top: 540 - M.T[1], width: SAT_W, height: SAT_H,
          opacity: opA, transformOrigin: `${M.T[0]}px ${M.T[1]}px`,
          transform: `perspective(1600px) rotateX(35deg) scale(${sA})`}}>
          <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.8)'}}/>
          <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
            {M.polys.map((p) => {
              const emptyT = f < OUT ? 0 : t(OUT + 60 + ((p.id * 7) % 47) * 9, OUT + 120 + ((p.id * 7) % 47) * 9);
              const fill = p.id === 13
                ? 'rgba(47,134,255,0.65)'
                : f < OUT ? 'rgba(10,16,24,0.3)' : `rgba(4,8,14,${0.3 + 0.42 * emptyT})`;
              return <path key={p.id} d={p.d} fill={fill} stroke="rgba(255,255,255,0.25)" strokeWidth={0.8}/>;
            })}
            {f >= OUT + 60 && houseIds.map((id, i) => {
              const on = t(OUT + 120 + i * 14, OUT + 140 + i * 14);
              if (on <= 0) return null;
              const p = M.polys.find((q) => q.id === id)!;
              const red = abOn && i % 3 === 0;
              return (
                <g key={id} opacity={on} transform={`translate(${p.c[0]} ${p.c[1] - 8 * on}) scale(${0.9 + 0.5 * (1 - on)})`}>
                  <path d="M -11 0 L 0 -11 L 11 0 L 11 13 L -11 13 Z"
                    fill={red ? CRIM : '#8ea7bf'} stroke="#0a1420" strokeWidth={1.6}/>
                </g>
              );
            })}
          </svg>
        </div>
      )}

      {opB > 0 && (
        <div style={{position: 'absolute', left: 960 - M.S[0] + interpolate(f, [OUT, 1673], [0, -80], clamp), top: 540 - M.S[1] + interpolate(f, [OUT, 1673], [0, 30], clamp), width: SAT2_W, height: SAT2_H,
          opacity: opB, transformOrigin: `${M.S[0]}px ${M.S[1]}px`,
          transform: `translate(${(cox - (1728 - M.S[0])) * (1 - cs)}px, ${(coy - (1308 - M.S[1])) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${sB})`}}>
          <Img src={staticFile('kanto-sat.jpg')} style={{position: 'absolute', width: SAT2_W, height: SAT2_H, filter: 'brightness(0.85)'}}/>
          <svg width={SAT2_W} height={SAT2_H} style={{position: 'absolute', left: 0, top: 0}}>
            {M.wards.map((w) => (
              <path key={w.n} d={w.d}
                fill={w.n === 'Shinjuku' && f > 470 ? 'rgba(255,214,10,0.42)' : 'rgba(10,18,28,0.3)'}
                stroke={w.n === 'Shinjuku' && f > 470 ? '#fff' : 'rgba(255,255,255,0.35)'}
                strokeWidth={w.n === 'Shinjuku' && f > 470 ? 2.5 : 1}/>
            ))}
            {shinOn && (
              <g>
                <circle cx={M.S[0]} cy={M.S[1]} r={40} fill="none" stroke={YEL}
                  strokeWidth={3} opacity={0.72}/>
                <line x1={M.S[0] - 8} y1={M.S[1] - 8} x2={M.S[0] - 70} y2={M.S[1] - 86} stroke="#fff" strokeWidth={2.5}/>
                <g transform={`translate(${M.S[0] - 290} ${M.S[1] - 140}) rotate(-2)`}>
                  <rect x={0} y={0} rx={10} width={222} height={52} fill="#fff"
                    style={{filter: 'drop-shadow(0 8px 18px rgba(0,0,0,0.55))'}}/>
                  <text x={111} y={36} textAnchor="middle" fontSize={30} fontWeight={900} fill={INK} fontFamily={MONT}>SHINJUKU</text>
                </g>
              </g>
            )}
          </svg>
        </div>
      )}

      <div style={{position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 46%, rgba(0,0,0,0.7) 100%)'}}/>

      {f > 490 && phase1Ui > 0 && (
        <div style={{position: 'absolute', top: 52, left: 86, opacity: t(490, 515) * phase1Ui}}>
          <div style={{fontSize: 30, fontWeight: 900, color: CRIM, letterSpacing: 5}}>CAUSE #1</div>
          <div style={{fontFamily: LUCK, fontSize: 74, color: '#fff', lineHeight: 1.0, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>
            THE SPACE<br/>SQUEEZE
          </div>
        </div>
      )}
      {phase1Ui > 0 && f > 560 && (
        <Img src={staticFile('photos/crowd.png')} style={{position: 'absolute', left: 64, top: 540, width: 470,
          opacity: c1.o * phase1Ui, filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))',
          transform: `scale(${c1.s}) rotate(-2deg)`, transformOrigin: 'left bottom'}}/>
      )}
      {phase1Ui > 0 && [{c: c1, y: 690, txt: 'TINY APARTMENTS', rot: -2},
        {c: c2, y: 788, txt: 'COMMUTES CAN EAT NEARLY 2 HOURS A DAY', rot: 1.5},
        {c: c3, y: 886, txt: "SOME OF JAPAN'S MOST EXPENSIVE SQUARE METERS", rot: -1.5}].map((k, i) => (
        <div key={i} style={{position: 'absolute', top: k.y, right: 60,
          background: '#fff', borderRadius: 12, padding: '14px 26px', opacity: k.c.o * phase1Ui,
          transform: `scale(${k.c.s}) rotate(${k.rot}deg)`, transformOrigin: 'right center',
          boxShadow: '0 12px 28px rgba(0,0,0,0.6)'}}>
          <span style={{fontSize: 29, fontWeight: 900, color: INK, whiteSpace: 'nowrap'}}>{k.txt}</span>
        </div>
      ))}

      {f > OUT + 380 && (
        <Img src={staticFile('photos/akiya.png')} style={{position: 'absolute', right: 70, top: 560, width: 470,
          opacity: t(OUT + 380, OUT + 400), filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))',
          transform: `scale(${interpolate(f, [OUT + 380, OUT + 402], [1.5, 1], {...clamp, easing: Easing.out(Easing.cubic)})}) rotate(2deg)`,
          transformOrigin: 'right top'}}/>
      )}
      {f > OUT + 80 && (
        <div style={{position: 'absolute', top: 52, left: 86, opacity: t(OUT + 80, OUT + 110)}}>
          <div style={{fontFamily: LUCK, fontSize: 50, color: '#fff', lineHeight: 1.05, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>
            MEANWHILE, THE REST OF JAPAN<br/><span style={{color: CRIM}}>IS EMPTYING OUT</span>
          </div>
          <div style={{marginTop: 24}}>
            <span style={{fontSize: 110, fontWeight: 900, color: '#fff', lineHeight: 1, textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>{cnt9}M</span>
            <span style={{fontSize: 32, fontWeight: 900, color: YEL}}>  VACANT HOMES — 13.8%</span>
          </div>
          <div style={{fontSize: 34, fontWeight: 900, color: '#ff8093', marginTop: 10, opacity: t(OUT + 370, OUT + 395)}}>
            3.86M FULLY ABANDONED
          </div>
          <div style={{fontSize: 26, fontWeight: 800, color: GRY, marginTop: 10, opacity: t(OUT + 500, OUT + 525)}}>
            SOME SELL FOR UNDER $10,000
          </div>
          <div style={{display: 'inline-block', background: '#fff', borderRadius: 12, padding: '10px 24px',
            marginTop: 18, opacity: t(OUT + 620, OUT + 645), transform: 'rotate(-2deg)',
            boxShadow: '0 12px 28px rgba(0,0,0,0.6)'}}>
            <span style={{fontSize: 28, fontWeight: 900, color: INK}}>MORE HOMES THAN HOUSEHOLDS</span>
          </div>
        </div>
      )}
      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
        {f < OUT ? 'Imagery: Esri World Imagery' : 'Source: MIC Housing and Land Survey, 2023'}
      </div>
    
      {f > OUT + 520 && (
        <div style={{position: 'absolute', right: 60, top: 780, opacity: interpolate(f, [OUT + 520, OUT + 530], [0, 1], clamp),
          transform: `rotate(-8deg) scale(${interpolate(f, [OUT + 520, OUT + 536], [2.2, 1], clamp)})`, transformOrigin: 'right top'}}>
          <div style={{border: '5px solid #e8273c', borderRadius: 10, padding: '6px 20px', background: 'rgba(255,255,255,0.95)',
            boxShadow: '0 12px 26px rgba(0,0,0,0.55)', display: 'inline-block'}}>
            <span style={{fontFamily: LUCK, fontSize: 36, color: '#e8273c'}}>UNDER $10,000</span>
          </div>
        </div>
      )}
      </AbsoluteFill>
  );
};
