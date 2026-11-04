import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing, staticFile, delayRender, continueRender, cancelRender} from 'remotion';
const registerLocalFont = (family: string, file: string, weight = '400 900') => {
  const handle = delayRender(`Loading local font: ${family}`);
  const face = new FontFace(family, `url("${staticFile(file)}")`, {style: 'normal', weight});
  face.load().then((loaded) => {
    document.fonts.add(loaded);
    continueRender(handle);
  }).catch(cancelRender);
};

registerLocalFont('Montserrat', 'Montserrat-Variable.ttf');
const MONT = 'Montserrat';

// ---------- helpers ----------
const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));
const ez = Easing.bezier(0.33, 0, 0.2, 1);

// ---------- THE ROOM (static backdrop) ----------
const Room: React.FC = () => (
  <AbsoluteFill>
    {/* wall */}
    <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg,#cdd0d3 0%,#b4b8bc 55%,#a7abafff 78%)'}} />
    {/* window band */}
    {[
      {x: 55, w: 390},
      {x: 505, w: 910},
      {x: 1475, w: 390},
    ].map((win, i) => (
      <div key={i} style={{position: 'absolute', left: win.x, top: 70, width: win.w, height: 770, background: '#e9edef', borderRadius: 4, boxShadow: 'inset 0 0 0 10px #dfe3e5, 0 6px 18px rgba(0,0,0,0.18)', overflow: 'hidden'}}>
        {/* glass */}
        <div style={{position: 'absolute', inset: 14, overflow: 'hidden', filter: 'blur(2.2px)'}}>
          <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg,#8fc8ec 0%,#b8ddf3 55%,#d8ecf8 72%)'}} />
          {/* distant water + shore */}
          <div style={{position: 'absolute', left: 0, right: 0, top: '72%', height: '14%', background: 'linear-gradient(180deg,#7fa6c0,#93b4c9)'}} />
          <div style={{position: 'absolute', left: 0, right: 0, top: '84%', height: '16%', background: 'linear-gradient(180deg,#9fb3ba,#b7c3c6)'}} />
          {/* faint cloud */}
          <div style={{position: 'absolute', left: '12%', top: '18%', width: '55%', height: 36, borderRadius: 40, background: 'rgba(255,255,255,0.5)', filter: 'blur(14px)'}} />
        </div>
        {/* mullions */}
        <div style={{position: 'absolute', left: 10, right: 10, top: 330, height: 16, background: '#e2e5e7'}} />
        <div style={{position: 'absolute', left: 10, right: 10, top: 560, height: 16, background: '#e2e5e7'}} />
        {win.w > 500 && <div style={{position: 'absolute', top: 10, bottom: 10, left: win.w / 2 - 8, width: 16, background: '#e2e5e7'}} />}
      </div>
    ))}
    {/* top wall strip over windows */}
    <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 72, background: 'linear-gradient(180deg,#c3c6c9,#babdc1)', boxShadow: '0 4px 10px rgba(0,0,0,0.10)'}} />
    {/* floor */}
    <div style={{position: 'absolute', left: 0, right: 0, top: 838, bottom: 0, background: 'linear-gradient(180deg,#8a6a4c 0%,#7c5e42 60%,#6b5038 100%)'}} />
    <div style={{position: 'absolute', left: 0, right: 0, top: 838, bottom: 0, background: 'repeating-linear-gradient(90deg, rgba(0,0,0,0.10) 0 3px, rgba(0,0,0,0) 3px 160px)', opacity: 0.6}} />
    <div style={{position: 'absolute', left: 0, right: 0, top: 838, height: 10, background: 'rgba(0,0,0,0.25)'}} />
    {/* board floor shadow */}
    <div style={{position: 'absolute', left: 430, top: 950, width: 1060, height: 60, background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.35), rgba(0,0,0,0) 70%)'}} />
    {/* vignette */}
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.22) 100%)'}} />
  </AbsoluteFill>
);

// ---------- THE BOARD (frame + legs + white canvas) ----------
const Board: React.FC<{children: React.ReactNode}> = ({children}) => (
  <>
    {/* legs */}
    {[438, 1456].map((x) => (
      <div key={x}>
        <div style={{position: 'absolute', left: x, top: 200, width: 26, height: 790, background: 'linear-gradient(90deg,#7e8488,#9ba1a5 40%,#6f757a)', borderRadius: 4}} />
        <div style={{position: 'absolute', left: x - 42, top: 968, width: 110, height: 16, background: 'linear-gradient(180deg,#848a8e,#5f656a)', borderRadius: 6}} />
      </div>
    ))}
    {/* wooden frame */}
    <div style={{position: 'absolute', left: 360, top: 58, width: 1200, height: 902, borderRadius: 10, background: 'linear-gradient(135deg,#e7bb8a 0%,#d9a873 45%,#c8945f 100%)', boxShadow: '0 18px 40px rgba(0,0,0,0.35), inset 0 2px 0 rgba(255,255,255,0.45)'}}>
      {/* screws */}
      {[{l: 16, t: 14}, {r: 16, t: 14}, {l: 16, b: 14}, {r: 16, b: 14}].map((p, i) => (
        <div key={i} style={{position: 'absolute', width: 14, height: 14, borderRadius: 7, background: 'radial-gradient(circle at 35% 30%, #f3f3f1, #8d8d89)', boxShadow: '0 1px 2px rgba(0,0,0,0.4)', ...(p as object)}} />
      ))}
      {/* white canvas */}
      <div style={{position: 'absolute', left: 32, top: 32, right: 32, bottom: 32, background: 'radial-gradient(ellipse at 50% 30%, #ffffff 0%, #fbfaf7 60%, #f1efe9 100%)', borderRadius: 4, boxShadow: 'inset 0 0 26px rgba(0,0,0,0.10)', overflow: 'hidden'}}>
        {children}
      </div>
    </div>
  </>
);

// ---------- PART A: line chart (fertility collapse) ----------
const YEARS = [1950, 1955, 1960, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025];
type Series = {name: string; color: string; vals: (number | null)[]; end: string; dy?: number};
const SERIES: Series[] = [
  {name: 'South Korea', color: '#f0a81f', end: '0.75', dy: 16, vals: [5.05, 6.33, 6.16, 5.63, 4.53, 3.43, 2.82, 1.66, 1.57, 1.63, 1.48, 1.09, 1.23, 1.24, 0.84, 0.75]},
  {name: 'Japan', color: '#2f86ff', end: '1.20', vals: [3.65, 2.37, 2.0, 2.14, 2.13, 1.91, 1.75, 1.76, 1.54, 1.42, 1.36, 1.26, 1.39, 1.45, 1.33, 1.2]},
  {name: 'Tokyo', color: '#e8273c', end: '0.96', dy: -6, vals: [null, null, null, null, 1.96, 1.63, 1.44, 1.44, 1.23, 1.11, 1.07, 1.0, 1.12, 1.24, 1.12, 0.96]},
  {name: 'Seoul', color: '#80868d', end: '0.63', vals: [null, null, null, null, null, null, null, null, null, 1.27, 1.26, 0.92, 1.02, 1.0, 0.64, 0.63]},
];
const PA = {x0: 150, x1: 1040, y0: 200, y1: 660, vmax: 6.5};
const px = (year: number) => PA.x0 + ((year - 1950) / 75) * (PA.x1 - PA.x0);
const py = (v: number) => PA.y1 - (v / PA.vmax) * (PA.y1 - PA.y0);

const LineChart: React.FC<{f: number}> = ({f}) => {
  const tIn = interpolate(f, [4, 22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez});
  const axIn = interpolate(f, [14, 34], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez});
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: MONT}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: 44, textAlign: 'center', fontSize: 52, fontWeight: 900, color: '#1b1e22', letterSpacing: 0.5, opacity: tIn, transform: `translateY(${(1 - tIn) * 18}px)`}}>
        The Fertility Collapse
      </div>
      {/* legend */}
      <div style={{position: 'absolute', left: 0, right: 0, top: 130, display: 'flex', justifyContent: 'center', gap: 34, opacity: axIn}}>
        {SERIES.map((s) => (
          <div key={s.name} style={{display: 'flex', alignItems: 'center', gap: 9}}>
            <div style={{width: 34, height: 7, borderRadius: 3, background: s.color}} />
            <div style={{fontSize: 21, fontWeight: 700, color: '#3a3f44'}}>{s.name}</div>
          </div>
        ))}
      </div>
      <svg width={1136} height={838} style={{position: 'absolute', left: 0, top: 0, opacity: axIn}}>
        {/* plot frame */}
        <rect x={PA.x0} y={PA.y0} width={PA.x1 - PA.x0} height={PA.y1 - PA.y0} fill="none" stroke="#2a2d31" strokeWidth={2.5} />
        {/* y ticks */}
        {[0, 1, 2, 3, 4, 5, 6].map((v) => (
          <g key={v}>
            <line x1={PA.x0 - 8} x2={PA.x0} y1={py(v)} y2={py(v)} stroke="#2a2d31" strokeWidth={2} />
            <text x={PA.x0 - 16} y={py(v) + 7} textAnchor="end" fontSize={20} fontWeight={700} fill="#4a4f54" fontFamily={MONT}>{v.toFixed(1)}</text>
            {v > 0 && <line x1={PA.x0} x2={PA.x1} y1={py(v)} y2={py(v)} stroke="rgba(0,0,0,0.06)" strokeWidth={1.5} />}
          </g>
        ))}
        {/* x ticks */}
        {[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020].map((yr) => (
          <g key={yr}>
            <line x1={px(yr)} x2={px(yr)} y1={PA.y1} y2={PA.y1 + 8} stroke="#2a2d31" strokeWidth={2} />
            <text x={px(yr)} y={PA.y1 + 34} textAnchor="middle" fontSize={20} fontWeight={700} fill="#4a4f54" fontFamily={MONT}>{yr}</text>
          </g>
        ))}
        {/* y axis title */}
        <text x={66} y={(PA.y0 + PA.y1) / 2} fontSize={20} fontWeight={700} fill="#5a5f64" fontFamily={MONT} transform={`rotate(-90 66 ${(PA.y0 + PA.y1) / 2})`} textAnchor="middle">births per woman</text>
        {/* replacement line */}
        <line x1={PA.x0} x2={PA.x1} y1={py(2.1)} y2={py(2.1)} stroke="#c2283a" strokeWidth={2.5} strokeDasharray="10 8" opacity={0.8} />
        <text x={PA.x1 - 6} y={py(2.1) - 10} textAnchor="end" fontSize={19} fontWeight={800} fill="#c2283a" fontFamily={MONT}>REPLACEMENT 2.1</text>
        {/* series */}
        {SERIES.map((s, si) => {
          const pts = YEARS.map((yr, i) => (s.vals[i] == null ? null : [px(yr), py(s.vals[i] as number)])).filter(Boolean) as number[][];
          const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
          const prog = interpolate(f, [34 + si * 10, 172 + si * 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.3, 1)});
          const lastP = pts[pts.length - 1];
          const lblIn = interpolate(f, [176 + si * 10, 192 + si * 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return (
            <g key={s.name}>
              <path d={d} fill="none" stroke={s.color} strokeWidth={5.5} strokeLinejoin="round" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - prog} />
              <circle cx={lastP[0]} cy={lastP[1]} r={7} fill={s.color} opacity={lblIn} />
              <text x={lastP[0] + 14} y={lastP[1] + 7 + (s.dy ?? 0)} fontSize={23} fontWeight={900} fill={s.color} fontFamily={MONT} opacity={lblIn}>{s.end}</text>
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: 150, bottom: 54, fontSize: 18, fontWeight: 700, color: '#6a6f74', opacity: axIn}}>
        SOURCE: UN World Population Prospects 2024 · national statistics. (lab sample)
      </div>
    </div>
  );
};

// ---------- PART B: sankey (Japan FY2025 budget) ----------
type SNode = {name: string; val: number; col: string; rib: string; pct?: string};
const LEFT: SNode[] = [
  {name: 'Tax revenue', val: 78.4, col: '#2fa868', rib: 'rgba(63,186,122,0.42)'},
  {name: 'New bond issuance', val: 28.6, col: '#57c08a', rib: 'rgba(87,192,138,0.38)'},
  {name: 'Other income', val: 8.5, col: '#7fd3a8', rib: 'rgba(127,211,168,0.38)'},
];
const RIGHT: SNode[] = [
  {name: 'Social security', val: 38.3, col: '#8b9196', rib: 'rgba(139,145,150,0.35)', pct: '33.2%'},
  {name: 'Debt service', val: 28.2, col: '#c2283a', rib: 'rgba(194,40,58,0.30)', pct: '24.4%'},
  {name: 'Local allocation', val: 19.3, col: '#a9aeb3', rib: 'rgba(169,174,179,0.38)', pct: '16.7%'},
  {name: 'Other spending', val: 29.5, col: '#6fa83f', rib: 'rgba(111,168,63,0.32)', pct: '25.5%'},
];
const TOTAL = 115.5;
const SK = {xL: 285, xC: 610, xR: 930, barW: 16, top: 215, span: 440, gap: 13};
const scaleV = SK.span / TOTAL;

const ribbon = (x0: number, y0: number, w0: number, x1: number, y1: number, w1: number) => {
  const mx = (x0 + x1) / 2;
  return `M ${x0} ${y0} C ${mx} ${y0}, ${mx} ${y1}, ${x1} ${y1} L ${x1} ${y1 + w1} C ${mx} ${y1 + w1}, ${mx} ${y0 + w0}, ${x0} ${y0 + w0} Z`;
};

const Sankey: React.FC<{f: number}> = ({f}) => {
  const tIn = interpolate(f, [4, 22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez});
  const statIn = interpolate(f, [16, 36], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez});
  // stacked positions
  const lPos: number[] = []; let acc = SK.top;
  LEFT.forEach((n) => {lPos.push(acc); acc += n.val * scaleV + SK.gap;});
  const cTop = SK.top + 8;
  const lcPos: number[] = []; let acc2 = cTop;
  LEFT.forEach((n) => {lcPos.push(acc2); acc2 += n.val * scaleV;});
  const rcPos: number[] = []; let acc3 = cTop;
  RIGHT.forEach((n) => {rcPos.push(acc3); acc3 += n.val * scaleV;});
  const rPos: number[] = []; let acc4 = SK.top - 6;
  RIGHT.forEach((n) => {rPos.push(acc4); acc4 += n.val * scaleV + SK.gap;});
  const count = Math.round(interpolate(f, [40, 120], [0, 1155], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez})) / 10;
  return (
    <div style={{position: 'absolute', inset: 0, fontFamily: MONT}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: 44, textAlign: 'center', fontSize: 50, fontWeight: 900, color: '#1b1e22', opacity: tIn, transform: `translateY(${(1 - tIn) * 18}px)`}}>
        Japan's Budget — Where It Goes
      </div>
      {/* top mini stats */}
      <div style={{position: 'absolute', left: 0, right: 0, top: 126, display: 'flex', justifyContent: 'center', gap: 120, opacity: statIn}}>
        {[['Budget FY2025', `¥${count.toFixed(1)}T`], ['Biggest cost', 'Social security'], ['Eaten by debt', '24.4%']].map((s) => (
          <div key={s[0]} style={{textAlign: 'center'}}>
            <div style={{fontSize: 17, fontWeight: 700, color: '#8a8f94', letterSpacing: 1}}>{s[0].toUpperCase()}</div>
            <div style={{fontSize: 27, fontWeight: 900, color: '#22262a'}}>{s[1]}</div>
          </div>
        ))}
      </div>
      <svg width={1136} height={838} style={{position: 'absolute', left: 0, top: 0}}>
        <defs>
          <clipPath id="ribL"><rect x={SK.xL} y={0} width={interpolate(f, [34, 96], [0, SK.xC - SK.xL + SK.barW], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez})} height={838} /></clipPath>
          <clipPath id="ribR"><rect x={SK.xC} y={0} width={interpolate(f, [86, 150], [0, SK.xR - SK.xC + SK.barW], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez})} height={838} /></clipPath>
        </defs>
        {/* ribbons left->center */}
        <g clipPath="url(#ribL)">
          {LEFT.map((n, i) => (
            <path key={n.name} d={ribbon(SK.xL + SK.barW, lPos[i], n.val * scaleV, SK.xC, lcPos[i], n.val * scaleV)} fill={n.rib} />
          ))}
        </g>
        {/* ribbons center->right */}
        <g clipPath="url(#ribR)">
          {RIGHT.map((n, i) => (
            <path key={n.name} d={ribbon(SK.xC + SK.barW, rcPos[i], n.val * scaleV, SK.xR, rPos[i], n.val * scaleV)} fill={n.rib} />
          ))}
        </g>
        {/* left bars */}
        {LEFT.map((n, i) => {
          const g1 = interpolate(f, [20 + i * 8, 44 + i * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez});
          return <rect key={n.name} x={SK.xL} y={lPos[i]} width={SK.barW} height={n.val * scaleV * g1} rx={3} fill={n.col} />;
        })}
        {/* center bar */}
        <rect x={SK.xC} y={cTop} width={SK.barW} height={(TOTAL * scaleV) * interpolate(f, [60, 100], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez})} rx={3} fill="#1f7a4d" />
        {/* right bars */}
        {RIGHT.map((n, i) => {
          const g1 = interpolate(f, [128 + i * 8, 152 + i * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ez});
          return <rect key={n.name} x={SK.xR} y={rPos[i]} width={SK.barW} height={n.val * scaleV * g1} rx={3} fill={n.col} />;
        })}
        {/* labels */}
        {LEFT.map((n, i) => {
          const o = interpolate(f, [44 + i * 8, 62 + i * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return (
            <g key={n.name} opacity={o}>
              <text x={SK.xL - 14} y={lPos[i] + (n.val * scaleV) / 2 - 2} textAnchor="end" fontSize={21} fontWeight={800} fill="#2e3236" fontFamily={MONT}>{n.name}</text>
              <text x={SK.xL - 14} y={lPos[i] + (n.val * scaleV) / 2 + 22} textAnchor="end" fontSize={20} fontWeight={700} fill="#767b80" fontFamily={MONT}>¥{n.val.toFixed(1)}T</text>
            </g>
          );
        })}
        <g opacity={interpolate(f, [96, 112], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}>
          <text x={SK.xC + SK.barW / 2} y={cTop - 14} textAnchor="middle" fontSize={22} fontWeight={900} fill="#1f7a4d" fontFamily={MONT}>Budget ¥115.5T</text>
        </g>
        {RIGHT.map((n, i) => {
          const o = interpolate(f, [152 + i * 8, 170 + i * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return (
            <g key={n.name} opacity={o}>
              <text x={SK.xR + SK.barW + 14} y={rPos[i] + (n.val * scaleV) / 2 - 2} fontSize={21} fontWeight={800} fill="#2e3236" fontFamily={MONT}>{n.name}</text>
              <text x={SK.xR + SK.barW + 14} y={rPos[i] + (n.val * scaleV) / 2 + 22} fontSize={20} fontWeight={700} fill="#767b80" fontFamily={MONT}>¥{n.val.toFixed(1)}T · {n.pct}</text>
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: 150, bottom: 54, fontSize: 18, fontWeight: 700, color: '#6a6f74', opacity: statIn}}>
        Source: Ministry of Finance, Japan — FY2025 initial budget. (lab sample)
      </div>
    </div>
  );
};

// ---------- MAIN ----------
export const LabBoard: React.FC = () => {
  const f = useCurrentFrame();
  const cs = interpolate(f, [0, 479], [1.0, 1.06], {easing: Easing.linear});
  const SWITCH = 250;
  const aOp = interpolate(f, [SWITCH - 14, SWITCH], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bOp = interpolate(f, [SWITCH, SWITCH + 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#9aa0a5', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${cs})`, transformOrigin: '50% 46%'}}>
        <Room />
        <Board>
          <div style={{position: 'absolute', inset: 0, opacity: aOp}}>{f < SWITCH + 5 ? <LineChart f={f} /> : null}</div>
          <div style={{position: 'absolute', inset: 0, opacity: bOp}}>{f >= SWITCH - 5 ? <Sankey f={f - SWITCH} /> : null}</div>
        </Board>
      </div>
    </AbsoluteFill>
  );
};
