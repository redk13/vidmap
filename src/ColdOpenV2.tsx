import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {feature} from 'topojson-client';
import type {FeatureCollection} from 'geojson';
import japanTopo from '../data/japan.json';
import tokyo23 from '../data/tokyo23.json';
import {lonLatToPx, SAT_W, SAT_H} from './sat';
import {lonLatToPx2, SAT2_W, SAT2_H} from './sat2';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: MONT} = loadMont('normal', {
  weights: ['500', '600', '700', '800', '900'],
  subsets: ['latin'],
});

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const lin = {...clamp, easing: Easing.linear};
const easeOut = {...clamp, easing: Easing.out(Easing.cubic)};

const BH16 = new Set([
  'Shinjuku', 'Bunkyo', 'Taito', 'Sumida', 'Shinagawa', 'Meguro', 'Ota', 'Setagaya',
  'Shibuya', 'Nakano', 'Suginami', 'Toshima', 'Kita', 'Arakawa', 'Itabashi', 'Nerima',
]);

const pathWith = (geom: any, proj: (lon: number, lat: number) => [number, number]): string => {
  const ring = (r: number[][]) =>
    r
      .map((c, i) => {
        const [x, y] = proj(c[0], c[1]);
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join('') + 'Z';
  if (geom.type === 'Polygon') return geom.coordinates.map(ring).join('');
  return geom.coordinates.map((p: number[][][]) => p.map(ring).join('')).join('');
};

const centroidOf = (geom: any, proj: (lon: number, lat: number) => [number, number]): [number, number] => {
  let best: number[][] = [];
  const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
  for (const p of polys) if (p[0].length > best.length) best = p[0];
  let sx = 0, sy = 0;
  for (const c of best) {
    const [x, y] = proj(c[0], c[1]);
    sx += x;
    sy += y;
  }
  return [sx / best.length, sy / best.length];
};

// Deterministic seeded urban night-light clusters around Greater Tokyo
const makeNightLights = (
  proj: (lon: number, lat: number) => [number, number],
  count: number,
  spreadLon: number,
  spreadLat: number,
) => {
  let s = 1337;
  const rnd = () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
  const hubs: [number, number, number][] = [
    [139.70, 35.69, 1.0],  // Shinjuku / Central Tokyo
    [139.76, 35.68, 0.95], // Chiyoda / Ginza
    [139.64, 35.45, 0.65], // Yokohama
    [139.63, 35.90, 0.55], // Saitama
    [140.01, 35.69, 0.50], // Chiba / Funabashi
    [139.48, 35.66, 0.45], // Western Tama
  ];
  const pts: {x: number; y: number; r: number; a: number; warm: boolean}[] = [];
  for (let i = 0; i < count; i++) {
    const h = hubs[i % hubs.length];
    const u1 = Math.max(1e-4, rnd());
    const u2 = rnd();
    const g0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    const g1 = Math.sqrt(-2 * Math.log(u1)) * Math.sin(2 * Math.PI * u2);
    const lon = h[0] + g0 * spreadLon * h[2];
    const lat = h[1] + g1 * spreadLat * h[2];
    const [x, y] = proj(lon, lat);
    pts.push({
      x,
      y,
      r: 0.7 + rnd() * 1.9,
      a: (0.35 + rnd() * 0.65) * h[2],
      warm: rnd() > 0.25,
    });
  }
  return pts;
};

// COLD OPEN V9 — Kings & Generals Nocturnal Satellite + Spotlight + Unidirectional Ken Burns (1023f)
// Shot structure (hard cuts on VO sentence boundaries, 1 monotonic linear drift per shot, 0 reversals):
//   Shot 1 [0..185]    (0.00-6.17s):  Nocturnal Japan -> Tokyo spotlight ignites -> -918,253 appears steadily inside the map callout
//   Shot 2 [186..310]  (6.20-10.33s): Tighter Honshu lateral drift -> Vox scale ruler (-918,253 vs San Francisco 808,988)
//   Shot 3 [311..452]  (10.37-15.07s): Archipelago sweep -> 46/47 prefectures darken & turn crimson; Tokyo alone glows gold
//   Shot 4 [453..702]  (15.10-23.40s): High-res z10 Kanto nocturnal satellite -> Tokyo 23 wards spotlight +0.09% + K&G framed card -> "NOT A LIFEBOAT" crimson twist
//   Shot 5 [703..1023] (23.43-34.10s): Council black-hole verdict on archipelago + "WHY TOKYO IS DELETING JAPAN" title
export const ColdOpenV2: React.FC = () => {
  const f = useCurrentFrame();

  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    const rawPolys = (fc.features as any[]).map((p) => {
      let g = p.geometry;
      if (p.properties.id === 13 && g.type === 'MultiPolygon') {
        let best = g.coordinates[0];
        for (const poly of g.coordinates) {
          if (JSON.stringify(poly).length > JSON.stringify(best).length) best = poly;
        }
        g = {type: 'Polygon', coordinates: best};
      }
      const c = centroidOf(g, lonLatToPx);
      return {id: p.properties.id as number, d: pathWith(g, lonLatToPx), c};
    });

    // Sort non-Tokyo prefectures SW -> NE (Kyushu -> Hokkaido) for clean directional sweep
    const nonTokyo = rawPolys
      .filter((p) => p.id !== 13)
      .sort((a, b) => (a.c[0] - a.c[1]) - (b.c[0] - b.c[1]));
    const sweepRank = new Map<number, number>();
    nonTokyo.forEach((p, idx) => sweepRank.set(p.id, idx + 1)); // 1..46

    const T = lonLatToPx(139.69, 35.68);
    const OSAKA = lonLatToPx(135.50, 34.69);
    const NAGOYA = lonLatToPx(136.91, 35.18);
    const FUKUOKA = lonLatToPx(130.40, 33.59);
    const SENDAI = lonLatToPx(140.87, 38.27);

    const wfc = tokyo23 as unknown as FeatureCollection;
    const wards2 = (wfc.features as any[]).map((w) => ({
      n: w.properties.n as string,
      bh: BH16.has(w.properties.n),
      d: pathWith(w.geometry, lonLatToPx2),
      c: centroidOf(w.geometry, lonLatToPx2),
    }));
    const T2 = lonLatToPx2(139.69, 35.68);
    const SHINJUKU2 = wards2.find((w) => w.n === 'Shinjuku')?.c ?? T2;

    const lightsZ6 = makeNightLights(lonLatToPx, 110, 0.22, 0.18);
    const lightsZ10 = makeNightLights(lonLatToPx2, 220, 0.16, 0.13);

    return {
      polys: rawPolys,
      sweepRank,
      T,
      OSAKA,
      NAGOYA,
      FUKUOKA,
      SENDAI,
      wards2,
      T2,
      SHINJUKU2,
      lightsZ6,
      lightsZ10,
    };
  }, []);

  // Determine active shot (hard cuts only — zero camera reversals inside any shot)
  const shot =
    f <= 185 ? 1 :
    f <= 310 ? 2 :
    f <= 452 ? 3 :
    f <= 702 ? 4 : 5;

  // Unidirectional linear Ken Burns per shot: [cx, cy, zoom]
  let cx = 855, cy = 780, Z = 2.0;
  if (shot === 1) {
    // Slow push-in onto nocturnal Japan & glowing Tokyo
    cx = interpolate(f, [0, 185], [840, 880], lin);
    cy = interpolate(f, [0, 185], [772, 790], lin);
    Z = interpolate(f, [0, 185], [1.94, 2.02], lin);
  } else if (shot === 2) {
    // Pure eastward lateral tracking glide along Honshu/Pacific coast
    cx = interpolate(f, [186, 310], [880, 900], lin);
    cy = interpolate(f, [186, 310], [790, 810], lin);
    Z = interpolate(f, [186, 310], [2.02, 2.06], lin);
  } else if (shot === 3) {
    // Slow northeastward climb up the Japanese archipelago as 46 prefectures turn crimson
    cx = interpolate(f, [311, 452], [900, 920], lin);
    cy = interpolate(f, [311, 452], [810, 755], lin);
    Z = interpolate(f, [311, 452], [2.06, 2.10], lin);
  } else if (shot === 4) {
    // High-res z10 Kanto plane: slow push-in toward Tokyo's 23 wards
    cx = interpolate(f, [453, 702], [790, 852], lin);
    cy = interpolate(f, [453, 702], [818, 838], lin);
    Z = interpolate(f, [453, 702], [2.10, 2.16], lin);
  } else {
    // Shot 5: slow pull-out over darkened Japan for Black Hole reveal & title
    cx = interpolate(f, [703, 1023], [930, 880], lin);
    cy = interpolate(f, [703, 1023], [805, 775], lin);
    Z = interpolate(f, [703, 1023], [2.26, 1.96], lin);
  }

  // Opening fade from deep black (first 16 frames = 0.53s)
  const masterFade = interpolate(f, [0, 16], [0, 1], clamp);

  // Shot 1 animations
  const tokyoGlow1 = interpolate(f, [6, 38], [0, 1], easeOut);
  const burnIn = interpolate(f, [22, 48], [0, 1], easeOut);
  // Static counter reveal: no rolling digits, glow flicker, pop, or pulse.
  const emberFlicker = 1.0;

  // Shot 2 animations (San Francisco Vox ruler comparison)
  const sfIn = interpolate(f, [190, 212], [0, 1], easeOut);
  const sfBar1 = interpolate(f, [192, 224], [0, 248], easeOut);
  const sfBar2 = interpolate(f, [206, 240], [0, 218], easeOut);
  const sfGone = interpolate(f, [264, 286], [0, 1], easeOut);

  // Shot 3 animations (46 of 47 prefectures crimson sweep)
  const sweepProgress = interpolate(f, [315, 422], [0, 46], clamp);
  const prefCount = Math.min(46, Math.round(sweepProgress));
  const shot3LabelOp = interpolate(f, [316, 336], [0, 1], easeOut);

  // Shot 4 animations (z10 Kanto Spotlight -> +0.09% -> K&G card -> "NOT A LIFEBOAT" twist)
  const kantoGlow = interpolate(f, [456, 495], [0.35, 1], easeOut);
  const tokyoIgnite4 = interpolate(f, [504, 526], [0, 1], easeOut);
  const cardOp = Math.min(
    interpolate(f, [510, 528], [0, 1], easeOut),
    interpolate(f, [604, 620], [1, 0], clamp),
  );
  const twistT = interpolate(f, [620, 652], [0, 1], easeOut);

  // Shot 5 animations (703..1023f)
  const councilOp = Math.min(
    interpolate(f, [714, 736], [0, 1], easeOut),
    interpolate(f, [872, 892], [1, 0], clamp),
  );
  const bhPulse5 = interpolate(f, [804, 855], [0, 1], easeOut);
  const titleOp = interpolate(f, [888, 918], [0, 1], easeOut);

  // Year displayed in permanent K&G top-right plaque
  const yearText = '2025';

  // Prefecture fill helper for z6 Japan map (Shots 1, 2, 3, 5)
  const getPrefFill = (id: number): string => {
    if (id === 13) {
      if (shot === 5 && bhPulse5 > 0) {
        return `rgba(225, 29, 72, ${0.52 + 0.36 * bhPulse5})`;
      }
      return `rgba(251, 191, 36, ${0.62 * (shot === 1 ? tokyoGlow1 : 1)})`;
    }
    if (shot === 1) {
      return 'rgba(10, 18, 32, 0.18)';
    }
    if (shot === 2) {
      return 'rgba(136, 24, 40, 0.20)';
    }
    if (shot === 3) {
      const rank = M.sweepRank.get(id) ?? 46;
      const lit = interpolate(sweepProgress, [rank - 1.2, rank + 0.4], [0, 1], clamp);
      const baseA = 0.22 * (1 - lit);
      const redA = (id % 2 === 0 ? 0.48 : 0.40) * lit;
      return lit > 0.02
        ? `rgba(185, 28, 48, ${redA.toFixed(3)})`
        : `rgba(10, 18, 32, ${baseA.toFixed(3)})`;
    }
    // Shot 5
    return 'rgba(150, 24, 42, 0.32)';
  };

  const getPrefStroke = (id: number): string => {
    if (id === 13) return 'rgba(254, 240, 138, 0.95)';
    if (shot === 3) {
      const rank = M.sweepRank.get(id) ?? 46;
      if (sweepProgress >= rank) return 'rgba(255, 145, 156, 0.52)';
    }
    if (shot === 5) return 'rgba(255, 165, 176, 0.62)';
    return 'rgba(205, 222, 244, 0.58)';
  };

  return (
    <AbsoluteFill style={{backgroundColor: '#070d18', opacity: masterFade, overflow: 'hidden'}}>
      {/* SAFETY FULL-BLEED BACKDROP (V8 guarantee preserved + nocturnal slate palette) */}
      <Img
        src={staticFile(shot === 4 ? 'kanto-sat.jpg' : 'japan-sat.jpg')}
        style={{
          position: 'absolute',
          left: -120,
          top: -120,
          width: 2160,
          height: 1320,
          objectFit: 'cover',
          filter: 'blur(14px) brightness(0.62) saturate(0.55)',
        }}
      />

      {/* ================= SHOTS 1, 2, 3, 5: NOCTURNAL Z6 JAPAN SATELLITE STAGE ================= */}
      {shot !== 4 && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: SAT_W,
            height: SAT_H,
            transformOrigin: '0 0',
            transform: `translate(${(960 - cx * Z).toFixed(2)}px, ${(540 - cy * Z).toFixed(2)}px) scale(${Z.toFixed(4)})`,
          }}
        >
          {/* Nocturnal desaturated Kings & Generals satellite base — terrain & bathymetry clearly visible */}
          <Img
            src={staticFile('japan-sat.jpg')}
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: SAT_W,
              height: SAT_H,
              filter: 'brightness(0.90) contrast(1.08) saturate(0.68)',
            }}
          />
          {/* Subtle cool night-blue atmospheric grade */}
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: SAT_W,
              height: SAT_H,
              background: 'rgba(6, 14, 28, 0.08)',
            }}
          />

          <svg width={SAT_W} height={SAT_H} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
            <defs>
              <radialGradient id="tokyoSpotGold" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#fffbeb" stopOpacity="0.95" />
                <stop offset="18%" stopColor="#fbbf24" stopOpacity="0.72" />
                <stop offset="48%" stopColor="#d97706" stopOpacity="0.28" />
                <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="tokyoSpotCrimson" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ffe4e6" stopOpacity="0.95" />
                <stop offset="22%" stopColor="#e11d48" stopOpacity="0.75" />
                <stop offset="55%" stopColor="#9f1239" stopOpacity="0.30" />
                <stop offset="100%" stopColor="#881337" stopOpacity="0" />
              </radialGradient>
              <filter id="emberGlow" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="4.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Subtle K&G spaced geographic sea/island labels on map */}
            <text
              x={688}
              y={612}
              fill="rgba(205, 224, 248, 0.28)"
              fontFamily={MONT}
              fontWeight={600}
              fontSize={10.5}
              letterSpacing={5.5}
              textAnchor="middle"
              transform="rotate(-28, 688, 612)"
            >
              SEA OF JAPAN
            </text>
            {shot !== 2 && (
              <text
                x={1145}
                y={972}
                fill="rgba(205, 224, 248, 0.24)"
                fontFamily={MONT}
                fontWeight={600}
                fontSize={10.5}
                letterSpacing={6}
                textAnchor="middle"
              >
                PACIFIC OCEAN
              </text>
            )}

            {/* 47 Prefecture Choropleth + Crisp Hairline Borders */}
            {M.polys.map((p) => (
              <path
                key={p.id}
                d={p.d}
                fill={getPrefFill(p.id)}
                stroke={getPrefStroke(p.id)}
                strokeWidth={p.id === 13 ? 1.15 : 0.55}
              />
            ))}

            {/* Orbital Night-Lights & Spotlight over Tokyo */}
            <g opacity={shot === 1 ? tokyoGlow1 : 1}>
              <circle
                cx={M.T[0]}
                cy={M.T[1]}
                r={shot === 5 && bhPulse5 > 0 ? 78 : 68}
                fill={shot === 5 && bhPulse5 > 0.3 ? 'url(#tokyoSpotCrimson)' : 'url(#tokyoSpotGold)'}
              />
              {M.lightsZ6.map((pt, idx) => (
                <circle
                  key={idx}
                  cx={pt.x}
                  cy={pt.y}
                  r={pt.r * 0.55}
                  fill={
                    shot === 5 && bhPulse5 > 0.4
                      ? '#fda4af'
                      : pt.warm
                        ? '#fde68a'
                        : '#fffbeb'
                  }
                  opacity={pt.a * 0.85}
                />
              ))}
              {/* Crisp pinpoint marker + Tokyo label */}
              <circle
                cx={M.T[0]}
                cy={M.T[1]}
                r={13}
                fill="none"
                stroke={shot === 5 && bhPulse5 > 0.3 ? 'rgba(251,113,133,0.65)' : 'rgba(253,224,71,0.65)'}
                strokeWidth={0.8}
                strokeDasharray="2.5 2"
              />
              <circle cx={M.T[0]} cy={M.T[1]} r={2.8} fill="#ffffff" />
              <line
                x1={M.T[0] + 9}
                y1={M.T[1] - 5}
                x2={M.T[0] + 34}
                y2={M.T[1] - 18}
                stroke="rgba(253, 224, 71, 0.80)"
                strokeWidth={0.9}
              />
              <text
                x={M.T[0] + 38}
                y={M.T[1] - 19}
                fill="#fef08a"
                fontFamily={MONT}
                fontWeight={800}
                fontSize={11.5}
                letterSpacing={2.8}
              >
                TOKYO
              </text>
            </g>

            {/* -------- SHOT 1 ON-MAP GRAPHIC: -918,253 BURNING ON THE MAP -------- */}
            {shot === 1 && burnIn > 0 && (
              <g opacity={burnIn}>
                {/* One bounded map callout: every counter line stays inside this plate. */}
                <rect
                  x={430}
                  y={650}
                  width={415}
                  height={120}
                  rx={5}
                  fill="rgba(8, 12, 20, 0.84)"
                  stroke="rgba(251, 113, 133, 0.58)"
                  strokeWidth={1}
                />
                {/* Subtle ember backlight directly on the Sea of Japan */}
                <ellipse
                  cx={710}
                  cy={712}
                  rx={135}
                  ry={52}
                  fill="rgba(225, 29, 72, 0.16)"
                  filter="url(#emberGlow)"
                />
                {/* Fine Vox measurement leader to Honshu */}
                <line
                  x1={818}
                  y1={715}
                  x2={896}
                  y2={758}
                  stroke="rgba(251, 113, 133, 0.55)"
                  strokeWidth={0.85}
                  strokeDasharray="3 2.5"
                />
                <circle cx={896} cy={758} r={2.2} fill="#fb7185" />

                <text
                  x={637}
                  y={716}
                  textAnchor="middle"
                  fontFamily={MONT}
                  fontWeight={900}
                  fontSize={52}
                  letterSpacing={-1}
                  fill="#fff1f2"
                  style={{
                    filter: `drop-shadow(0 0 ${8 * emberFlicker}px rgba(244, 63, 94, 0.85)) drop-shadow(0 4px 12px rgba(0,0,0,0.95))`,
                  }}
                >
                  −918,253
                </text>
                <text
                  x={637}
                  y={735}
                  textAnchor="middle"
                  fontFamily={MONT}
                  fontWeight={700}
                  fontSize={10.5}
                  letterSpacing={2.6}
                  fill="#fda4af"
                >
                  DEATHS MINUS BIRTHS · 2025
                </text>
                <line
                  x1={530}
                  y1={742}
                  x2={744}
                  y2={742}
                  stroke="rgba(244, 63, 94, 0.45)"
                  strokeWidth={0.9}
                />
                <text
                  x={637}
                  y={754}
                  textAnchor="middle"
                  fontFamily={MONT}
                  fontWeight={600}
                  fontSize={8.2}
                  letterSpacing={1.8}
                  fill="rgba(226, 232, 240, 0.68)"
                >
                  JAPANESE NATIONALS · 19TH STRAIGHT YEAR
                </text>
              </g>
            )}

            {/* -------- SHOT 2 ON-MAP GRAPHIC: VOX SCALE RULER (-918,253 vs SAN FRANCISCO) -------- */}
            {shot === 2 && sfIn > 0 && (
              <g opacity={sfIn}>
                {/* Subtle city markers along Honshu for geographic grounding */}
                {[
                  {pt: M.OSAKA, name: 'OSAKA'},
                  {pt: M.NAGOYA, name: 'NAGOYA'},
                ].map((c) => (
                  <g key={c.name} opacity={0.72}>
                    <circle cx={c.pt[0]} cy={c.pt[1]} r={1.8} fill="#e2e8f0" />
                    <text
                      x={c.pt[0]}
                      y={c.pt[1] - 6}
                      textAnchor="middle"
                      fontFamily={MONT}
                      fontWeight={600}
                      fontSize={7.5}
                      letterSpacing={2}
                      fill="rgba(226, 232, 240, 0.82)"
                    >
                      {c.name}
                    </text>
                  </g>
                ))}

                {/* Vox-style measured scale comparison cleanly over Pacific water */}
                <g transform="translate(835, 922)">
                  <rect
                    x={-14}
                    y={-24}
                    width={392}
                    height={102}
                    rx={3}
                    fill="rgba(6, 12, 24, 0.66)"
                    stroke="rgba(148, 163, 184, 0.24)"
                    strokeWidth={0.7}
                  />
                  <text
                    x={0}
                    y={-9}
                    fontFamily={MONT}
                    fontWeight={700}
                    fontSize={8.5}
                    letterSpacing={2.4}
                    fill="rgba(226, 232, 240, 0.85)"
                  >
                    12-MONTH POPULATION LOSS SCALE
                  </text>

                  {/* Bar 1: Japan 2025 loss (-918,253) */}
                  <rect
                    x={0}
                    y={0}
                    width={sfBar1}
                    height={13}
                    rx={1.5}
                    fill="rgba(225, 29, 72, 0.90)"
                    stroke="#fda4af"
                    strokeWidth={0.6}
                  />
                  <text
                    x={sfBar1 + 8}
                    y={10.5}
                    fontFamily={MONT}
                    fontWeight={900}
                    fontSize={13.5}
                    fill="#fff1f2"
                  >
                    −918,253
                  </text>
                  <text
                    x={0}
                    y={24}
                    fontFamily={MONT}
                    fontWeight={700}
                    fontSize={7.8}
                    letterSpacing={1.8}
                    fill="#fda4af"
                  >
                    JAPAN NATURAL DECLINE (2025)
                  </text>

                  {/* Bar 2: Entire City of San Francisco (~808,988) */}
                  <rect
                    x={0}
                    y={34}
                    width={sfBar2}
                    height={11}
                    rx={1.5}
                    fill={`rgba(148, 163, 184, ${(0.52 * (1 - 0.65 * sfGone)).toFixed(2)})`}
                    stroke="rgba(226, 232, 240, 0.72)"
                    strokeWidth={0.7}
                    strokeDasharray="2.5 2"
                  />
                  <text
                    x={sfBar2 + 8}
                    y={43}
                    fontFamily={MONT}
                    fontWeight={800}
                    fontSize={10.5}
                    fill={`rgba(226, 232, 240, ${(0.92 - 0.35 * sfGone).toFixed(2)})`}
                  >
                    808,988 · SAN FRANCISCO
                  </text>

                  {/* "GONE IN 12 MONTHS" Vox bracket */}
                  {sfGone > 0 && (
                    <g opacity={sfGone}>
                      <line x1={0} y1={54} x2={sfBar1} y2={54} stroke="#fbbf24" strokeWidth={0.95} />
                      <line x1={0} y1={50} x2={0} y2={58} stroke="#fbbf24" strokeWidth={0.95} />
                      <line x1={sfBar1} y1={50} x2={sfBar1} y2={58} stroke="#fbbf24" strokeWidth={0.95} />
                      <text
                        x={0}
                        y={67}
                        fontFamily={MONT}
                        fontWeight={800}
                        fontSize={8.8}
                        letterSpacing={1.9}
                        fill="#fde047"
                      >
                        BIGGER THAN SAN FRANCISCO — GONE IN 12 MONTHS
                      </text>
                    </g>
                  )}
                </g>
              </g>
            )}

            {/* -------- SHOT 3 ON-MAP GRAPHIC: 46 / 47 PREFECTURES SHRINKING -------- */}
            {shot === 3 && shot3LabelOp > 0 && (
              <g opacity={shot3LabelOp} transform="translate(920, 695)">
                <rect x={-380} y={-54} width={388} height={104} rx={5} fill="rgba(8,12,20,0.86)" stroke="rgba(251,113,133,0.48)" strokeWidth={0.9} />
                <text
                  x={0}
                  y={0}
                  textAnchor="end"
                  fontFamily={MONT}
                  fontWeight={900}
                  fontSize={48}
                  fill="#fff1f2"
                  style={{filter: 'drop-shadow(0 4px 14px rgba(0,0,0,0.95))'}}
                >
                  <tspan fill="#fb7185">{prefCount}</tspan>
                  <tspan fill="rgba(226,232,240,0.55)" fontSize={32}> / 47</tspan>
                </text>
                <text
                  x={0}
                  y={18}
                  textAnchor="end"
                  fontFamily={MONT}
                  fontWeight={700}
                  fontSize={10}
                  letterSpacing={2.4}
                  fill="#fda4af"
                >
                  PREFECTURES LOSING JAPANESE RESIDENTS
                </text>
                <line x1={-215} y1={25} x2={0} y2={25} stroke="rgba(251,113,133,0.42)" strokeWidth={0.8} />
                <text
                  x={0}
                  y={37}
                  textAnchor="end"
                  fontFamily={MONT}
                  fontWeight={600}
                  fontSize={8.2}
                  letterSpacing={2}
                  fill="#fde68a"
                >
                  SOLE EXCEPTION: TOKYO (+0.09%)
                </text>
              </g>
            )}

            {/* -------- SHOT 5 ON-MAP GRAPHIC: COUNCIL DOSSIER CALLOUT (703..1023f) -------- */}
            {shot === 5 && councilOp > 0 && (
              <g opacity={councilOp} transform="translate(790, 725)">
                <rect
                  x={-230}
                  y={-36}
                  width={230}
                  height={62}
                  rx={3}
                  fill="rgba(9, 13, 22, 0.88)"
                  stroke="rgba(244, 63, 94, 0.65)"
                  strokeWidth={1.1}
                />
                <rect x={-230} y={-36} width={3.5} height={62} fill="#f43f5e" />
                <text
                  x={-216}
                  y={-17}
                  fontFamily={MONT}
                  fontWeight={800}
                  fontSize={9.5}
                  letterSpacing={2}
                  fill="#fda4af"
                >
                  POPULATION STRATEGY COUNCIL
                </text>
                <text
                  x={-216}
                  y={-3}
                  fontFamily={MONT}
                  fontWeight={600}
                  fontSize={7.8}
                  letterSpacing={1.4}
                  fill="rgba(203, 213, 225, 0.82)"
                >
                  INDEPENDENT PRIVATE PANEL · 2024 REPORT
                </text>
                <text
                  x={-216}
                  y={15}
                  fontFamily={MONT}
                  fontWeight={900}
                  fontSize={12.5}
                  letterSpacing={1.8}
                  fill="#fff1f2"
                >
                  “DEMOGRAPHIC BLACK HOLE”
                </text>
                <line
                  x1={0}
                  y1={-4}
                  x2={M.T[0] - 802}
                  y2={M.T[1] - 725}
                  stroke="rgba(244, 63, 94, 0.65)"
                  strokeWidth={0.9}
                  strokeDasharray="3 2.5"
                />
              </g>
            )}
          </svg>
        </div>
      )}

      {/* ================= SHOT 4: HIGH-RES Z10 NOCTURNAL KANTO + TOKYO 23 WARDS ================= */}
      {shot === 4 && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: SAT2_W,
            height: SAT2_H,
            transformOrigin: '0 0',
            transform: `translate(${(960 - cx * Z).toFixed(2)}px, ${(540 - cy * Z).toFixed(2)}px) scale(${Z.toFixed(4)})`,
          }}
        >
          <Img
            src={staticFile('kanto-sat.jpg')}
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: SAT2_W,
              height: SAT2_H,
              filter: 'brightness(0.88) contrast(1.08) saturate(0.66)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: SAT2_W,
              height: SAT2_H,
              background: 'rgba(6, 13, 26, 0.08)',
            }}
          />

          <svg width={SAT2_W} height={SAT2_H} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
            <defs>
              <radialGradient id="kantoGold" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#fffbeb" stopOpacity="0.62" />
                <stop offset="35%" stopColor="#f59e0b" stopOpacity="0.28" />
                <stop offset="75%" stopColor="#b45309" stopOpacity="0.08" />
                <stop offset="100%" stopColor="#b45309" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="kantoCrimson" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#fda4af" stopOpacity="0.55" />
                <stop offset="42%" stopColor="#e11d48" stopOpacity="0.28" />
                <stop offset="100%" stopColor="#881337" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Subtle Kanto geographic labels */}
            <text
              x={992}
              y={992}
              textAnchor="middle"
              fontFamily={MONT}
              fontWeight={600}
              fontSize={9.5}
              letterSpacing={4.5}
              fill="rgba(186, 208, 235, 0.24)"
            >
              TOKYO BAY
            </text>
            <text
              x={615}
              y={665}
              textAnchor="middle"
              fontFamily={MONT}
              fontWeight={600}
              fontSize={9}
              letterSpacing={5}
              fill="rgba(186, 208, 235, 0.17)"
            >
              KANTO PLAIN
            </text>

            {/* Atmospheric Spotlight beneath the 23 wards */}
            <circle
              cx={892}
              cy={837}
              r={215}
              fill="url(#kantoGold)"
              opacity={kantoGlow * (1 - 0.72 * twistT)}
            />
            {twistT > 0 && (
              <circle cx={882} cy={835} r={205} fill="url(#kantoCrimson)" opacity={twistT} />
            )}

            {/* 23 Wards of Tokyo polygons: Golden Spotlight -> 16 Black-Hole Wards shift crimson on Twist */}
            {M.wards2.map((w) => {
              const isBH = w.bh;
              const goldA = 0.22 + 0.24 * tokyoIgnite4;
              const crimA = isBH ? 0.56 : 0.16;
              const r = Math.round(245 * (1 - twistT) + (isBH ? 225 : 70) * twistT);
              const g = Math.round(178 * (1 - twistT) + (isBH ? 29 : 80) * twistT);
              const b = Math.round(32 * (1 - twistT) + (isBH ? 62 : 105) * twistT);
              const a = goldA * (1 - twistT) + crimA * twistT;
              const strokeCol =
                twistT > 0.35 && isBH
                  ? `rgba(253, 164, 175, ${(0.45 + 0.4 * twistT).toFixed(2)})`
                  : `rgba(254, 240, 138, ${(0.38 + 0.42 * tokyoIgnite4).toFixed(2)})`;
              return (
                <path
                  key={w.n}
                  d={w.d}
                  fill={`rgba(${r}, ${g}, ${b}, ${a.toFixed(3)})`}
                  stroke={strokeCol}
                  strokeWidth={0.85}
                />
              );
            })}

            {/* Urban night-light stipple over Greater Tokyo */}
            <g opacity={kantoGlow}>
              {M.lightsZ10.map((pt, idx) => (
                <circle
                  key={idx}
                  cx={pt.x}
                  cy={pt.y}
                  r={pt.r * 0.65}
                  fill={twistT > 0.5 ? '#fecdd3' : pt.warm ? '#fde68a' : '#fffbeb'}
                  opacity={pt.a * (0.72 - 0.25 * twistT)}
                />
              ))}
            </g>

            {/* +0.09% ONLY GROWING PREFECTURE callout on right side of 23 wards */}
            {tokyoIgnite4 > 0 && (
              <g opacity={tokyoIgnite4 * (1 - 0.35 * twistT)}>
                <rect x={1020} y={706} width={260} height={94} rx={5} fill="rgba(8,12,20,0.86)" stroke="rgba(253,224,71,0.55)" strokeWidth={0.9} />
                <line
                  x1={978}
                  y1={792}
                  x2={1032}
                  y2={752}
                  stroke="#fde047"
                  strokeWidth={1.0}
                />
                <circle cx={978} cy={792} r={2.6} fill="#fef08a" />
                <text
                  x={1040}
                  y={742}
                  fontFamily={MONT}
                  fontWeight={800}
                  fontSize={11.5}
                  letterSpacing={2.8}
                  fill="#fef08a"
                >
                  TOKYO METROPOLIS
                </text>
                <text
                  x={1040}
                  y={774}
                  fontFamily={MONT}
                  fontWeight={900}
                  fontSize={34}
                  fill="#ffffff"
                  style={{filter: 'drop-shadow(0 3px 10px rgba(0,0,0,0.95))'}}
                >
                  +0.09%
                </text>
                <text
                  x={1040}
                  y={790}
                  fontFamily={MONT}
                  fontWeight={700}
                  fontSize={8.8}
                  letterSpacing={2.2}
                  fill="rgba(254, 240, 138, 0.90)"
                >
                  SOLE GROWING PREFECTURE
                </text>
              </g>
            )}

            {/* Leader line for K&G framed archival card (f=510..620) */}
            {cardOp > 0 && (
              <g opacity={cardOp}>
                <line
                  x1={726}
                  y1={812}
                  x2={M.SHINJUKU2[0]}
                  y2={M.SHINJUKU2[1]}
                  stroke="rgba(248, 250, 252, 0.78)"
                  strokeWidth={0.95}
                />
                <circle cx={M.SHINJUKU2[0]} cy={M.SHINJUKU2[1]} r={3} fill="#ffffff" />
              </g>
            )}

            {/* THE TWIST ON-MAP GRAPHIC (f=620..702): "NOT JAPAN'S LIFEBOAT" */}
            {twistT > 0 && (
              <g opacity={twistT}>
                <rect x={398} y={798} width={306} height={92} rx={5} fill="rgba(8,12,20,0.88)" stroke="rgba(244,63,94,0.52)" strokeWidth={0.9} />
                {/* Subtle dashed analytical reticle around Tokyo's 23 wards */}
                <circle
                  cx={890}
                  cy={838}
                  r={148}
                  fill="none"
                  stroke="rgba(244, 63, 94, 0.65)"
                  strokeWidth={1.1}
                  strokeDasharray="5 3.5"
                />
                <line
                  x1={742}
                  y1={838}
                  x2={700}
                  y2={838}
                  stroke="rgba(244, 63, 94, 0.78)"
                  strokeWidth={1.0}
                />
                <text
                  x={690}
                  y={828}
                  textAnchor="end"
                  fontFamily={MONT}
                  fontWeight={700}
                  fontSize={9.5}
                  letterSpacing={2.6}
                  fill="#fda4af"
                >
                  THE DEMOGRAPHIC PARADOX
                </text>
                <text
                  x={690}
                  y={855}
                  textAnchor="end"
                  fontFamily={MONT}
                  fontWeight={900}
                  fontSize={25}
                  letterSpacing={1.2}
                  fill="#fff1f2"
                  style={{filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.95))'}}
                >
                  NOT A LIFEBOAT
                </text>
                <text
                  x={690}
                  y={872}
                  textAnchor="end"
                  fontFamily={MONT}
                  fontWeight={600}
                  fontSize={8.5}
                  letterSpacing={1.8}
                  fill="rgba(226, 232, 240, 0.78)"
                >
                  16 OF 23 WARDS FLAGGED AT RISK
                </text>
              </g>
            )}
          </svg>

          {/* KINGS & GENERALS PINNED FRAMED ARCHIVAL CARD (motionless on map, crisp white border + caption bar) */}
          {cardOp > 0 && (
            <div
              style={{
                position: 'absolute',
                left: 506,
                top: 734,
                width: 220,
                opacity: cardOp,
                background: '#f8fafc',
                padding: 4,
                borderRadius: 2,
                boxShadow: '0 14px 34px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255,255,255,0.2)',
              }}
            >
              <Img
                src={staticFile('photos-src/tokyo-night.jpg')}
                style={{
                  width: '100%',
                  height: 124,
                  objectFit: 'cover',
                  display: 'block',
                  filter: 'contrast(1.06) saturate(0.92)',
                }}
              />
              <div
                style={{
                  background: '#0f172a',
                  padding: '5px 8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    fontFamily: MONT,
                    fontWeight: 800,
                    fontSize: 7.8,
                    letterSpacing: 1.6,
                    color: '#facc15',
                  }}
                >
                  SHINJUKU · TOKYO
                </span>
                <span
                  style={{
                    fontFamily: MONT,
                    fontWeight: 600,
                    fontSize: 7.2,
                    letterSpacing: 1,
                    color: '#cbd5e1',
                  }}
                >
                  POP. 14.1M
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ================= CINEMATIC VIGNETTE & TOP/BOTTOM DOCUMENTARY GRADIENT ================= */}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          background:
            'radial-gradient(ellipse at 52% 50%, rgba(4,7,13,0) 68%, rgba(3,6,12,0.24) 100%)',
        }}
      />

      {/* ================= PERMANENT KINGS & GENERALS YEAR PLAQUE (TOP-RIGHT) ================= */}
      <div
        style={{
          position: 'absolute',
          top: 38,
          right: 48,
          background: 'rgba(8, 12, 20, 0.84)',
          border: '1px solid rgba(234, 179, 8, 0.34)',
          borderLeft: '4px solid #eab308',
          padding: '8px 22px 9px 18px',
          borderRadius: 3,
          boxShadow: '0 10px 28px rgba(0, 0, 0, 0.65)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
        }}
      >
        <span
          style={{
            fontFamily: MONT,
            fontWeight: 700,
            fontSize: 11,
            letterSpacing: 4,
            color: '#eab308',
            lineHeight: 1.1,
          }}
        >
          YEAR
        </span>
        <span
          style={{
            fontFamily: MONT,
            fontWeight: 900,
            fontSize: 36,
            letterSpacing: 2.5,
            color: '#f8fafc',
            lineHeight: 1.05,
            marginTop: 2,
          }}
        >
          {yearText}
        </span>
      </div>

      {/* ================= DISCREET ON-SCREEN SOURCE CITATION (BOTTOM-LEFT) ================= */}
      <div
        style={{
          position: 'absolute',
          bottom: 28,
          left: 48,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          opacity: 0.78,
        }}
      >
        <div style={{width: 18, height: 2, background: 'rgba(234, 179, 8, 0.7)'}} />
        <span
          style={{
            fontFamily: MONT,
            fontWeight: 600,
            fontSize: 14,
            letterSpacing: 1.8,
            color: 'rgba(214, 224, 238, 0.82)',
            textShadow: '0 2px 8px rgba(0,0,0,0.9)',
          }}
        >
          SOURCE: MHLW VITAL STATISTICS &amp; MIC · JAPANESE NATIONALS
        </span>
      </div>

      {/* ================= DOCUMENTARY TITLE REVEAL AT END OF COLD OPEN (f=888..1023) ================= */}
      {titleOp > 0 && (
        <div
          style={{
            position: 'absolute',
            bottom: 84,
            left: 0,
            width: '100%',
            textAlign: 'center',
            opacity: titleOp,
          }}
        >
          <div
            style={{
              display: 'inline-block',
              padding: '14px 42px',
              background: 'rgba(6, 10, 18, 0.78)',
              borderTop: '1px solid rgba(250, 204, 21, 0.45)',
              borderBottom: '1px solid rgba(250, 204, 21, 0.45)',
              boxShadow: '0 18px 48px rgba(0,0,0,0.75)',
            }}
          >
            <span
              style={{
                fontFamily: MONT,
                fontWeight: 900,
                fontSize: 58,
                letterSpacing: 6,
                color: '#f8fafc',
              }}
            >
              WHY TOKYO IS <span style={{color: '#f43f5e'}}>DELETING</span> JAPAN
            </span>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
