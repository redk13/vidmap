import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {JapanMap} from './JapanMap';
import pyr from '../data/pyramids.json';

const CRIM = '#e8273c', BLUE = '#2f86ff', INK = '#0a1420', YEL = '#ffd60a';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const N = pyr.meta.labels.length; // 18 groups, 0-4 ... 85+

const Pyramid: React.FC<{
  cx: number; top: number; name: string; color: string; colorF: string;
  male: number[]; female: number[]; total: number; f: number; delay: number;
  highlight: [number, number]; hiColor: string; maxPct: number;
}> = ({cx, top, name, color, colorF, male, female, total, f, delay, highlight, hiColor, maxPct}) => {
  const sum = male.reduce((a, b) => a + b, 0) + female.reduce((a, b) => a + b, 0);
  const barH = 30, gap = 6, axisW = 78, maxW = 310;
  const rows = [];
  for (let i = 0; i < N; i++) {
    const yi = top + (N - 1 - i) * (barH + gap); // oldest on top
    const grow = interpolate(f, [delay + i * 5, delay + 28 + i * 5], [0, 1], clamp);
    const breathe = 1 + 0.012 * Math.sin((f - delay) / 17 + i * 0.6);
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
          <text x={cx} y={yi + 21} textAnchor="middle" fontSize={17} fill="#7e95ab" fontWeight={700}>
            {pyr.meta.labels[i]}
          </text>
        )}
      </g>
    );
  }
  const hdr = interpolate(f, [delay - 10, delay + 15], [0, 1], clamp);
  return (
    <g>
      <g opacity={hdr} transform={`translate(0 ${(1 - hdr) * -30})`}>
        <rect x={cx - 210} y={top - 86} rx={12} width={420} height={58} fill={color}/>
        <text x={cx} y={top - 45} textAnchor="middle" fontSize={32} fontWeight={900} fill="#fff">
          {name} — {(total / 1000).toFixed(1)}M
        </text>
      </g>
      <text x={cx - axisW / 2 - 40} y={top - 110} textAnchor="middle" fontSize={20} fill="#7e95ab" fontWeight={700} opacity={hdr}>M</text>
      <text x={cx + axisW / 2 + 40} y={top - 110} textAnchor="middle" fontSize={20} fill="#7e95ab" fontWeight={700} opacity={hdr}>F</text>
      {rows}
    </g>
  );
};

// PYRAMIDS — ONE COUNTRY, TWO JAPANS (600f)
export const Pyramids: React.FC = () => {
  const f = useCurrentFrame();
  const title = interpolate(f, [5, 35], [0, 1], clamp);
  const chips = interpolate(f, [360, 390], [0, 1], clamp);
  const maxPct = 4.6; // max single-sex group share (%), shared scale for honest comparison
  const styleFor = (id: number) => {
    if (id === 13) return {fill: 'rgba(232,39,60,0.5)'};
    if (id === 47) return {fill: 'rgba(47,134,255,0.5)'};
    return {fill: '#15222f'};
  };
  const TOP = 268;
  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      <div style={{position: 'absolute', inset: 0, opacity: 0.22}}>
        <JapanMap width={1920} height={1080} styleFor={styleFor}/>
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute', top: 0, left: 0}}>
        <Pyramid cx={520} top={TOP} name="TOKYO" color={CRIM} colorF="#ff8093"
          male={pyr.tokyo.male} female={pyr.tokyo.female} total={pyr.tokyo.total}
          f={f} delay={50} highlight={[4, 7]} hiColor={YEL} maxPct={maxPct}/>
        <Pyramid cx={1400} top={TOP} name="OKINAWA" color={BLUE} colorF="#8fc6ff"
          male={pyr.okinawa.male} female={pyr.okinawa.female} total={pyr.okinawa.total}
          f={f} delay={80} highlight={[0, 2]} hiColor="#49e07c" maxPct={maxPct}/>
        {f > 280 && (
          <g opacity={chips}>
            <rect x={740} y={150} rx={12} width={440} height={96} fill={YEL}/>
            <text x={960} y={188} textAnchor="middle" fontSize={27} fontWeight={900} fill={INK}>TOKYO AGES 20–39:</text>
            <text x={960} y={226} textAnchor="middle" fontSize={32} fontWeight={900} fill={INK}>27.2% OF THE CITY</text>
            <rect x={740} y={262} rx={12} width={440} height={96} fill="#0f2b1b" stroke="#49e07c" strokeWidth={2.5}/>
            <text x={960} y={300} textAnchor="middle" fontSize={27} fontWeight={900} fill="#49e07c">KIDS UNDER 15:</text>
            <text x={960} y={338} textAnchor="middle" fontSize={32} fontWeight={900} fill="#49e07c">OKINAWA 15.8% vs TOKYO 10.5%</text>
          </g>
        )}
      </svg>
      <div style={{position: 'absolute', top: 52, width: '100%', textAlign: 'center', opacity: title}}>
        <span style={{fontSize: 58, fontWeight: 900, color: '#fff'}}>ONE COUNTRY. </span>
        <span style={{fontSize: 58, fontWeight: 900, color: YEL}}>TWO JAPANS.</span>
      </div>
      <div style={{position: 'absolute', bottom: 28, right: 42, fontSize: 19, color: '#6d8aa6'}}>
        Source: Statistics Bureau of Japan — Population Estimates, Oct 1, 2024 · Total population
      </div>
    </AbsoluteFill>
  );
};
