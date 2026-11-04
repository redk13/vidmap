import React, {useMemo} from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import pyr from '../data/pyramids.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {loadFont as loadLuck} from '@remotion/google-fonts/LuckiestGuy';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: LUCK} = loadLuck();
const {fontFamily: MONT} = loadMont();
const CRIM = '#e8273c', BLUE = '#2f86ff', INK = '#101418', YEL = '#ffd60a', GRN = '#49e07c';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const N = pyr.meta.labels.length;

const toPath = (geom: any): string => {
  const ring = (r: number[][]) => r.map((c, i) => {
    const [x, y] = lonLatToPx(c[0], c[1]);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};

const Pyramid: React.FC<{
  cx: number; top: number; name: string; color: string; colorF: string;
  male: number[]; female: number[]; total: number; f: number; delay: number;
  highlight: [number, number]; hiColor: string; maxPct: number;
}> = ({cx, top, name, color, colorF, male, female, total, f, delay, highlight, hiColor, maxPct}) => {
  const sum = male.reduce((a, b) => a + b, 0) + female.reduce((a, b) => a + b, 0);
  const barH = 28, gap = 6, axisW = 76, maxW = 300;
  const rows = [];
  for (let i = 0; i < N; i++) {
    const yi = top + (N - 1 - i) * (barH + gap);
    const grow = interpolate(f, [delay + i * 5, delay + 28 + i * 5], [0, 1], clamp);
    const breathe = 1;
    const wM = (100 * male[i] / sum / maxPct) * maxW * grow * breathe;
    const wF = (100 * female[i] / sum / maxPct) * maxW * grow * breathe;
    const hi = i >= highlight[0] && i <= highlight[1];
    const hiOn = hi && f > 280;
    rows.push(
      <g key={i}>
        <rect x={cx - axisW / 2 - wM} y={yi} width={wM} height={barH} rx={4} fill={color}
          stroke={hiOn ? hiColor : 'none'} strokeWidth={hiOn ? 3 : 0}/>
        <rect x={cx + axisW / 2} y={yi} width={wF} height={barH} rx={4} fill={colorF}
          stroke={hiOn ? hiColor : 'none'} strokeWidth={hiOn ? 3 : 0}/>
        {(i % 4 === 0 || i === N - 1) && (
          <text x={cx} y={yi + 20} textAnchor="middle" fontSize={16} fill="#cfe0f0" fontWeight={800} fontFamily={MONT}>
            {pyr.meta.labels[i]}
          </text>
        )}
      </g>
    );
  }
  const hdr = interpolate(f, [delay - 10, delay + 15], [0, 1], clamp);
  const pop = interpolate(f, [delay - 10, delay + 10], [1.5, 1], clamp);
  return (
    <g>
      <g opacity={hdr} transform={`translate(${cx} ${top - 58}) scale(${pop}) rotate(-2)`}>
        <rect x={-215} y={-32} rx={12} width={430} height={62} fill={color}
          style={{filter: 'drop-shadow(0 10px 22px rgba(0,0,0,0.55))'}}/>
        <text x={0} y={14} textAnchor="middle" fontSize={38} fill="#fff" fontFamily={LUCK}>
          {name} — {(total / 1000).toFixed(1)}M
        </text>
      </g>
      {rows}
    </g>
  );
};

// PYRAMIDS V2 — ONE COUNTRY, TWO JAPANS (652f) · satellite base + collage
export const PyramidsV2: React.FC = () => {
  const f = useCurrentFrame();
  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    return (fc.features as any[]).map((p) => ({id: p.properties.id, d: toPath(p.geometry)}));
  }, []);
  const fadeIn = interpolate(f, [0, 25], [0, 1], clamp);
    const panX = interpolate(f, [0, 652], [-35, 35], clamp);
  const panYp = interpolate(f, [0, 652], [20, -30], clamp);
  const CAM: number[][] = [[0,960,540,1.03],[90,420,630,1.3],[200,400,640,1.33],[290,1660,850,1.35],[380,1650,840,1.37],[450,960,840,1.4],[560,960,830,1.43],[652,960,560,1.05]];
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

  const title = interpolate(f, [5, 35], [0, 1], clamp);
  const chip1 = interpolate(f, [360, 378], [0, 1], clamp);
  const chip2 = interpolate(f, [410, 428], [0, 1], clamp);
  const maxPct = 4.6;
  const pulse = 0.78;
  const fillFor = (id: number): string => {
    if (id === 13) return `rgba(232,39,60,${pulse})`;
    if (id === 47) return `rgba(47,134,255,${pulse})`;
    return 'rgba(8,14,22,0.52)';
  };
  return (
    <AbsoluteFill style={{backgroundColor: '#05080d', fontFamily: MONT, overflow: 'hidden'}}>
      <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', left: -120, top: -180,
        width: 2160, height: 2160, objectFit: 'cover', filter: 'blur(4px) brightness(0.72) saturate(1.08)'}}/>
            <div style={{position: 'absolute', left: 960 - SAT_W / 2 + panX, top: 540 - SAT_H / 2 - 40 + panYp,
        width: SAT_W, height: SAT_H, opacity: fadeIn,
        transform: `translate(${(cox - 960) * (1 - cs)}px, ${(coy - 438.6) * (1 - cs)}px) scale(${cs}) perspective(1600px) rotateX(35deg) scale(${interpolate(f, [0, 652], [1.52, 1.68], clamp)})`, transformOrigin: '50% 46%'}}>
        <Img src={staticFile('japan-sat.jpg')} style={{position: 'absolute', width: SAT_W, height: SAT_H, filter: 'brightness(0.72)'}}/>
        <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0}}>
          {M.map((p) => (
            <path key={p.id} d={p.d} fill={fillFor(p.id)} stroke="rgba(255,255,255,0.22)" strokeWidth={1}/>
          ))}
        </svg>
      </div>
      <div style={{position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 46%, rgba(0,0,0,0.72) 100%)'}}/>

      <svg width={1920} height={1080} style={{position: 'absolute', top: 0, left: 0}}>
        <Pyramid cx={430} top={268} name="TOKYO" color={CRIM} colorF="#ff8093"
          male={pyr.tokyo.male} female={pyr.tokyo.female} total={pyr.tokyo.total}
          f={f} delay={50} highlight={[4, 7]} hiColor={YEL} maxPct={maxPct}/>
        <Pyramid cx={1490} top={268} name="OKINAWA" color={BLUE} colorF="#8fc6ff"
          male={pyr.okinawa.male} female={pyr.okinawa.female} total={pyr.okinawa.total}
          f={f} delay={80} highlight={[0, 2]} hiColor={GRN} maxPct={maxPct}/>
      </svg>

      {/* center stat stickers */}
      <div style={{position: 'absolute', left: 960, top: 150, opacity: chip1,
        transform: `translateX(-50%) rotate(-2deg) scale(${interpolate(f, [360, 378], [1.5, 1], clamp)})`}}>
        <div style={{background: YEL, borderRadius: 12, padding: '12px 26px', boxShadow: '0 12px 28px rgba(0,0,0,0.6)', textAlign: 'center'}}>
          <div style={{fontWeight: 900, fontSize: 24, color: INK, whiteSpace: 'nowrap'}}>TOKYO AGES 20–39</div>
          <div style={{fontWeight: 900, fontSize: 36, color: INK, whiteSpace: 'nowrap'}}>27.2% OF THE CITY</div>
        </div>
      </div>
      <div style={{position: 'absolute', left: 960, top: 298, opacity: chip2,
        transform: `translateX(-50%) rotate(1.5deg) scale(${interpolate(f, [410, 428], [1.5, 1], clamp)})`}}>
        <div style={{background: '#fff', borderRadius: 12, padding: '12px 26px', boxShadow: '0 12px 28px rgba(0,0,0,0.6)', textAlign: 'center'}}>
          <div style={{fontWeight: 900, fontSize: 24, color: INK, whiteSpace: 'nowrap'}}>KIDS UNDER 15</div>
          <div style={{fontWeight: 900, fontSize: 31, whiteSpace: 'nowrap'}}>
            <span style={{color: BLUE}}>OKINAWA 15.8%</span> <span style={{color: INK}}>vs</span> <span style={{color: CRIM}}>TOKYO 10.5%</span>
          </div>
        </div>
      </div>

      <div style={{position: 'absolute', top: 44, width: '100%', textAlign: 'center', opacity: title, fontFamily: LUCK}}>
        <span style={{fontSize: 68, color: '#fff', textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>ONE COUNTRY. </span>
        <span style={{fontSize: 68, color: YEL, textShadow: '0 6px 20px rgba(0,0,0,0.8)'}}>TWO JAPANS.</span>
      </div>
      <div style={{position: 'absolute', bottom: 26, right: 42, fontSize: 19, color: '#9db4ca', fontWeight: 700}}>
        Source: Statistics Bureau of Japan — Population Estimates, Oct 1, 2024 · Total population
      </div>
    
      {f > 440 && (
        <Img src={staticFile('photos/okinawa-kids.png')} style={{position: 'absolute', left: '50%', top: 788, width: 360,
          opacity: interpolate(f, [440, 458], [0, 1], clamp),
          transform: `translateX(-50%) scale(${interpolate(f, [440, 462], [1.5, 1], clamp)}) rotate(-1deg)`,
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.65))'}}/>
      )}
      
      {f > 200 && (
        <Img src={staticFile('puppets/senior.png')} style={{position: 'absolute', height: 250,
          left: interpolate(f, [200, 245], [-280, 95], clamp),
          top: 752,
          opacity: interpolate(f, [200, 220], [0, 1], clamp),
          filter: 'drop-shadow(0 12px 20px rgba(0,0,0,0.6))'}}/>
      )}
      {f > 240 && (
        <Img src={staticFile('puppets/youth-pyramid-alt.png')} style={{position: 'absolute', height: 235,
          left: interpolate(f, [240, 285], [2160, 1655], clamp),
          top: 765,
          opacity: interpolate(f, [240, 260], [0, 1], clamp),
          transform: 'scaleX(-1)',
          filter: 'drop-shadow(0 12px 20px rgba(0,0,0,0.6))'}}/>
      )}
      </AbsoluteFill>
  );
};
