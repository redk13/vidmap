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
const CRIM = '#e8273c', INK = '#101418', YEL = '#ffd60a', GRY = '#aec4da';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const toPath = (geom: any): string => {
  const ring = (r: number[][]) => r.map((c, i) => {
    const [x, y] = lonLatToPx(c[0], c[1]);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};

const Puppet: React.FC<{src: string; x: number; y: number; h: number; frac?: number; o?: number; rot?: number}> =
({src, x, y, h, frac = 1, o = 1, rot = 0}) => (
  <div style={{position: 'absolute', left: x, top: y, width: h, height: h, opacity: o, transform: `rotate(${rot}deg)`}}>
    {frac < 1 && (
      <>
        <Img src={staticFile(src)} style={{position: 'absolute', top: 0, height: h, left: '50%',
          transform: 'translateX(-50%)', opacity: 0.22, filter: 'grayscale(1)'}}/>
        <div style={{position: 'absolute', inset: -8, border: '3px dashed rgba(255,255,255,0.55)', borderRadius: 14}}/>
        <div style={{position: 'absolute', top: -46, width: '100%', textAlign: 'center', fontSize: 27,
          fontWeight: 900, color: '#ffd60a', fontFamily: MONT}}>+{frac.toFixed(1)}</div>
      </>
    )}
    <div style={{position: 'absolute', left: 0, top: h * (1 - frac), width: '100%', height: h * frac, overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{position: 'absolute', top: -h * (1 - frac), height: h, left: '50%',
        transform: 'translateX(-50%)', filter: 'drop-shadow(0 12px 22px rgba(0,0,0,0.55))'}}/>
    </div>
  </div>
);

// ACT 3 — THE BILL V2 (1761f): dependency puppets -> IPSS milestones -> akiya breakdown
export const BillV2: React.FC = () => {
  const f = useCurrentFrame();
  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    return (fc.features as any[]).map((p) => ({id: p.properties.id, d: toPath(p.geometry)}));
  }, []);
  const t = (a: number, b: number) => interpolate(f, [a, b], [0, 1], clamp);
  const pA = 1 - t(470, 510), pB = t(490, 530) * (1 - t(1130, 1170)), pC = t(1150, 1190);
  const ratio = interpolate(f, [150, 400], [2.1, 1.3], {...clamp, easing: Easing.inOut(Easing.quad)});
  const year = Math.round(interpolate(f, [150, 400], [2020, 2070], clamp));
  const slam = (t0: number) => interpolate(f, [t0, t0 + 20], [1.7, 1], {...clamp, easing: Easing.out(Easing.back(1.7))});
    const CAM: number[][] = [[0,960,540,1.04],[110,330,370,1.4],[230,340,380,1.43],[350,960,540,1.05],[560,540,480,1.34],[720,780,480,1.38],[880,970,490,1.42],[1000,960,680,1.2],[1140,950,690,1.22],[1260,650,620,1.36],[1400,660,630,1.38],[1500,1400,650,1.34],[1600,1420,660,1.36],[1700,1480,790,1.4],[1761,1300,700,1.2]];
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

  
  const bar = (t0: number) => interpolate(f, [t0, t0 + 40], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const full = Math.floor(ratio), frac = ratio - full;
  const bob = 0;

  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(4px) brightness(0.72) saturate(1.08)'}}/>
            <div style={{position: 'absolute', left: 960 - SAT_W / 2 + interpolate(f, [0, 1761], [45, -45], clamp), top: 540 - SAT_H / 2 - 40 + interpolate(f, [0, 1761], [-20, 25], clamp),
        width: SAT_W, height: SAT_H, opacity: t(0, 25),
        transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 438.6) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${interpolate(f, [0, 700, 1300, 1761], [1.56, 1.64, 1.56, 1.68], clamp)})`, transformOrigin: '50% 46%'}}>
        <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.72)'}}/>
        <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
          {M.map((p) => (
            <path key={p.id} d={p.d} fill="rgba(8,14,22,0.55)" stroke="rgba(255,255,255,0.18)" strokeWidth={1}/>
          ))}
        </svg>
      </div>
      <div style={{position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0.1) 40%, rgba(0,0,0,0.78) 100%)'}}/>

      <div style={{position: 'absolute', top: 52, left: 86}}>
        <div style={{fontSize: 30, fontWeight: 900, color: CRIM, letterSpacing: 5, opacity: t(10, 35)}}>ACT 3</div>
        <div style={{fontFamily: LUCK, fontSize: 80, color: '#fff', lineHeight: 1.0, opacity: t(10, 35),
          textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>THE BILL</div>
      </div>

      {pA > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pA}}>
          {Array.from({length: full}, (_, i) => (
            <Puppet key={i} src="puppets/worker.png" x={600 + i * 190} y={430 + (i % 2) * 6 + bob} h={250} rot={i % 2 ? 2 : -2}
              o={t(60 + i * 30, 85 + i * 30)}/>
          ))}
          {frac > 0.03 && <Puppet src="puppets/worker.png" x={600 + full * 190} y={430 + bob} h={250} frac={frac} rot={1.5}/>}
          <div style={{position: 'absolute', left: 1220, top: 420, bottom: 340, width: 0,
            borderLeft: '3px dashed rgba(174,196,218,0.6)'}}/>
          <Puppet src="puppets/senior.png" x={1310} y={416 - bob} h={272}/>
          <div style={{position: 'absolute', top: 250, left: 86}}>
            <div style={{fontSize: 26, fontWeight: 800, color: GRY, letterSpacing: 3}}>WORKERS PER SENIOR (65+)</div>
            <div style={{fontSize: 124, fontWeight: 900, color: ratio < 1.6 ? '#ff5a6e' : '#fff', lineHeight: 1,
              textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>{ratio.toFixed(1)}</div>
            <div style={{fontSize: 46, fontWeight: 900, color: YEL}}>{year}</div>
          </div>
          <div style={{position: 'absolute', top: 780, left: 480, border: '3px dashed ' + GRY, borderRadius: 12,
            padding: '10px 24px', opacity: t(130, 160), background: 'rgba(5,8,13,0.55)'}}>
            <span style={{fontSize: 24, fontWeight: 800, color: GRY}}>PROJECTION — IPSS MEDIUM SCENARIO · ALL RESIDENTS</span>
          </div>
        </div>
      )}

      {pB > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pB}}>
          <div style={{position: 'absolute', top: 240, left: 86, fontSize: 32, fontWeight: 900, color: '#fff', letterSpacing: 1,
            textShadow: '0 4px 14px rgba(0,0,0,0.8)'}}>
            WORKING-AGE PEOPLE <span style={{color: GRY, fontSize: 24, fontWeight: 700}}>(15–64, all residents)</span>
          </div>
          {[{y: 330, yr: '2032', v: 'BELOW 70M', d: 600, r: -1.5},
            {y: 490, yr: '2043', v: 'BELOW 60M', d: 680, r: 1},
            {y: 650, yr: '2062', v: 'BELOW 50M', d: 780, r: -1}].map((m, i) => (
            <div key={i} style={{position: 'absolute', top: m.y, left: 86 + i * 230, opacity: f > m.d ? 1 : 0,
              transform: `scale(${slam(m.d)}) rotate(${m.r}deg)`, transformOrigin: 'left center',
              border: '4px dashed ' + CRIM, borderRadius: 14, background: 'rgba(8,14,24,0.92)', padding: '14px 30px',
              boxShadow: '0 12px 28px rgba(0,0,0,0.55)'}}>
              <span style={{fontFamily: LUCK, fontSize: 42, color: YEL}}>{m.yr}</span>
              <span style={{fontSize: 40, fontWeight: 900, color: '#fff'}}>  —  {m.v}</span>
            </div>
          ))}
          <div style={{position: 'absolute', top: 840, left: 86, border: '3px dashed ' + GRY, borderRadius: 12,
            padding: '10px 24px', opacity: t(950, 975), background: 'rgba(5,8,13,0.55)'}}>
            <span style={{fontSize: 24, fontWeight: 800, color: GRY}}>DOTTED = PROJECTION, NOT FATE · IPSS MEDIUM SCENARIO</span>
          </div>
        </div>
      )}

      {pC > 0.01 && (
        <div style={{position: 'absolute', inset: 0, opacity: pC}}>
          <div style={{position: 'absolute', top: 225, left: 86}}>
            <span style={{fontSize: 100, fontWeight: 900, color: '#fff', textShadow: '0 6px 20px rgba(0,0,0,0.7)'}}>9.0M</span>
            <span style={{fontSize: 34, fontWeight: 900, color: '#ff5a6e'}}>  EMPTY HOMES — 13.8% OF ALL OF JAPAN</span>
          </div>
          {[{v: 4.44, n: 'FOR RENT', c: '#7e99b4', d: 1230},
            {v: 3.86, n: 'TRULY ABANDONED', c: CRIM, d: 1290},
            {v: 0.38, n: 'SECOND HOMES', c: '#7e99b4', d: 1350},
            {v: 0.33, n: 'FOR SALE', c: '#7e99b4', d: 1390}].map((b, i) => (
            <div key={i} style={{position: 'absolute', top: 390 + i * 92, left: 86, opacity: f > b.d ? 1 : 0}}>
              <div style={{fontSize: 24, fontWeight: 900, color: b.c === CRIM ? '#ff8093' : GRY}}>
                {b.n} — {b.v.toFixed(2)}M
              </div>
              <div style={{width: `${b.v * 240 * bar(b.d)}px`, height: 34, background: b.c, borderRadius: 8, marginTop: 6,
                boxShadow: '0 6px 16px rgba(0,0,0,0.5)'}}/>
            </div>
          ))}
          <div style={{position: 'absolute', top: 420, right: 100, width: 520, opacity: t(1480, 1510)}}>
            <div style={{background: '#fff', borderRadius: 14, padding: '20px 28px', transform: 'rotate(-2deg)',
              boxShadow: '0 14px 30px rgba(0,0,0,0.6)'}}>
              <div style={{fontSize: 28, fontWeight: 900, color: INK}}>65.0M HOMES</div>
              <div style={{fontSize: 28, fontWeight: 900, color: CRIM}}>vs 56.2M HOUSEHOLDS</div>
              <div style={{fontSize: 22, fontWeight: 700, color: '#44546a', marginTop: 6}}>Japan already has more homes than households</div>
            </div>
            <div style={{background: 'rgba(5,8,13,0.7)', border: '2px solid #4a627c', borderRadius: 14,
              padding: '16px 28px', marginTop: 20, opacity: t(1580, 1610), transform: 'rotate(1deg)'}}>
              <span style={{fontSize: 25, fontWeight: 800, color: '#fff'}}>EVEN TOKYO: 896.5K VACANT (10.9%)</span>
            </div>
          </div>
        </div>
      )}

      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
        {f < 1150 ? 'Source: IPSS, Population Projections for Japan (2023), medium variant'
                 : 'Source: MIC Housing and Land Survey, 2023'}
      </div>
    
      {f > 340 && pA > 0.01 && (
        <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none', opacity: pA}}>
          <ellipse cx={212} cy={348} rx={155} ry={72} fill="none" stroke="#e8273c" strokeWidth={6}
            transform="rotate(-4 212 348)" pathLength={100} strokeDasharray={100}
            strokeDashoffset={100 - 100 * t(340, 385)} strokeLinecap="round"/>
        </svg>
      )}
      {pC > 0.01 && f > 1300 && (
        <Img src={staticFile('photos/akiya-bill-alt.png')} style={{position: 'absolute', right: 100, top: 740, width: 360,
          opacity: pC * t(1300, 1320),
          transform: `scale(${interpolate(f, [1300, 1324], [1.5, 1], clamp)}) rotate(1deg)`, transformOrigin: 'right top',
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))', border: '8px solid #f1eee4', padding: 6, background: '#f1eee4'}}/>
      )}
      </AbsoluteFill>
  );
};
