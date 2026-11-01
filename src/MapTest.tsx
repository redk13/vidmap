import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {JapanMap} from './JapanMap';

const RED = '#c2283a', DRED = '#7e1824', BLUE = '#1e6fd9', INK = '#0a1420', GREY = '#1d2b3a';
// Cold-open view: 46 prefectures bleed red (losing Japanese residents), Tokyo pulses blue.
export const MapTest: React.FC = () => {
  const f = useCurrentFrame();
  const W = 1920, H = 1080;
  // deterministic sweep order: by JIS id (north→south roughly)
  const reddened = interpolate(f, [10, 70], [0, 47], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tokyoPulse = 0.5 + 0.5 * Math.sin((f - 70) / 8);
  const counter = Math.round(interpolate(f, [15, 95], [0, 918253], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const styleFor = (id: number) => {
    if (id === 13) return f > 70
      ? {fill: BLUE, glow: 'y', stroke: '#9cc4ff', strokeWidth: 2.5}
      : {fill: GREY};
    const idx = id > 13 ? id - 1 : id; // sweep skips Tokyo
    return idx <= reddened ? {fill: id % 3 === 0 ? DRED : RED} : {fill: GREY};
  };
  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif'}}>
      <JapanMap width={W} height={H} styleFor={styleFor}>
        {(centroidOf) => {
          const [tx, ty] = centroidOf(13);
          const [ox, oy] = centroidOf(47);
          return (
            <g>
              {f > 75 && (
                <g>
                  <rect x={tx + 18} y={ty - 64} rx={10} width={210} height={52} fill="#ffffff"/>
                  <text x={tx + 123} y={ty - 27} textAnchor="middle" fontSize={34} fontWeight={900} fill={DRED}>TOKYO 0.96</text>
                </g>
              )}
              {f > 85 && (
                <g>
                  <rect x={ox - 125} y={oy - 100} rx={10} width={250} height={52} fill="#ffffff"/>
                  <text x={ox} y={oy - 63} textAnchor="middle" fontSize={34} fontWeight={900} fill={BLUE}>OKINAWA 1.52</text>
                </g>
              )}
              {f > 70 && <circle cx={tx} cy={ty} r={14 + 10 * tokyoPulse} fill="none" stroke="#9cc4ff" strokeWidth={3} opacity={1 - tokyoPulse * 0.6}/>}
            </g>
          );
        }}
      </JapanMap>
      <div style={{position: 'absolute', top: 70, left: 90}}>
        <div style={{fontSize: 92, fontWeight: 900, color: '#fff', lineHeight: 1}}>
          −{counter.toLocaleString('en-US')}
        </div>
        <div style={{fontSize: 30, fontWeight: 700, color: '#ffd60a', letterSpacing: 3, marginTop: 10}}>
          DEATHS MINUS BIRTHS — 2025
        </div>
        <div style={{fontSize: 22, color: '#8fa6bd', marginTop: 6}}>Source: MHLW, 2026</div>
      </div>
    </AbsoluteFill>
  );
};
