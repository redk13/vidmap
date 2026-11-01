import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';
import {loadFont as loadLuck} from '@remotion/google-fonts/LuckiestGuy';

const {fontFamily: MONT} = loadMont();
const {fontFamily: LUCK} = loadLuck();
const INK = '#101418', YEL = '#ffd60a';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const FLIP = 770;

const toPath = (geom: any): string => {
  const ring = (r: number[][]) => r.map((c, i) => {
    const [x, y] = lonLatToPx(c[0], c[1]);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};
const centroidPx = (geom: any): [number, number] => {
  let ring = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
  if (geom.type === 'MultiPolygon') {
    for (const poly of geom.coordinates) if (poly[0].length > ring.length) ring = poly[0];
  }
  let sx = 0, sy = 0;
  for (const c of ring) { const [x, y] = lonLatToPx(c[0], c[1]); sx += x; sy += y; }
  return [sx / ring.length, sy / ring.length];
};
const qb = (p0: number[], c: number[], p1: number[], t: number) => [
  (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
  (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1],
];

// ACT 1 v2 — arrows + fertility flip on REAL tilted satellite (1509f)
export const Act1V2: React.FC = () => {
  const f = useCurrentFrame();
  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    const polys: {id: number; d: string; c: [number, number]}[] = [];
    for (const ft of fc.features) {
      const p: any = ft;
      let g = p.geometry;
      if (p.properties.id === 13 && g.type === 'MultiPolygon') {
        let best = g.coordinates[0];
        for (const poly of g.coordinates) if (JSON.stringify(poly).length > JSON.stringify(best).length) best = poly;
        g = {type: 'Polygon', coordinates: best};
      }
      polys.push({id: p.properties.id, d: toPath(g), c: centroidPx(g)});
    }
    const T = polys.find((p) => p.id === 13)!.c;
    const O = polys.find((p) => p.id === 47)!.c;
    return {polys, T, O};
  }, []);

  const mig = interpolate(f, [FLIP - 60, FLIP], [1, 0], clamp);
  const fert = interpolate(f, [FLIP, FLIP + 80], [0, 1], clamp);
  const counter = Math.round(interpolate(f, [90, 600], [0, 65219], clamp));
    const zoomS = interpolate(f, [0, 340, FLIP - 60, FLIP + 90, 1509], [1.64, 1.52, 1.6, 1.4, 1.48], {...clamp});
  const panX = interpolate(f, [0, 680, FLIP, 900, 1509], [-45, 25, 0, 0, -20], clamp);
  const CAM: number[][] = [[0,960,540,1.04],[120,1220,490,1.4],[240,1210,500,1.43],[360,870,670,1.18],[480,1060,620,1.42],[580,1070,630,1.44],[700,1300,700,1.2],[800,960,540,1.03],[950,360,520,1.4],[1060,370,530,1.43],[1170,935,780,1.42],[1300,930,790,1.45],[1420,960,560,1.08],[1509,955,570,1.1]];
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

  const panY = interpolate(f, [FLIP - 30, FLIP + 140], [0, 460], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const pulse = (f % 50) / 50;

  const fillFor = (id: number): string => {
    if (fert > 0) {
      if (id === 13) return `rgba(220,30,50,${0.25 + 0.55 * fert})`;
      if (id === 47) return `rgba(47,134,255,${0.2 + 0.6 * fert})`;
      return 'rgba(10,16,24,0.3)';
    }
    if (id === 13) return 'rgba(47,134,255,0.75)';
    return 'rgba(12,20,30,0.22)';
  };

  const Sticker: React.FC<{x: number; y: number; rot?: number; bg?: string; color?: string; o: number; children: React.ReactNode}> =
  ({x, y, rot = -2, bg = '#fff', color = INK, o, children}) => (
    <g opacity={o} transform={`translate(${x} ${y}) rotate(${rot})`}>
      <foreignObject x={0} y={0} width={640} height={86}>
        <div style={{display: 'inline-block', background: bg, borderRadius: 10, padding: '10px 22px',
          boxShadow: '0 10px 26px rgba(0,0,0,0.55)'}}>
          <span style={{fontFamily: MONT, fontWeight: 900, fontSize: 32, color, whiteSpace: 'nowrap'}}>{children}</span>
        </div>
      </foreignObject>
    </g>
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(12px) brightness(0.5)'}}/>
            <div style={{position: 'absolute', left: 960 - SAT_W / 2 + panX, top: 540 - SAT_H / 2 - 40 - panY,
        width: SAT_W, height: SAT_H,
        transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 438.6) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${zoomS})`, transformOrigin: '50% 46%'}}>
        <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H}}/>
        <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
          <defs>
            <radialGradient id="haloA">
              <stop offset="0%" stopColor="#7db8ff" stopOpacity="0.9"/>
              <stop offset="50%" stopColor="#2f86ff" stopOpacity="0.35"/>
              <stop offset="100%" stopColor="#2f86ff" stopOpacity="0"/>
            </radialGradient>
          </defs>
          {M.polys.map((p) => (
            <path key={p.id} d={p.d} fill={fillFor(p.id)} stroke="rgba(255,255,255,0.3)" strokeWidth={1}/>
          ))}

          {mig > 0 && M.polys.filter((p) => p.id !== 13 && p.id !== 47).map((p) => {
            const S = p.c, T = M.T;
            const mx = (S[0] + T[0]) / 2, my = (S[1] + T[1]) / 2;
            const dx = T[0] - S[0], dy = T[1] - S[1];
            const len = Math.hypot(dx, dy) || 1;
            const bend = (p.id % 2 === 0 ? 1 : -1) * (26 + (p.id * 13) % 42);
            const C = [mx - (dy / len) * bend, my + (dx / len) * bend];
            const grow = interpolate(f, [80 + p.id * 4, 170 + p.id * 4], [0, 1], clamp);
            if (grow <= 0) return null;
            const pts: string[] = [];
            for (let i = 0; i <= 22 * grow; i++) {
              const q = qb(S, C, T, i / 22);
              pts.push(`${i === 0 ? 'M' : 'L'}${q[0].toFixed(1)},${q[1].toFixed(1)}`);
            }
            const pt = ((f * 0.013 + p.id * 0.11) % 1) * grow;
            const q = qb(S, C, T, pt);
            return (
              <g key={p.id} opacity={mig}>
                <path d={pts.join(' ')} fill="none" stroke="#bfe0ff" strokeWidth={2} opacity={0.55} strokeLinecap="round"/>
                <circle cx={q[0]} cy={q[1]} r={3.4} fill="#ffffff"/>
              </g>
            );
          })}

          {mig > 0 && (
            <g opacity={mig}>
              <circle cx={M.T[0]} cy={M.T[1]} r={60} fill="url(#haloA)"/>
              <circle cx={M.T[0]} cy={M.T[1]} r={5} fill="#eaf4ff"/>
            </g>
          )}
          {mig > 0 && f > 430 && (
            <g opacity={mig}>
              <line x1={M.T[0] - 30} y1={M.T[1] + 86} x2={M.T[0] - 6} y2={M.T[1] + 14} stroke="#fff" strokeWidth={3}
                opacity={interpolate(f, [430, 448], [0, 1], clamp)}/>
              <Sticker x={M.T[0] - 580} y={M.T[1] + 92} rot={-3} bg={YEL} o={interpolate(f, [430, 448], [0, 1], clamp)}>
                BIGGEST GROUP: AGE 20–24
              </Sticker>
            </g>
          )}

          {fert > 0.5 && (
            <g>
              <circle cx={M.T[0]} cy={M.T[1]} r={14 + 40 * pulse} fill="none" stroke="#ff3b4f"
                strokeWidth={3 * (1 - pulse)} opacity={(1 - pulse) * fert}/>
              <line x1={M.T[0] - 6} y1={M.T[1] + 8} x2={M.T[0] - 60} y2={M.T[1] + 44} stroke="#fff" strokeWidth={3} opacity={interpolate(f, [FLIP + 100, FLIP + 125], [0, 1], clamp)}/>
              <Sticker x={M.T[0] - 380} y={M.T[1] + 48} rot={-2} bg="#e8273c" color="#fff" o={interpolate(f, [FLIP + 100, FLIP + 125], [0, 1], clamp)}>
                TOKYO 0.96 — THE LOWEST
              </Sticker>
              <line x1={M.O[0] + 2} y1={M.O[1] - 2} x2={M.O[0] + 80} y2={M.O[1] - 120} stroke="#fff" strokeWidth={3} opacity={interpolate(f, [FLIP + 200, FLIP + 225], [0, 1], clamp)}/>
              <Sticker x={M.O[0] + 80} y={M.O[1] - 196} rot={-3} bg="#2f86ff" color="#fff" o={interpolate(f, [FLIP + 200, FLIP + 225], [0, 1], clamp)}>
                OKINAWA 1.52 — THE HIGHEST
              </Sticker>
            </g>
          )}
        </svg>
        {f > 260 && f < 640 && (() => {
          const p = interpolate(f, [260, 620], [0, 1], clamp);
          return (
            <div style={{position: 'absolute', left: 640 + (M.T[0] - 640) * p, top: 980 + (M.T[1] - 980) * p + 3 * Math.sin(f / 5),
              transform: 'translate(-50%, -100%) rotateX(-35deg)', transformOrigin: '50% 100%',
              opacity: Math.min(interpolate(f, [260, 282], [0, 1], clamp), interpolate(f, [598, 624], [1, 0], clamp))}}>
              <Img src={staticFile('photos/commuters.png')} style={{width: 150 - 95 * p, filter: 'drop-shadow(0 8px 12px rgba(0,0,0,0.5))'}}/>
            </div>
          );
        })()}
        {f > 380 && f < 745 && (() => {
          const p = interpolate(f, [380, 722], [0, 1], clamp);
          return (
            <div style={{position: 'absolute', left: 430 + (M.T[0] - 430) * p, top: 1180 + (M.T[1] - 1180) * p + 3 * Math.sin(f / 5 + 2),
              transform: 'translate(-50%, -100%) rotateX(-35deg)', transformOrigin: '50% 100%',
              opacity: Math.min(interpolate(f, [380, 402], [0, 1], clamp), interpolate(f, [700, 726], [1, 0], clamp))}}>
              <Img src={staticFile('photos/commuters.png')} style={{width: 140 - 88 * p, filter: 'drop-shadow(0 8px 12px rgba(0,0,0,0.5))'}}/>
            </div>
          );
        })()}
        {f > 1180 && (
          <div style={{position: 'absolute', left: M.O[0] + 28, top: M.O[1] - 2,
            transform: `translate(-50%, -100%) rotateX(-35deg) scale(${interpolate(f, [1180, 1202], [0, 1], clamp)})`,
            transformOrigin: '50% 100%'}}>
            <Img src={staticFile('puppets/baby.png')} style={{width: 92, filter: 'drop-shadow(0 8px 12px rgba(0,0,0,0.5))'}}/>
          </div>
        )}
      </div>

      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 48%, rgba(0,0,0,0.5) 100%)', pointerEvents: 'none'}}/>

      {mig > 0 && (
        <div style={{position: 'absolute', top: 54, left: 76, opacity: mig}}>
          <div style={{fontWeight: 900, fontSize: 100, color: '#fff', lineHeight: 1, textShadow: '0 6px 26px rgba(0,0,0,0.85)'}}>
            +{counter.toLocaleString('en-US')}
          </div>
          <div style={{display: 'inline-block', background: '#fff', borderRadius: 10, padding: '8px 20px',
            marginTop: 14, transform: 'rotate(-2deg)', boxShadow: '0 8px 22px rgba(0,0,0,0.55)'}}>
            <span style={{fontWeight: 800, fontSize: 29, color: INK}}>NET MOVES INTO TOKYO — 2025</span>
          </div>
          <div style={{fontWeight: 700, fontSize: 20, color: 'rgba(255,255,255,0.75)', marginTop: 10, textShadow: '0 2px 8px #000'}}>
            Slower than 2024 — still #1 · Source: MIC, 2026
          </div>
        </div>
      )}

      {fert > 0 && (
        <div style={{position: 'absolute', top: 54, left: 76, opacity: fert}}>
          <div style={{fontFamily: LUCK, fontSize: 64, color: '#fff', lineHeight: 1.04, textShadow: '0 6px 26px rgba(0,0,0,0.9)'}}>
            NOW FLIP THE MAP:<br/><span style={{color: '#ff3b4f'}}>FERTILITY</span>
          </div>
          <div style={{display: 'inline-block', background: '#fff', borderRadius: 10, padding: '10px 24px',
            marginTop: 18, transform: 'rotate(-2deg)', boxShadow: '0 8px 22px rgba(0,0,0,0.55)'}}>
            <span style={{fontWeight: 900, fontSize: 36, color: INK}}>JAPAN 1.14</span>
            <span style={{fontWeight: 800, fontSize: 24, color: '#e8273c'}}> — 10TH RECORD LOW</span>
          </div>
          <div style={{fontWeight: 700, fontSize: 20, color: 'rgba(255,255,255,0.75)', marginTop: 10, textShadow: '0 2px 8px #000'}}>
            Source: MHLW, 2026
          </div>
        </div>
      )}
    
      {f > 210 && f < 745 && (
        <Img src={staticFile('photos/station.png')} style={{position: 'absolute', right: 70, bottom: 110, width: 440,
          opacity: Math.min(interpolate(f, [210, 228], [0, 1], clamp), interpolate(f, [700, 740], [1, 0], clamp)),
          transform: `scale(${interpolate(f, [210, 232], [1.5, 1], clamp)}) rotate(${-2 + 0.8 * Math.sin(f / 37)}deg) translateY(${5 * Math.sin(f / 27)}px)`, transformOrigin: 'right bottom',
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))'}}/>
      )}
      {f > FLIP + 150 && (
        <div style={{position: 'absolute', left: 86, top: 292, opacity: interpolate(f, [FLIP + 150, FLIP + 160], [0, 1], clamp),
          transform: `rotate(-7deg) scale(${interpolate(f, [FLIP + 150, FLIP + 166], [2.2, 1], clamp)})`, transformOrigin: 'left top'}}>
          <div style={{border: '5px solid #e8273c', borderRadius: 10, padding: '6px 20px', background: 'rgba(255,255,255,0.95)',
            boxShadow: '0 12px 26px rgba(0,0,0,0.55)', display: 'inline-block'}}>
            <span style={{fontFamily: LUCK, fontSize: 40, color: '#e8273c'}}>RECORD LOW</span>
          </div>
        </div>
      )}
      
      
      </AbsoluteFill>
  );
};
